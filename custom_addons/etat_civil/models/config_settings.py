# -*- coding: utf-8 -*-
"""
Modèle singleton de configuration de l'identité de la commune.

Un seul enregistrement par base PostgreSQL représente l'identité officielle
de l'installation : nom, code, région, district, logo, contact, mentions légales.
Après le premier acte enregistré, l'identité est verrouillée pour empêcher
toute modification non autorisée.
"""
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError


class EtatCivilConfigSettings(models.Model):
    _name = 'etat.civil.config.settings'
    _description = 'Configuration de l\'identité de la commune'
    _rec_name = 'commune_nom_officiel'

    # --- Identité de la commune (champs critiques, verrouillés après 1er acte) ---

    commune_nom_officiel = fields.Char(
        string='Nom officiel de la commune',
        required=True,
        help='Ex: Commune urbaine d\'Antsohihy, Commune rurale d\'Ambanja',
    )
    commune_type = fields.Selection([
        ('urbaine', 'Commune urbaine'),
        ('rurale', 'Commune rurale'),
    ], string='Type de commune', required=True, default='urbaine')
    commune_code = fields.Char(
        string='Code de la commune',
        required=True,
        help='Court code unique pour les références et documents (ex: ANTS, FIA, AMB)',
    )
    region = fields.Char(
        string='Région / Province',
        required=True,
    )
    district = fields.Char(
        string='District',
        required=True,
    )

    # --- Informations non critiques (modifiables par admin local) ---

    adresse = fields.Text(
        string='Adresse du siège',
    )
    logo_officiel = fields.Image(
        string='Logo officiel de la commune',
        max_width=512,
        max_height=512,
    )
    signature_cachet = fields.Image(
        string='Signature / Cachet officiel',
        max_width=512,
        max_height=512,
    )
    devise = fields.Many2one(
        'res.currency',
        string='Devise',
        default=lambda self: self.env.ref('base.mga', raise_if_not_found=False),
    )
    langue_principale = fields.Selection([
        ('mg', 'Malagasy'),
        ('fr', 'Français'),
        ('en', 'Anglais'),
    ], string='Langue principale', default='fr')
    contact_officiel = fields.Text(
        string='Contact officiel',
        help='Téléphone, email, site web',
    )
    mentions_legales = fields.Text(
        string='Mentions légales',
        help='Texte affiché en en-tête des documents officiels',
    )

    # --- Liaison avec res.company ---

    company_id = fields.Many2one(
        'res.company',
        string='Société Odoo associée',
        required=True,
        default=lambda self: self.env.company,
        help='Société Odoo synchronisée avec cette configuration',
    )

    # --- Verrouillage de l'identité ---

    identity_locked = fields.Boolean(
        string='Identité verrouillée',
        default=False,
        readonly=True,
        help='Après le premier acte enregistré, l\'identité ne peut plus être modifiée sans procédure administrative',
    )
    locked_at = fields.Datetime(
        string='Date de verrouillage',
        readonly=True,
    )
    locked_by_id = fields.Many2one(
        'res.users',
        string='Verrouillé par',
        readonly=True,
    )

    @api.model
    def get_config(self):
        """Retourne le singleton de configuration ou le crée s'il n'existe pas."""
        config = self.sudo().search([], limit=1)
        if not config:
            config = self._create_default_config()
        return config

    @api.model
    def _create_default_config(self):
        """Crée la configuration par défaut en pré-remplissant depuis les données existantes."""
        company = self.env.company
        centre = self.env['etat.civil.centre'].sudo().search([], limit=1)

        vals = {
            'company_id': company.id,
            'commune_nom_officiel': company.name or 'Commune',
            'commune_type': 'urbaine',
            'commune_code': 'COMM',
            'region': centre.district_province or '',
            'district': '',
            'logo_officiel': centre.logo_commune if centre else False,
            'devise': self.env.ref('base.mga', raise_if_not_found=False).id if self.env.ref('base.mga', raise_if_not_found=False) else False,
            'langue_principale': 'fr',
        }
        if vals['region']:
            vals['district'] = vals['region']

        config = self.sudo().create(vals)

        # Si des actes existent déjà, verrouiller automatiquement
        if self._should_lock_identity():
            config._lock_identity()

        return config

    def _should_lock_identity(self):
        """Vérifie si des actes existent déjà dans la base."""
        if self.identity_locked:
            return True
        # Vérifier s'il y a des actes enregistrés
        acte_naissance_count = self.env['etat.civil.acte.naissance'].sudo().search_count([])
        acte_mariage_count = self.env['etat.civil.acte.mariage'].sudo().search_count([])
        acte_deces_count = self.env['etat.civil.acte.deces'].sudo().search_count([])
        return (acte_naissance_count + acte_mariage_count + acte_deces_count) > 0

    def _lock_identity(self):
        """Verrouille l'identité de la commune."""
        self.sudo().write({
            'identity_locked': True,
            'locked_at': fields.Datetime.now(),
            'locked_by_id': self.env.user.id,
        })
        # Log dans l'audit log
        self.env['etat.civil.audit.log'].sudo()._record_event(
            action_type='identity_locked',
            record_model='etat.civil.config.settings',
            record_id=self.id,
            details='Identité de la commune verrouillée automatiquement après le premier acte.',
        )

    @api.model_create_multi
    def create(self, vals_list):
        """Empêche la création de plusieurs singletons."""
        if self.sudo().search_count([]) > 0:
            raise ValidationError(
                "Une seule configuration d'identité est autorisée par installation. "
                "Utilisez le bouton Modifier pour mettre à jour la configuration existante."
            )
        return super().create(vals_list)

    def write(self, vals):
        """Contrôle la modification des champs critiques verrouillés."""
        critical_fields = {'commune_nom_officiel', 'commune_code', 'region', 'district', 'commune_type'}
        for record in self:
            if record.identity_locked:
                changing_critical = critical_fields & set(vals.keys())
                if changing_critical:
                    # Vérifier si l'utilisateur est administrateur technique
                    if not self.env.user.has_group('etat_civil.group_etat_civil_tech_admin'):
                        raise AccessError(
                            "L'identité de la commune est verrouillée. "
                            "Seul un administrateur technique peut modifier les champs critiques. "
                            "Champs protégés: " + ', '.join(changing_critical)
                        )
                    # L'admin technique peut modifier, mais on trace dans l'audit log
                    for field in changing_critical:
                        self.env['etat.civil.audit.log'].sudo()._record_event(
                            action_type='identity_modified',
                            record_model='etat.civil.config.settings',
                            record_id=record.id,
                            details=f"Champ critique modifié: {field} = {vals.get(field)} (par {self.env.user.name})",
                        )
        return super().write(vals)

    def unlink(self):
        """Empêche la suppression de la configuration."""
        raise ValidationError(
            "La configuration de l'identité ne peut pas être supprimée. "
            "Utilisez le bouton Modifier pour mettre à jour les champs."
        )

    def action_sync_company(self):
        """Synchronise la configuration avec res.company."""
        for record in self:
            company = record.company_id
            if company:
                company.sudo().write({
                    'name': record.commune_nom_officiel,
                })
                # Mettre à jour le partenaire associé
                partner = company.partner_id
                if partner:
                    partner.sudo().write({
                        'name': record.commune_nom_officiel,
                    })
                # Synchroniser le logo
                if record.logo_officiel:
                    company.sudo().write({
                        'logo': record.logo_officiel,
                    })
                # Synchroniser l'adresse
                if record.adresse:
                    lines = record.adresse.strip().split('\n')
                    company.sudo().write({
                        'street': lines[0] if len(lines) > 0 else '',
                        'street2': lines[1] if len(lines) > 1 else '',
                        'city': record.district,
                        'state_id': False,
                        'zip': '',
                        'country_id': self.env.ref('base.mg', raise_if_not_found=False).id if self.env.ref('base.mg', raise_if_not_found=False) else False,
                    })
                # Synchroniser le contact
                if record.contact_officiel:
                    contact_lines = record.contact_officiel.strip().split('\n')
                    company.sudo().write({
                        'email': contact_lines[0] if '@' in (contact_lines[0] if contact_lines else '') else '',
                        'phone': contact_lines[-1] if len(contact_lines) > 1 else (contact_lines[0] if contact_lines else ''),
                    })
        return True

    def action_lock_identity(self):
        """Action manuelle pour verrouiller l'identité."""
        self._lock_identity()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Identité verrouillée',
                'message': "L'identité de la commune a été verrouillée avec succès.",
                'sticky': False,
                'type': 'success',
            }
        }

    def action_unlock_identity(self):
        """Ouvre le wizard de déverrouillage."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Déverrouiller l\'identité',
            'res_model': 'etat.civil.unlock.identity.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_config_id': self.id},
        }

    def get_full_identity(self):
        """Retourne l'identité complète pour les documents."""
        config = self.get_config()
        return {
            'nom': config.commune_nom_officiel,
            'type': config.commune_type,
            'code': config.commune_code,
            'region': config.region,
            'district': config.district,
            'adresse': config.adresse or '',
            'contact': config.contact_officiel or '',
            'mentions_legales': config.mentions_legales or '',
            'logo': config.logo_officiel,
            'signature': config.signature_cachet,
            'company_name': config.company_id.name if config.company_id else '',
        }


class UnlockIdentityWizard(models.TransientModel):
    _name = 'etat.civil.unlock.identity.wizard'
    _description = 'Wizard de déverrouillage de l\'identité'

    config_id = fields.Many2one('etat.civil.config.settings', required=True)
    justification = fields.Text(
        string='Motif du déverrouillage',
        required=True,
        help='Expliquez pourquoi vous devez déverrouiller l\'identité de la commune.',
    )
    confirmation = fields.Boolean(
        string='Je confirme que je suis administrateur technique et que je comprends les conséquences',
        required=True,
    )

    def action_unlock(self):
        """Déverrouille l'identité après confirmation."""
        if not self.confirmation:
            raise ValidationError("Vous devez confirmer pour déverrouiller l'identité.")
        if not self.justification.strip():
            raise ValidationError("Un motif est obligatoire.")

        if not self.env.user.has_group('etat_civil.group_etat_civil_tech_admin'):
            raise AccessError(
                "Seul un administrateur technique peut déverrouiller l'identité de la commune."
            )

        self.config_id.sudo().write({
            'identity_locked': False,
            'locked_at': False,
            'locked_by_id': False,
        })

        # Log dans l'audit log
        self.env['etat.civil.audit.log'].sudo()._record_event(
            action_type='identity_unlocked',
            record_model='etat.civil.config.settings',
            record_id=self.config_id.id,
            details=f"Identité déverrouillée par {self.env.user.name}. Motif: {self.justification}",
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Identité déverrouillée',
                'message': "L'identité de la commune a été déverrouillée. Vous pouvez maintenant modifier les champs critiques.",
                'sticky': False,
                'type': 'success',
            }
        }


# NOTE: Les hooks _check_and_lock_identity() sont intégrés directement
# dans les fichiers acte_naissance.py, acte_mariage.py et acte_deces.py
# pour éviter les conflits avec les méthodes create/write existantes.

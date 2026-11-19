# -*- coding: utf-8 -*-
"""
Assistant de configuration initiale de l'identité de la commune.

Ce wizard s'ouvre automatiquement au premier lancement si aucune configuration
n'existe. Il pré-remplit depuis res.company et le premier centre existant.
"""
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ConfigInitWizard(models.TransientModel):
    _name = 'etat.civil.config.init.wizard'
    _description = 'Assistant de configuration initiale de la commune'

    # --- Identité de la commune ---

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

    # --- Informations non critiques ---

    adresse = fields.Text(
        string='Adresse du siège',
    )
    contact_officiel = fields.Text(
        string='Contact officiel',
        help='Téléphone, email, site web',
    )
    mentions_legales = fields.Text(
        string='Mentions légales',
        help='Texte affiché en en-tête des documents officiels',
    )
    langue_principale = fields.Selection([
        ('mg', 'Malagasy'),
        ('fr', 'Français'),
        ('en', 'Anglais'),
    ], string='Langue principale', default='fr')

    @api.model
    def default_get(self, fields_list):
        """Pré-remplit depuis res.company et le premier centre existant."""
        res = super().default_get(fields_list)
        company = self.env.company
        centre = self.env['etat.civil.centre'].sudo().search([], limit=1)

        if 'commune_nom_officiel' in fields_list:
            res['commune_nom_officiel'] = company.name or 'Commune'
        if 'commune_code' in fields_list:
            # Essayer de déduire un code depuis le nom
            name = company.name or ''
            if 'fianarantsoa' in name.lower():
                res['commune_code'] = 'FIA'
            elif 'antsohihy' in name.lower():
                res['commune_code'] = 'ANTS'
            elif 'ambanja' in name.lower():
                res['commune_code'] = 'AMB'
            else:
                res['commune_code'] = 'COMM'
        if 'region' in fields_list:
            res['region'] = centre.district_province or ''
        if 'district' in fields_list:
            res['district'] = centre.district_province or ''
        if 'commune_type' in fields_list and 'urbaine' in (company.name or '').lower():
            res['commune_type'] = 'urbaine'

        return res

    def action_configure(self):
        """Crée ou met à jour le singleton de configuration."""
        config = self.env['etat.civil.config.settings'].sudo().search([], limit=1)

        vals = {
            'commune_nom_officiel': self.commune_nom_officiel,
            'commune_type': self.commune_type,
            'commune_code': self.commune_code,
            'region': self.region,
            'district': self.district,
            'adresse': self.adresse or '',
            'contact_officiel': self.contact_officiel or '',
            'mentions_legales': self.mentions_legales or '',
            'langue_principale': self.langue_principale,
        }

        if config:
            config.write(vals)
        else:
            config = self.env['etat.civil.config.settings'].sudo().create(vals)

        # Synchroniser avec res.company
        config.action_sync_company()

        # Log dans l'audit log
        self.env['etat.civil.audit.log'].sudo().log_event(
            action_type='config_initialized',
            record_model='etat.civil.config.settings',
            record_id=config.id,
            details=f"Configuration initiale créée par {self.env.user.name}. "
                    f"Commune: {self.commune_nom_officiel} ({self.commune_code})",
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Configuration enregistrée',
                'message': "L'identité de la commune a été configurée avec succès. "
                           "La société Odoo a été synchronisée.",
                'sticky': False,
                'type': 'success',
            }
        }


# Action automatique pour ouvrir le wizard au premier lancement
class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _check_config_and_redirect(self):
        """Vérifie si la configuration existe et redirige vers le wizard si nécessaire."""
        config = self.env['etat.civil.config.settings'].sudo().search([], limit=1)
        if not config and self.env.user.has_group('etat_civil.group_etat_civil_admin'):
            return {
                'type': 'ir.actions.act_window',
                'name': 'Configuration de la commune',
                'res_model': 'etat.civil.config.init.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {},
            }
        return False

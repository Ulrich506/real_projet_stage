# -*- coding: utf-8 -*-
"""
Tests d'isolation et de validation du modèle singleton de configuration.

Valide :
- Le singleton est bien un singleton (un seul enregistrement)
- La synchronisation avec res.company fonctionne
- Le verrouillage de l'identité après le premier acte
- Le groupe administrateur technique a les bons accès
- Les documents portent la bonne identité
"""
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError, AccessError
from odoo import fields


@tagged('post_install', '-at_install')
class TestConfigSingleton(TransactionCase):
    """Tests du modèle singleton de configuration de la commune."""

    def setUp(self):
        super().setUp()
        self.Config = self.env['etat.civil.config.settings']
        self.Company = self.env['res.company']

    def test_singleton_creation(self):
        """Le singleton est créé automatiquement via get_config()."""
        config = self.Config.get_config()
        self.assertTrue(config, "Le singleton doit exister après get_config()")
        self.assertEqual(config.commune_nom_officiel, self.env.company.name,
                        "Le nom doit être pré-rempli depuis res.company")

    def test_singleton_uniqueness(self):
        """On ne peut pas créer deux singletons."""
        config1 = self.Config.sudo().create({
            'commune_nom_officiel': 'Commune Test',
            'commune_type': 'urbaine',
            'commune_code': 'TEST',
            'region': 'Atsinanana',
            'district': 'Antsohihy',
        })
        with self.assertRaises(ValidationError):
            self.Config.sudo().create({
                'commune_nom_officiel': 'Commune Test 2',
                'commune_type': 'rurale',
                'commune_code': 'TEST2',
                'region': 'Haute Matsiatra',
                'district': 'Fianarantsoa',
            })

    def test_singleton_unlink_prevented(self):
        """On ne peut pas supprimer le singleton."""
        config = self.Config.get_config()
        with self.assertRaises(ValidationError):
            config.unlink()

    def test_sync_company(self):
        """La synchronisation met à jour res.company."""
        config = self.Config.sudo().create({
            'commune_nom_officiel': 'Commune urbaine d\'Antsohihy',
            'commune_type': 'urbaine',
            'commune_code': 'ANTS',
            'region': 'Atsinanana',
            'district': 'Antsohihy',
            'adresse': 'Rue de la Mairie\nAntsohihy',
            'contact_officiel': 'contact@ants.mg\n034 00 000 00',
        })
        config.action_sync_company()
        company = config.company_id
        self.assertEqual(company.name, 'Commune urbaine d\'Antsohihy')
        self.assertEqual(company.partner_id.name, 'Commune urbaine d\'Antsohihy')

    def test_get_full_identity(self):
        """get_full_identity() retourne tous les champs."""
        config = self.Config.sudo().create({
            'commune_nom_officiel': 'Commune Test',
            'commune_type': 'urbaine',
            'commune_code': 'TEST',
            'region': 'Region',
            'district': 'District',
            'mentions_legales': 'Mentions légales test',
        })
        identity = config.get_full_identity()
        self.assertEqual(identity['nom'], 'Commune Test')
        self.assertEqual(identity['code'], 'TEST')
        self.assertEqual(identity['region'], 'Region')
        self.assertEqual(identity['district'], 'District')
        self.assertEqual(identity['mentions_legales'], 'Mentions légales test')


@tagged('post_install', '-at_install')
class TestIdentityLocking(TransactionCase):
    """Tests du verrouillage de l'identité après le premier acte."""

    def setUp(self):
        super().setUp()
        self.Config = self.env['etat.civil.config.settings']
        self.Centre = self.env['etat.civil.centre']
        self.Registre = self.env['etat.civil.registre']
        self.Individu = self.env['etat.civil.individu']
        self.AdminUser = self.env.ref('etat_civil.group_etat_civil_admin')

        # Créer un centre et un registre
        self.centre = self.Centre.sudo().create({
            'code_centre': 'TEST',
            'nom_centre': 'Centre Test',
            'commune': 'Commune Test',
            'district_province': 'Region Test',
        })
        self.registre = self.Registre.sudo().create({
            'annee': 2024,
            'type_registre': 'naissance',
            'numero_volume': 1,
            'centre_id': self.centre.id,
        })

        # Créer un individu
        self.individu = self.Individu.sudo().create({
            'nom': 'Test',
            'prenom': 'Enfant',
            'sexe': 'F',
            'date_naissance': '2024-01-15',
            'lieu_naissance': 'Antsohihy',
            'nationalite': 'Malgache',
        })

    def test_identity_locks_after_first_act(self):
        """L'identité se verrouille après le premier acte."""
        config = self.Config.sudo().create({
            'commune_nom_officiel': 'Commune Test',
            'commune_type': 'urbaine',
            'commune_code': 'TEST',
            'region': 'Region',
            'district': 'District',
        })
        self.assertFalse(config.identity_locked, "L'identité ne doit pas être verrouillée sans acte")

        # Créer un acte de naissance
        acte = self.env['etat.civil.acte.naissance'].sudo().create({
            'enfant_id': self.individu.id,
            'mere_id': self.individu.id,
            'registre_id': self.registre.id,
            'lieu_naissance': 'Antsohihy',
            'lieu_accouchement': 'hopital',
            'filiation': 'legitime',
        })
        config_after = self.Config.get_config()
        self.assertTrue(config_after.identity_locked,
                       "L'identité doit être verrouillée après le premier acte")
        self.assertTrue(config_after.locked_at, "La date de verrouillage doit être renseignée")

    def test_locked_critical_fields_readonly(self):
        """Les champs critiques sont protégés quand l'identité est verrouillée."""
        config = self.Config.sudo().create({
            'commune_nom_officiel': 'Commune Test',
            'commune_type': 'urbaine',
            'commune_code': 'TEST',
            'region': 'Region',
            'district': 'District',
        })
        config.sudo().write({'identity_locked': True})

        # Un utilisateur non-tech-admin ne peut pas modifier les champs critiques
        with self.assertRaises(AccessError):
            config.write({'commune_nom_officiel': 'Nouvelle Commune'})

        # Les champs non-critiques restent modifiables
        config.write({'adresse': 'Nouvelle adresse'})
        self.assertEqual(config.adresse, 'Nouvelle adresse')

    def test_tech_admin_can_modify_locked_fields(self):
        """L'admin technique peut modifier les champs critiques verrouillés."""
        config = self.Config.sudo().create({
            'commune_nom_officiel': 'Commune Test',
            'commune_type': 'urbaine',
            'commune_code': 'TEST',
            'region': 'Region',
            'district': 'District',
        })
        config.sudo().write({'identity_locked': True})

        # Sudo pour simuler un admin technique
        tech_group = self.env.ref('etat_civil.group_etat_civil_tech_admin')
        self.env.user.sudo().write({'groups_id': [(4, tech_group.id)]})

        # L'admin technique peut modifier
        config.write({'commune_nom_officiel': 'Nouvelle Commune'})
        self.assertEqual(config.commune_nom_officiel, 'Nouvelle Commune')


@tagged('post_install', '-at_install')
class TestUnlockWizard(TransactionCase):
    """Tests du wizard de déverrouillage."""

    def setUp(self):
        super().setUp()
        self.Config = self.env['etat.civil.config.settings']
        self.Wizard = self.env['etat.civil.unlock.identity.wizard']

    def test_unlock_requires_confirmation(self):
        """Le déverrouillage nécessite la confirmation."""
        config = self.Config.sudo().create({
            'commune_nom_officiel': 'Commune Test',
            'commune_type': 'urbaine',
            'commune_code': 'TEST',
            'region': 'Region',
            'district': 'District',
        })
        config.sudo().write({'identity_locked': True})

        wizard = self.Wizard.create({
            'config_id': config.id,
            'justification': 'Test',
            'confirmation': False,
        })
        with self.assertRaises(ValidationError):
            wizard.action_unlock()

    def test_unlock_requires_justification(self):
        """Le déverrouillage nécessite un motif."""
        config = self.Config.sudo().create({
            'commune_nom_officiel': 'Commune Test',
            'commune_type': 'urbaine',
            'commune_code': 'TEST',
            'region': 'Region',
            'district': 'District',
        })
        config.sudo().write({'identity_locked': True})

        wizard = self.Wizard.create({
            'config_id': config.id,
            'justification': '',
            'confirmation': True,
        })
        with self.assertRaises(ValidationError):
            wizard.action_unlock()

    def test_unlock_requires_tech_admin(self):
        """Seul l'admin technique peut déverrouiller."""
        config = self.Config.sudo().create({
            'commune_nom_officiel': 'Commune Test',
            'commune_type': 'urbaine',
            'commune_code': 'TEST',
            'region': 'Region',
            'district': 'District',
        })
        config.sudo().write({'identity_locked': True})

        wizard = self.Wizard.create({
            'config_id': config.id,
            'justification': 'Test',
            'confirmation': True,
        })
        with self.assertRaises(AccessError):
            wizard.action_unlock()


@tagged('post_install', '-at_install')
class TestConfigInitWizard(TransactionCase):
    """Tests de l'assistant de configuration initiale."""

    def setUp(self):
        super().setUp()
        self.Wizard = self.env['etat.civil.config.init.wizard']
        self.Config = self.env['etat.civil.config.settings']

    def test_default_get_prefills_from_company(self):
        """L'assistant pré-remplit depuis res.company."""
        defaults = self.Wizard.default_get(
            list(self.Wizard._fields.keys())
        )
        self.assertIn('commune_nom_officiel', defaults)
        self.assertEqual(defaults['commune_nom_officiel'], self.env.company.name)

    def test_action_configure_creates_singleton(self):
        """L'action crée le singleton et synchronise res.company."""
        # Supprimer tout singleton existant
        existing = self.Config.sudo().search([])
        if existing:
            existing.sudo().write({'identity_locked': False})
            existing.sudo().unlink()

        wizard = self.Wizard.create({
            'commune_nom_officiel': 'Commune urbaine d\'Antsohihy',
            'commune_type': 'urbaine',
            'commune_code': 'ANTS',
            'region': 'Atsinanana',
            'district': 'Antsohihy',
        })
        wizard.action_configure()

        config = self.Config.get_config()
        self.assertEqual(config.commune_nom_officiel, 'Commune urbaine d\'Antsohihy')
        self.assertEqual(config.commune_code, 'ANTS')
        self.assertEqual(self.env.company.name, 'Commune urbaine d\'Antsohihy')


@tagged('post_install', '-at_install')
class TestReportCommuneIdentity(TransactionCase):
    """Tests que les rapports incluent l'identité de la commune."""

    def test_report_values_include_identity(self):
        """Les valeurs du rapport incluent commune_identity."""
        from odoo.addons.etat_civil.reports.acte_reports import _get_commune_identity

        identity = _get_commune_identity(self.env)
        self.assertIn('nom', identity)
        self.assertIn('code', identity)
        self.assertIn('region', identity)
        self.assertIn('district', identity)
        self.assertIn('mentions_legales', identity)

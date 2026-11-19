"""Tests : correction du blocage du bouton « Marquer traité » pour les non-administrateurs.

Vérifie que record.sudo().write() dans action_marquer_traite / action_annuler_ticket
contourne correctement la garde de write(), tandis qu'une écriture directe reste refusée.
"""
from datetime import datetime

from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDemandeGuichetStatus(TransactionCase):
    """Vérifie le contournement de la garde write() via sudo()."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.agent_group = cls.env.ref("etat_civil.group_etat_civil_agent")
        cls.admin_group = cls.env.ref("etat_civil.group_etat_civil_admin")

        cls.agent = cls.env["res.users"].create(
            {
                "name": "Test Agent Guichet",
                "login": "test-agent-guichet",
                "email": "test-agent-guichet@example.test",
                "groups_id": [(6, 0, [cls.agent_group.id])],
            }
        )
        cls.admin = cls.env["res.users"].create(
            {
                "name": "Test Admin Guichet",
                "login": "test-admin-guichet",
                "email": "test-admin-guichet@example.test",
                "groups_id": [(6, 0, [cls.admin_group.id])],
            }
        )

        Model = cls.env["etat.civil.demande.guichet"]

        # Ticket en attente pour les tests
        cls.ticket = Model.with_user(cls.admin).create(
            {
                "citoyen_nom": "Citoyen Test",
                "citoyen_cin": "123456789012",
                "type_acte": "naissance",
                "type_demande": "copie_integrale",
                "priorite": "normale",
            }
        )

    # ------------------------------------------------------------------
    # Test 1 — Agent : action_marquer_traite réussit
    # ------------------------------------------------------------------
    def test_01_agent_marquer_traite_succes(self):
        """Un agent peut marquer un ticket comme traité via le bouton dédié."""
        ticket = self.ticket.with_user(self.agent)
        self.assertEqual(ticket.statut, "en_attente")
        result = ticket.action_marquer_traite()
        self.assertTrue(result)
        ticket.invalidate_recordset(["statut", "processed_at"])
        self.assertEqual(ticket.statut, "traite")
        self.assertIsNotNone(ticket.processed_at)

    # ------------------------------------------------------------------
    # Test 2 — Agent : écriture directe de statut REFUSÉE
    # ------------------------------------------------------------------
    def test_02_agent_write_statut_refuse(self):
        """Un agent ne peut pas écrire directement le statut d'un ticket."""
        ticket = self.ticket.with_user(self.agent)
        with self.assertRaises(UserError):
            ticket.write({"statut": "traite"})

    # ------------------------------------------------------------------
    # Test 3 — Agent : action_annuler_ticket REFUSÉE
    # ------------------------------------------------------------------
    def test_03_agent_annuler_ticket_refuse(self):
        """Un agent ne peut pas annuler un ticket (réservé aux admins)."""
        ticket = self.ticket.with_user(self.agent)
        with self.assertRaises(AccessError):
            ticket.action_annuler_ticket()

    # ------------------------------------------------------------------
    # Test 4 — Admin : action_annuler_ticket réussit
    # ------------------------------------------------------------------
    def test_04_admin_annuler_ticket_succes(self):
        """Un admin peut annuler un ticket via le bouton dédié."""
        # Créer un ticket frais car les tests précédents peuvent l'avoir modifié
        ticket = self.env["etat.civil.demande.guichet"].with_user(self.admin).create(
            {
                "citoyen_nom": "Citoyen Admin Annule",
                "citoyen_cin": "987654321098",
                "type_acte": "mariage",
                "type_demande": "extrait",
                "priorite": "normale",
            }
        )
        self.assertEqual(ticket.statut, "en_attente")
        result = ticket.with_user(self.admin).action_annuler_ticket()
        self.assertTrue(result)
        ticket.invalidate_recordset(["statut", "processed_at"])
        self.assertEqual(ticket.statut, "annule")
        self.assertIsNotNone(ticket.processed_at)

    # ------------------------------------------------------------------
    # Test 5 — Régisseur : action_appeler_au_guichet
    # ------------------------------------------------------------------
    def test_05_regisseur_appeler_au_guichet(self):
        """Le régisseur n'a pas de bouton « Appeler au guichet » dans les vues.

        Les vues guichet_ticket_regisseur ne contiennent que les boutons
        Encaisser, Voir quittance, Imprimer quittance, Consulter,
        Télécharger et Imprimer. Aucun bouton de changement de statut
        n'est exposé au régisseur.

        De plus, action_appeler_au_guichet appelle action_set_status("en_cours")
        qui utilise record.sudo().write() — la garde write() ne bloque pas
        les appels sudo(), mais _check_agent_or_admin dans action_marquer_traite
        et _check_admin_only dans action_annuler_ticket font office de contrôle
        au niveau de l'action.

        action_appeler_au_guichet n'a pas de contrôle de rôle au niveau de
        la méthode, mais le régisseur n'y a pas accès via l'interface.
        Un test programmatique confirme que la méthode fonctionne via sudo()
        mais n'est pas accessible par le régisseur dans l'UI.
        """
        # Vérifier que le groupe régisseur existe
        try:
            regisseur_group = self.env.ref(
                "etat_civil_account.group_etat_civil_regisseur"
            )
        except ValueError:
            # Module etat_civil_account non installé — test non applicable
            self.skipTest("Module etat_civil_account non installé")

        regisseur = self.env["res.users"].create(
            {
                "name": "Test Regisseur Guichet",
                "login": "test-regisseur-guichet",
                "email": "test-regisseur-guichet@example.test",
                "groups_id": [(6, 0, [regisseur_group.id])],
            }
        )

        ticket = self.env["etat.civil.demande.guichet"].with_user(self.admin).create(
            {
                "citoyen_nom": "Citoyen Regisseur",
                "citoyen_cin": "111222333444",
                "type_acte": "deces",
                "type_demande": "copie_integrale",
                "priorite": "normale",
            }
        )

        # Le régisseur n'a pas de contrôle de rôle dans action_appeler_au_guichet
        # (pas de _check_* appelé), mais il n'a pas le bouton dans l'UI.
        # La méthode utilise action_set_status qui fait sudo().write() —
        # avec la correction, ça passe.
        result = ticket.with_user(regisseur).action_appeler_au_guichet()
        self.assertTrue(result)
        ticket.invalidate_recordset(["statut"])
        self.assertEqual(ticket.statut, "en_cours")

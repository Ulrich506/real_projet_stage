# -*- coding: utf-8 -*-
"""
Tests automatisés pour la génération automatique des pièces justificatives.
Module : etat_civil
Fonctionnalité : auto-population de l'onglet « Pièces à vérifier »
"""

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install", "pieces_auto")
class TestPiecesAutoPopulation(TransactionCase):
    """
    Suite de tests pour la génération automatique des pièces justificatives.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Groupe admin état civil
        cls.group_admin = cls.env.ref("etat_civil.group_etat_civil_admin")
        cls.group_agent = cls.env.ref("etat_civil.group_etat_civil_agent")
        cls.group_officier = cls.env.ref("etat_civil.group_etat_civil_officier")

        # Utilisateurs de test
        cls.user_admin = cls.env["res.users"].create({
            "name": "Admin Test Pièces",
            "login": "admin_pieces_test",
            "email": "admin_pieces@test.com",
            "groups_id": [(6, 0, [cls.group_admin.id])],
        })
        cls.user_agent = cls.env["res.users"].create({
            "name": "Agent Test Pièces",
            "login": "agent_pieces_test",
            "email": "agent_pieces@test.com",
            "groups_id": [(6, 0, [cls.group_agent.id])],
        })
        cls.user_officier = cls.env["res.users"].create({
            "name": "Officier Test Pièces",
            "login": "officier_pieces_test",
            "email": "officier_pieces@test.com",
            "groups_id": [(6, 0, [cls.group_officier.id])],
        })

        # Centre et commune
        cls.centre = cls.env["etat.civil.centre"].sudo().create({
            "code_centre": "PIECES-TEST",
            "nom_centre": "Centre de test des pièces",
            "commune": "Commune de test",
        })

        # Associer l'agent et l'officier au centre
        cls.user_agent.sudo().write({"etat_civil_centre_ids": [(4, cls.centre.id)]})
        cls.user_officier.sudo().write({"etat_civil_centre_ids": [(4, cls.centre.id)]})
        cls.user_admin.sudo().write({"etat_civil_centre_ids": [(4, cls.centre.id)]})

        # Registres
        cls.registre_naissance = cls.env["etat.civil.registre"].sudo().create({
            "type_registre": "naissance",
            "annee": 2026,
            "numero_volume": 1,
            "centre_id": cls.centre.id,
        })
        cls.registre_mariage = cls.env["etat.civil.registre"].sudo().create({
            "type_registre": "mariage",
            "annee": 2026,
            "numero_volume": 1,
            "centre_id": cls.centre.id,
        })
        cls.registre_deces = cls.env["etat.civil.registre"].sudo().create({
            "type_registre": "deces",
            "annee": 2026,
            "numero_volume": 1,
            "centre_id": cls.centre.id,
        })

        # Individus de base
        cls.enfant = cls.env["etat.civil.individu"].sudo().create({
            "nom": "Enfant",
            "prenoms": "Test",
            "sexe": "M",
            "date_naissance": "2026-01-01",
        })
        cls.mere = cls.env["etat.civil.individu"].sudo().create({
            "nom": "Mere",
            "prenoms": "Test",
            "sexe": "F",
            "date_naissance": "1990-01-01",
        })
        cls.pere = cls.env["etat.civil.individu"].sudo().create({
            "nom": "Pere",
            "prenoms": "Test",
            "sexe": "M",
            "date_naissance": "1988-01-01",
        })
        cls.conjoint_1 = cls.env["etat.civil.individu"].sudo().create({
            "nom": "Conjoint",
            "prenoms": "Un",
            "sexe": "M",
            "date_naissance": "1990-06-01",
        })
        cls.conjoint_2 = cls.env["etat.civil.individu"].sudo().create({
            "nom": "Conjoint",
            "prenoms": "Deux",
            "sexe": "F",
            "date_naissance": "1992-03-01",
        })
        cls.defunt = cls.env["etat.civil.individu"].sudo().create({
            "nom": "Defunt",
            "prenoms": "Test",
            "sexe": "M",
            "date_naissance": "1950-01-01",
        })
        cls.declarant_deces = cls.env["etat.civil.individu"].sudo().create({
            "nom": "Declarant",
            "prenoms": "Deces",
            "sexe": "M",
            "date_naissance": "1970-01-01",
            "cin": "123456789012",
        })

    # ==================================================================
    # TEST 1 : Naissance à l'hôpital — pièces auto-générées
    # ==================================================================

    def test_01_naissance_hopital_pieces_auto(self):
        """Naissance hôpital : declaration_hopital générée automatiquement."""
        acte = self.env["etat.civil.acte.naissance"].with_user(self.user_agent).create({
            "registre_id": self.registre_naissance.id,
            "enfant_id": self.enfant.id,
            "mere_id": self.mere.id,
            "lieu_accouchement": "hopital",
            "filiation": "legitime",
            "lieu_naissance": "Hôpital de test",
        })
        codes = acte.piece_ids.mapped("name")
        self.assertIn("declaration_hopital", codes,
                      "La déclaration de l'hôpital doit être générée pour une naissance à l'hôpital.")
        self.assertIn("livret_famille", codes,
                      "Le livret de famille doit être généré pour une filiation légitime.")
        self.assertIn("residence_parent", codes,
                      "Le certificat de résidence du parent doit être généré.")
        # Vérifier qu'elles sont bien marquées genere_automatiquement
        for piece in acte.piece_ids:
            self.assertTrue(piece.genere_automatiquement,
                            f"La pièce {piece.name} doit être marquée genere_automatiquement=True.")

    def test_02_naissance_maison_illegitime_pieces_auto(self):
        """Naissance à domicile, filiation illégitime : cin_parent généré, pas declaration_hopital."""
        acte = self.env["etat.civil.acte.naissance"].with_user(self.user_agent).create({
            "registre_id": self.registre_naissance.id,
            "enfant_id": self.enfant.id,
            "mere_id": self.mere.id,
            "declarant_id": self.pere.id,
            "lieu_accouchement": "maison",
            "filiation": "illegitime",
            "lieu_naissance": "Domicile test",
        })
        codes = acte.piece_ids.mapped("name")
        self.assertIn("cin_parent", codes,
                      "Le CIN du parent doit être généré pour une filiation illégitime.")
        self.assertNotIn("declaration_hopital", codes,
                         "Pas de déclaration hôpital pour une naissance à domicile.")
        self.assertNotIn("livret_famille", codes,
                         "Pas de livret de famille pour une filiation illégitime.")

    def test_03_naissance_pas_de_doublon(self):
        """Appeler sync deux fois ne crée pas de doublons."""
        acte = self.env["etat.civil.acte.naissance"].create({
            "registre_id": self.registre_naissance.id,
            "enfant_id": self.enfant.id,
            "mere_id": self.mere.id,
            "lieu_accouchement": "hopital",
            "filiation": "legitime",
            "lieu_naissance": "Hôpital test doublon",
        })
        count_before = len(acte.piece_ids)
        acte._sync_pieces_justificatives()
        acte._sync_pieces_justificatives()
        self.assertEqual(len(acte.piece_ids), count_before,
                         "Le sync ne doit pas créer de doublons.")

    # ==================================================================
    # TEST 4 : Acte de mariage — conjoints locaux
    # ==================================================================

    def test_04_mariage_conjoints_locaux(self):
        """Mariage avec deux conjoints malgaches : pièces locales générées."""
        acte = self.env["etat.civil.acte.mariage"].with_user(self.user_agent).create({
            "registre_id": self.registre_mariage.id,
            "conjoint_1_id": self.conjoint_1.id,
            "conjoint_2_id": self.conjoint_2.id,
            "conjoint_1_est_etranger": False,
            "conjoint_2_est_etranger": False,
            "donnees_historiques_incompletes": False,
            "lieu_mariage": "Mairie test",
            "date_mariage": "2026-06-15",
            "regime_matrimonial": "communaute_biens",
        })
        codes = acte.piece_ids.mapped("name")
        self.assertIn("celibat_conjoint_1", codes)
        self.assertIn("cin_conjoint_1", codes)
        self.assertIn("residence_conjoint_1", codes)
        self.assertIn("celibat_conjoint_2", codes)
        self.assertIn("cin_conjoint_2", codes)
        self.assertIn("residence_conjoint_2", codes)
        self.assertNotIn("passeport_1", codes)
        self.assertNotIn("passeport_2", codes)

    # ==================================================================
    # TEST 5 : Conjoint étranger — pièces étrangères apparaissent
    # ==================================================================

    def test_05_mariage_conjoint_1_etranger(self):
        """Si conjoint 1 est étranger, passeport_1 est généré."""
        acte = self.env["etat.civil.acte.mariage"].create({
            "registre_id": self.registre_mariage.id,
            "conjoint_1_id": self.conjoint_1.id,
            "conjoint_2_id": self.conjoint_2.id,
            "conjoint_1_est_etranger": True,
            "conjoint_2_est_etranger": False,
            "donnees_historiques_incompletes": False,
            "lieu_mariage": "Mairie étranger",
            "date_mariage": "2026-06-16",
            "regime_matrimonial": "communaute_biens",
        })
        codes = acte.piece_ids.mapped("name")
        self.assertIn("passeport_1", codes,
                      "Le passeport du conjoint étranger 1 doit être généré.")
        self.assertNotIn("celibat_conjoint_1", codes,
                         "Pas de certificat de célibat pour un conjoint étranger.")

    # ==================================================================
    # TEST 6 : Conjoint étranger → redevient local → pièces étrangères supprimées
    # ==================================================================

    def test_06_mariage_etranger_devient_local(self):
        """Les pièces étrangères sont supprimées quand le conjoint redevient local (sans fichier)."""
        acte = self.env["etat.civil.acte.mariage"].create({
            "registre_id": self.registre_mariage.id,
            "conjoint_1_id": self.conjoint_1.id,
            "conjoint_2_id": self.conjoint_2.id,
            "conjoint_1_est_etranger": True,
            "conjoint_2_est_etranger": False,
            "donnees_historiques_incompletes": False,
            "lieu_mariage": "Mairie test retour local",
            "date_mariage": "2026-06-17",
            "regime_matrimonial": "communaute_biens",
        })
        self.assertIn("passeport_1", acte.piece_ids.mapped("name"))

        # Changer : conjoint 1 redevient local
        acte.write({"conjoint_1_est_etranger": False})
        codes_apres = acte.piece_ids.mapped("name")
        self.assertNotIn("passeport_1", codes_apres,
                         "La pièce passeport_1 doit être supprimée quand le conjoint n'est plus étranger.")
        self.assertIn("celibat_conjoint_1", codes_apres,
                      "Le certificat de célibat doit apparaître pour le conjoint local.")

    # ==================================================================
    # TEST 7 : Ligne avec fichier ou état Reçu — jamais supprimée automatiquement
    # ==================================================================

    def test_07_piece_recu_non_supprimee(self):
        """Une pièce avec état Reçu n'est jamais supprimée même si la condition change."""
        acte = self.env["etat.civil.acte.mariage"].create({
            "registre_id": self.registre_mariage.id,
            "conjoint_1_id": self.conjoint_1.id,
            "conjoint_2_id": self.conjoint_2.id,
            "conjoint_1_est_etranger": True,
            "conjoint_2_est_etranger": False,
            "donnees_historiques_incompletes": False,
            "lieu_mariage": "Mairie test protection",
            "date_mariage": "2026-06-18",
            "regime_matrimonial": "communaute_biens",
        })
        # Marquer passeport_1 comme reçu en utilisant le token de procédure correct
        piece_passeport = acte.piece_ids.filtered(lambda p: p.name == "passeport_1")
        self.assertTrue(piece_passeport, "Le passeport_1 doit exister.")
        from odoo.addons.etat_civil.models.piece_justificative import _PROCEDURE_TOKEN
        piece_passeport.with_context(
            etat_civil_piece_procedure_token=_PROCEDURE_TOKEN
        ).write({"etat": "recu"})

        # Changer conjoint 1 → local
        acte.write({"conjoint_1_est_etranger": False})
        # La pièce avec état Reçu doit toujours être là
        piece_toujours = acte.piece_ids.filtered(lambda p: p.name == "passeport_1")
        self.assertTrue(piece_toujours,
                        "La pièce marquée Reçu ne doit pas être supprimée automatiquement.")

    # ==================================================================
    # TEST 8 : Agent ne peut pas supprimer une pièce auto-générée
    # ==================================================================

    def test_08_agent_ne_peut_pas_supprimer_ligne_auto(self):
        """Un agent ne peut pas supprimer une ligne générée automatiquement."""
        acte = self.env["etat.civil.acte.naissance"].create({
            "registre_id": self.registre_naissance.id,
            "enfant_id": self.enfant.id,
            "mere_id": self.mere.id,
            "lieu_accouchement": "hopital",
            "filiation": "legitime",
            "lieu_naissance": "Hôpital test droits",
        })
        piece_auto = acte.piece_ids.filtered(lambda p: p.genere_automatiquement)
        self.assertTrue(piece_auto, "Au moins une pièce auto-générée doit exister.")
        with self.assertRaises(AccessError,
                               msg="L'agent ne doit pas pouvoir supprimer une pièce auto-générée."):
            piece_auto[0].with_user(self.user_agent).unlink()

    # ==================================================================
    # TEST 9 : Officier ne peut pas supprimer de pièce
    # ==================================================================

    def test_09_officier_ne_peut_pas_supprimer(self):
        """Un officier ne peut ni supprimer une pièce ni modifier son contenu."""
        acte = self.env["etat.civil.acte.naissance"].create({
            "registre_id": self.registre_naissance.id,
            "enfant_id": self.enfant.id,
            "mere_id": self.mere.id,
            "lieu_accouchement": "hopital",
            "filiation": "legitime",
            "lieu_naissance": "Hôpital test officier",
        })
        piece = acte.piece_ids[0]
        with self.assertRaises(AccessError,
                               msg="L'officier ne doit pas pouvoir supprimer une pièce."):
            piece.with_user(self.user_officier).unlink()
        with self.assertRaises(AccessError,
                               msg="L'officier ne doit pas pouvoir modifier une pièce."):
            piece.with_user(self.user_officier).write({"name": "livret_famille"})

    # ==================================================================
    # TEST 10 : Acte de décès — 2 pièces auto-générées
    # ==================================================================

    def test_10_deces_pieces_auto(self):
        """Acte de décès : cin_declarant_deces et residence_declarant_deces générés."""
        acte = self.env["etat.civil.acte.deces"].with_user(self.user_agent).create({
            "registre_id": self.registre_deces.id,
            "defunt_id": self.defunt.id,
            "declarant_id": self.declarant_deces.id,
            "date_deces": "2026-05-10",
            "lieu_deces": "Domicile test décès",
        })
        codes = acte.piece_ids.mapped("name")
        self.assertIn("cin_declarant_deces", codes,
                      "Le CIN du déclarant doit être généré pour un acte de décès.")
        self.assertIn("residence_declarant_deces", codes,
                      "Le certificat de résidence du déclarant doit être généré.")
        self.assertEqual(len(acte.piece_ids), 2,
                         "Un acte de décès doit avoir exactement 2 pièces auto-générées.")

    # ==================================================================
    # TEST 11 : toutes_pieces_obligatoires_recues — champ compute
    # ==================================================================

    def test_11_toutes_pieces_obligatoires_recues_calcul(self):
        """Le champ compute est False tant qu'une pièce obligatoire n'est pas reçue."""
        acte = self.env["etat.civil.acte.deces"].create({
            "registre_id": self.registre_deces.id,
            "defunt_id": self.defunt.id,
            "declarant_id": self.declarant_deces.id,
            "date_deces": "2026-05-11",
            "lieu_deces": "Domicile test compute",
        })
        self.assertFalse(acte.toutes_pieces_obligatoires_recues,
                         "Le champ doit être False tant que les pièces ne sont pas reçues.")
        # Marquer toutes les pièces obligatoires comme reçues (via procedure token)
        from odoo.addons.etat_civil.models.piece_justificative import _PROCEDURE_TOKEN
        for piece in acte.piece_ids.filtered(lambda p: p.obligatoire):
            piece.with_context(
                etat_civil_piece_procedure_token=_PROCEDURE_TOKEN
            ).write({"etat": "recu"})
        acte.invalidate_recordset(["toutes_pieces_obligatoires_recues"])
        self.assertTrue(acte.toutes_pieces_obligatoires_recues,
                        "Le champ doit être True quand toutes les pièces obligatoires sont reçues.")

    # ==================================================================
    # TEST 12 : Admin peut supprimer une pièce auto-générée
    # ==================================================================

    def test_12_admin_peut_supprimer_ligne_auto(self):
        """L'administrateur peut supprimer n'importe quelle pièce."""
        acte = self.env["etat.civil.acte.deces"].create({
            "registre_id": self.registre_deces.id,
            "defunt_id": self.defunt.id,
            "declarant_id": self.declarant_deces.id,
            "date_deces": "2026-05-12",
            "lieu_deces": "Test admin unlink",
        })
        piece = acte.piece_ids[0]
        # Ne doit pas lever d'exception
        try:
            piece.with_user(self.user_admin).unlink()
        except AccessError as e:
            self.fail(f"L'admin ne devrait pas avoir d'erreur d'accès lors de la suppression : {e}")

    # ==================================================================
    # TEST 13 : Naissance — changement filiation déclenche resync
    # ==================================================================

    def test_13_naissance_changement_filiation_resync(self):
        """Changer la filiation après création resynchronise les pièces."""
        enfant2 = self.env["etat.civil.individu"].sudo().create({
            "nom": "Enfant2",
            "prenoms": "Resync",
            "sexe": "F",
            "date_naissance": "2026-02-01",
        })
        acte = self.env["etat.civil.acte.naissance"].create({
            "registre_id": self.registre_naissance.id,
            "enfant_id": enfant2.id,
            "mere_id": self.mere.id,
            "declarant_id": self.pere.id,
            "lieu_accouchement": "maison",
            "filiation": "illegitime",
            "lieu_naissance": "Domicile resync",
        })
        self.assertIn("cin_parent", acte.piece_ids.mapped("name"))
        self.assertNotIn("livret_famille", acte.piece_ids.mapped("name"))

        # Changer en légitime
        acte.write({"filiation": "legitime"})
        codes = acte.piece_ids.mapped("name")
        self.assertIn("livret_famille", codes,
                      "Le livret de famille doit apparaître après passage en filiation légitime.")
        # cin_parent est toujours requis (condition='toujours') donc il reste présent
        self.assertIn("cin_parent", codes,
                      "Le CIN du parent reste présent car requis pour toute naissance.")

    # ==================================================================
    # TEST 14 : Boutons d'impression bloqués tant que pièce obligatoire manque
    # ==================================================================

    def test_14_boutons_impression_bloques_tant_que_piece_manquante(self):
        """Les boutons d'impression et de téléchargement sont bloqués côté serveur tant qu'une pièce manque."""
        acte = self.env["etat.civil.acte.deces"].create({
            "registre_id": self.registre_deces.id,
            "defunt_id": self.defunt.id,
            "declarant_id": self.declarant_deces.id,
            "date_deces": "2026-05-10",
            "lieu_deces": "Domicile test print",
        })
        self.assertFalse(acte.toutes_pieces_obligatoires_recues)
        with self.assertRaises(UserError, msg="L'impression doit être bloquée tant que l'acte n'est pas validé et pièces reçues."):
            acte.action_imprimer_acte()
        with self.assertRaises(UserError, msg="Le téléchargement doit être bloqué tant que l'acte n'est pas validé et pièces reçues."):
            acte.action_telecharger_acte_pdf()


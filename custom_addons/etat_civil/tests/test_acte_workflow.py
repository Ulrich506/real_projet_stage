import json

from odoo.exceptions import AccessError, UserError
from odoo.tests import HttpCase, TransactionCase, tagged


ACT_TYPES = ("naissance", "mariage", "deces")
MODEL_BY_TYPE = {
    "naissance": "etat.civil.acte.naissance",
    "mariage": "etat.civil.acte.mariage",
    "deces": "etat.civil.acte.deces",
}


class ActeWorkflowFixtures:
    def _create_act(self, acte_type, suffix):
        person_model = self.env["etat.civil.individu"].sudo()
        if acte_type == "naissance":
            enfant = person_model.create({
                "nom": f"Enfant {suffix}",
                "sexe": "M",
                "date_naissance": "2020-01-01",
            })
            mere = person_model.create({
                "nom": f"Mère {suffix}",
                "sexe": "F",
                "date_naissance": "1990-01-01",
            })
            values = {
                "enfant_id": enfant.id,
                "mere_id": mere.id,
                "lieu_naissance": "Commune de test",
            }
        elif acte_type == "mariage":
            spouse_1 = person_model.create({
                "nom": f"Conjoint A {suffix}",
                "sexe": "M",
                "date_naissance": "1980-01-01",
            })
            spouse_2 = person_model.create({
                "nom": f"Conjoint B {suffix}",
                "sexe": "F",
                "date_naissance": "1981-01-01",
            })
            witness_1 = person_model.create({
                "nom": f"Témoin A {suffix}",
                "sexe": "M",
                "date_naissance": "1970-01-01",
            })
            witness_2 = person_model.create({
                "nom": f"Témoin B {suffix}",
                "sexe": "F",
                "date_naissance": "1971-01-01",
            })
            values = {
                "conjoint_1_id": spouse_1.id,
                "conjoint_2_id": spouse_2.id,
                "temoin_1_id": witness_1.id,
                "temoin_2_id": witness_2.id,
                "lieu_mariage": "Commune de test",
                "regime_matrimonial": "communaute_biens",
            }
        else:
            defunt = person_model.create({
                "nom": f"Défunt {suffix}",
                "sexe": "M",
                "date_naissance": "1950-01-01",
            })
            declarant = person_model.create({
                "nom": f"Déclarant {suffix}",
                "sexe": "F",
                "date_naissance": "1980-01-01",
            })
            values = {
                "defunt_id": defunt.id,
                "declarant_id": declarant.id,
                "date_deces": "2020-01-01",
                "lieu_deces": "Commune de test",
            }

        values.update({
            "registre_id": self.registers[acte_type].id,
            "texte_integral_acte": f"Acte de test {acte_type} {suffix}.",
        })
        return self.env[MODEL_BY_TYPE[acte_type]].with_user(self.agent).create(values)

    def _transmit(self, acte):
        acte.piece_ids.with_user(self.agent).write({"etat": "recu"})
        acte.with_user(self.agent).action_envoyer_validation(officier=self.officer)

    def _verify_and_validate(self, acte):
        acte.piece_ids.with_user(self.officer).write({"etat": "verifie"})
        acte.with_user(self.officer).action_valider_acte()


@tagged("post_install", "-at_install")
class TestActeWorkflowTransitions(ActeWorkflowFixtures, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.centre = cls.env["etat.civil.centre"].sudo().create({
            "code_centre": "WF-TRANSITIONS",
            "nom_centre": "Centre workflow transitions",
            "commune": "Commune de test",
        })
        cls.registers = {}
        for index, acte_type in enumerate(ACT_TYPES, 1):
            cls.registers[acte_type] = cls.env["etat.civil.registre"].sudo().create({
                "annee": 2026,
                "type_registre": acte_type,
                "numero_volume": index,
                "centre_id": cls.centre.id,
            })

        cls.agent = cls.env["res.users"].sudo().create({
            "name": "Agent Workflow Test",
            "login": "agent-workflow-transitions",
            "email": "agent-workflow-transitions@example.test",
            "groups_id": [(6, 0, [cls.env.ref("etat_civil.group_etat_civil_agent").id])],
            "etat_civil_centre_ids": [(6, 0, [cls.centre.id])],
        })
        cls.officer = cls.env["res.users"].sudo().create({
            "name": "Officier Workflow Test",
            "login": "officer-workflow-transitions",
            "email": "officer-workflow-transitions@example.test",
            "groups_id": [(6, 0, [cls.env.ref("etat_civil.group_etat_civil_officier").id])],
            "etat_civil_centre_ids": [(6, 0, [cls.centre.id])],
        })

    def test_all_act_types_reject_invalid_states_and_run_validation_effects(self):
        for index, acte_type in enumerate(ACT_TYPES, 1):
            with self.subTest(acte_type=acte_type):
                acte = self._create_act(acte_type, f"transition-{index}")

                with self.assertRaises(UserError):
                    acte.with_user(self.officer).action_valider_acte()

                self._transmit(acte)
                acte.with_user(self.officer).action_retourner_correction("Correction de test.")
                with self.assertRaises(UserError):
                    acte.with_user(self.officer).action_valider_acte()

                self._transmit(acte)
                self._verify_and_validate(acte)
                self.assertEqual(acte.statut, "valide")
                with self.assertRaises(UserError):
                    acte.with_user(self.officer).action_valider_acte()

                if acte_type == "mariage":
                    self.assertEqual(len(acte.notification_mention_ids), 2)
                    self.assertEqual(acte.conjoint_1_id.situation_matrimoniale, "marie")
                    self.assertEqual(acte.conjoint_2_id.situation_matrimoniale, "marie")
                elif acte_type == "deces":
                    self.assertEqual(acte.defunt_id.statut_vital, "decede")

                acte.with_user(self.officer).action_annuler_acte("Motif de test.")
                self.assertTrue(acte.motif_annulation.startswith("ANNULATION"))
                with self.assertRaises(UserError):
                    acte.with_user(self.officer).action_valider_acte()

                acte.with_user(self.officer).action_archiver_acte()
                with self.assertRaises(UserError):
                    acte.with_user(self.officer).action_valider_acte()

    def test_officer_record_rule_preserves_read_access_in_own_centre(self):
        acte = self._create_act("naissance", "read")
        visible = self.env["etat.civil.acte.naissance"].with_user(self.officer).search([
            ("id", "=", acte.id),
        ])
        self.assertEqual(visible, acte)
        self.assertFalse(self.officer.has_group("etat_civil.group_etat_civil_agent"))


@tagged("post_install", "-at_install")
class TestActeWorkflowApi(ActeWorkflowFixtures, HttpCase):
    password = "Workflow-Test-Only-Password"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.centre = cls.env["etat.civil.centre"].sudo().create({
            "code_centre": "WF-API",
            "nom_centre": "Centre workflow API",
            "commune": "Commune de test",
        })
        cls.registers = {}
        for index, acte_type in enumerate(ACT_TYPES, 1):
            cls.registers[acte_type] = cls.env["etat.civil.registre"].sudo().create({
                "annee": 2026,
                "type_registre": acte_type,
                "numero_volume": index,
                "centre_id": cls.centre.id,
            })

        cls.agent = cls.env["res.users"].sudo().create({
            "name": "Agent Workflow API Test",
            "login": "agent-workflow-api",
            "email": "agent-workflow-api@example.test",
            "password": cls.password,
            "groups_id": [(6, 0, [cls.env.ref("etat_civil.group_etat_civil_agent").id])],
            "etat_civil_centre_ids": [(6, 0, [cls.centre.id])],
        })
        cls.officer = cls.env["res.users"].sudo().create({
            "name": "Officier Workflow API Test",
            "login": "officer-workflow-api",
            "email": "officer-workflow-api@example.test",
            "password": cls.password,
            "groups_id": [(6, 0, [cls.env.ref("etat_civil.group_etat_civil_officier").id])],
            "etat_civil_centre_ids": [(6, 0, [cls.centre.id])],
        })

    def test_specific_api_routes_enforce_the_workflow_for_each_act_type(self):
        self.authenticate(self.officer.login, self.password)
        specific_routes = {
            "naissance": "naissance",
            "mariage": "mariage",
            "deces": "deces",
        }
        for index, acte_type in enumerate(ACT_TYPES, 1):
            with self.subTest(acte_type=acte_type):
                self.authenticate(self.officer.login, self.password)
                acte = self._create_act(acte_type, f"api-{index}")
                unified_url = f"/api/v1/actes/{acte_type}/{acte.id}/valider"
                draft_response = self.url_open(
                    unified_url,
                    data=json.dumps({}),
                    headers={"Content-Type": "application/json"},
                )
                self.assertEqual(draft_response.status_code, 409)
                self.assertEqual(acte.statut, "brouillon")

                self.authenticate(self.agent.login, self.password)
                acte.piece_ids.with_user(self.agent).write({"etat": "recu"})
                transmit_response = self.url_open(
                    f"/api/v1/actes/{acte_type}/{acte.id}/transmettre",
                    data=json.dumps({"officier_id": self.officer.id}),
                    headers={"Content-Type": "application/json"},
                )
                self.assertEqual(transmit_response.status_code, 200, transmit_response.text)
                self.assertEqual(acte.statut, "en_attente")
                self.assertEqual(acte.officier_validateur_id, self.officer)

                self.authenticate(self.officer.login, self.password)
                acte.piece_ids.with_user(self.officer).write({"etat": "verifie"})
                specific_url = f"/api/v1/actes/{specific_routes[acte_type]}/{acte.id}/valider"
                response = self.url_open(
                    specific_url,
                    data=json.dumps({}),
                    headers={"Content-Type": "application/json"},
                )
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(acte.statut, "valide")
                body = json.loads(response.content)
                self.assertEqual(body["officier_responsable"]["id"], self.officer.id)
                self.assertTrue(body["qr_verification_payload"])

                if acte_type == "mariage":
                    self.assertEqual(len(acte.notification_mention_ids), 2)
                elif acte_type == "deces":
                    self.assertEqual(acte.defunt_id.statut_vital, "decede")

                self.authenticate(self.agent.login, self.password)

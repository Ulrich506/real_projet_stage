import base64
import io
import json
from unittest.mock import patch

from PIL import Image

from odoo.exceptions import AccessError, UserError, ValidationError
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

                if acte_type == "mariage":
                    self.assertEqual(
                        acte.conjoint_1_id.situation_matrimoniale,
                        "celibataire",
                    )
                    self.assertEqual(
                        acte.conjoint_2_id.situation_matrimoniale,
                        "celibataire",
                    )

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
                    acte.piece_ids.with_user(self.agent).write({"etat": "recu"})
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
                with self.assertRaises(UserError):
                    acte.with_user(self.officer).write({"texte_integral_acte": "Modification archive."})
                with self.assertRaises(UserError):
                    acte.with_user(self.officer).write({"mention_ids": [(0, 0, {
                        "type_mention": "autre",
                        "contenu": "Mention interdite après archivage.",
                    })]})

    def test_officer_record_rule_preserves_read_access_in_own_centre(self):
        acte = self._create_act("naissance", "read")
        visible = self.env["etat.civil.acte.naissance"].with_user(self.officer).search([
            ("id", "=", acte.id),
        ])
        self.assertEqual(visible, acte)
        self.assertFalse(self.officer.has_group("etat_civil.group_etat_civil_agent"))

    def test_orphan_attachment_is_relinked_to_piece_for_agent_read_access(self):
        acte = self._create_act("mariage", "attachment-relink")
        piece = acte.piece_ids[0]
        attachment = self.env["ir.attachment"].sudo().create({
            "name": "wall2.jpeg",
            "datas": base64.b64encode(b"image-bytes"),
            "res_model": "etat.civil.piece.justificative",
            "res_id": 0,
        })
        piece.sudo().write({"attachment_ids": [(4, attachment.id)]})

        attachment.invalidate_recordset(["res_model", "res_id"])
        self.assertEqual(attachment.res_model, piece._name)
        self.assertEqual(attachment.res_id, piece.id)
        self.assertEqual(
            attachment.with_user(self.agent).read(["name"])[0]["name"],
            "wall2.jpeg",
        )

    def test_piece_receipt_and_verification_actions_are_persistent_and_audited(self):
        acte = self._create_act("naissance", "piece-audit")
        piece = acte.piece_ids[0]

        with self.assertRaises(AccessError):
            piece.with_user(self.officer).action_mark_received()

        before_receipt = len(acte.message_ids)
        piece.with_user(self.agent).action_mark_received()
        self.assertEqual(piece.etat, "recu")
        self.assertEqual(piece.recu_par_id, self.agent)
        self.assertTrue(piece.date_reception)
        self.assertEqual(
            piece.with_user(self.officer).read(["etat"])[0]["etat"],
            "recu",
        )
        self.assertEqual(len(acte.message_ids), before_receipt)
        with self.assertRaises(AccessError):
            piece.with_user(self.agent).write({"recu_par_id": self.officer.id})

        piece.with_user(self.agent).action_mark_received()
        self.assertEqual(len(acte.message_ids), before_receipt)

        with self.assertRaises(AccessError):
            piece.with_user(self.agent).action_mark_verified()

        self._transmit(acte)
        before_verification = len(acte.message_ids)
        piece.with_user(self.officer).action_mark_verified()
        self.assertEqual(piece.etat, "verifie")
        self.assertEqual(piece.verifie_par_id, self.officer)
        self.assertTrue(piece.date_verification)
        self.assertEqual(len(acte.message_ids), before_verification)

        piece.with_user(self.officer).action_mark_verified()
        self.assertEqual(len(acte.message_ids), before_verification)

    def test_piece_actions_are_separated_in_each_act_form(self):
        model_views = (
            ("etat.civil.acte.naissance", "view_etat_civil_acte_naissance_form"),
            ("etat.civil.acte.mariage", "view_etat_civil_acte_mariage_form"),
            ("etat.civil.acte.deces", "view_etat_civil_acte_deces_form"),
        )
        admin = self.env["res.users"].sudo().create({
            "name": "Administrateur pièces vues",
            "login": "admin-piece-view-test",
            "groups_id": [(6, 0, [self.env.ref("etat_civil.group_etat_civil_admin").id])],
        })
        for model_name, view_id in model_views:
            with self.subTest(view_id=view_id):
                view = self.env.ref(f"etat_civil.{view_id}")
                arch = view.arch_db
                self.assertIn('<field name="etat" readonly="1"/>', arch)
                for user, visible, hidden in (
                    (self.agent, "action_mark_received", "action_mark_verified"),
                    (self.officer, "action_mark_verified", "action_mark_received"),
                ):
                    user_arch = self.env[model_name].with_user(user).get_view(
                        view_id=view.id,
                        view_type="form",
                    )["arch"]
                    self.assertIn(visible, user_arch)
                    self.assertNotIn(hidden, user_arch)
                admin_arch = self.env[model_name].with_user(admin).get_view(
                    view_id=view.id,
                    view_type="form",
                )["arch"]
                self.assertIn("action_mark_received", admin_arch)
                self.assertIn("action_mark_verified", admin_arch)

    def test_validation_is_atomic_when_a_post_validation_effect_fails(self):
        for index, acte_type in enumerate(ACT_TYPES, 1):
            with self.subTest(acte_type=acte_type):
                acte = self._create_act(acte_type, f"atomic-{index}")
                self._transmit(acte)
                acte.piece_ids.with_user(self.officer).write({"etat": "verifie"})

                if acte_type == "mariage":
                    mention_model_class = type(self.env["etat.civil.mention.marginale"])
                    failure_patch = patch.object(
                        mention_model_class,
                        "create",
                        side_effect=UserError("Échec simulé de création de mention."),
                    )
                elif acte_type == "deces":
                    person_model_class = type(acte.defunt_id)
                    failure_patch = patch.object(
                        person_model_class,
                        "write",
                        side_effect=UserError("Échec simulé de mise à jour de statut vital."),
                    )
                else:
                    act_model_class = type(acte)
                    failure_patch = patch.object(
                        act_model_class,
                        "message_post",
                        side_effect=UserError("Échec simulé de journalisation."),
                    )

                with failure_patch, self.assertRaises(UserError):
                    acte.with_user(self.officer).action_valider_acte()

                self.assertEqual(acte.statut, "en_attente")
                self.assertFalse(acte.hash_empreinte_num)
                if acte_type == "mariage":
                    self.assertFalse(acte.notification_mention_ids)
                    self.assertNotEqual(acte.conjoint_1_id.situation_matrimoniale, "marie")
                elif acte_type == "deces":
                    self.assertNotEqual(acte.defunt_id.statut_vital, "decede")

    def test_transmission_is_atomic_when_activity_creation_fails(self):
        acte = self._create_act("naissance", "transmission-atomic")
        acte.piece_ids.with_user(self.agent).write({"etat": "recu"})
        with patch.object(
            type(acte),
            "activity_schedule",
            side_effect=UserError("Échec simulé de création d'activité."),
        ), self.assertRaises(UserError):
            acte.with_user(self.agent).action_envoyer_validation(officier=self.officer)

        self.assertEqual(acte.statut, "brouillon")
        self.assertFalse(acte.officier_validateur_id)
        self.assertFalse(acte.agent_transmetteur_id)
        self.assertFalse(acte.date_transmission)

    def test_second_marriage_for_a_spouse_is_rechecked_before_validation(self):
        first = self._create_act("mariage", "marriage-lock-first")
        second = self._create_act("mariage", "marriage-lock-second")
        second.with_user(self.agent).write({
            "conjoint_1_id": first.conjoint_1_id.id,
        })
        for acte in (first, second):
            self._transmit(acte)
            acte.piece_ids.with_user(self.officer).write({"etat": "verifie"})

        first.with_user(self.officer).action_valider_acte()
        with self.assertRaises(ValidationError):
            second.with_user(self.officer).action_valider_acte()

        self.assertEqual(second.statut, "en_attente")
        self.assertFalse(second.hash_empreinte_num)


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
        cls.other_centre = cls.env["etat.civil.centre"].sudo().create({
            "code_centre": "WF-API-OTHER",
            "nom_centre": "Autre centre workflow API",
            "commune": "Autre commune",
        })
        cls.outsider = cls.env["res.users"].sudo().create({
            "name": "Agent Outside Workflow API",
            "login": "agent-outside-workflow-api",
            "email": "agent-outside-workflow-api@example.test",
            "password": cls.password,
            "groups_id": [(6, 0, [cls.env.ref("etat_civil.group_etat_civil_agent").id])],
            "etat_civil_centre_ids": [(6, 0, [cls.other_centre.id])],
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
                self.assertEqual(
                    draft_response.status_code,
                    409,
                    draft_response.text,
                )
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

    def test_api_allows_agent_correction_and_rejects_direct_civil_status_changes(self):
        acte = self._create_act("naissance", "api-correction")
        self._transmit(acte)
        acte.with_user(self.officer).action_retourner_correction(
            "Compléter les informations du dossier."
        )

        self.authenticate(self.agent.login, self.password)
        correction_response = self.url_open(
            f"/api/v1/actes/naissance/{acte.id}",
            data=json.dumps({"texte_integral_acte": "Texte corrigé."}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(
            correction_response.status_code,
            200,
            correction_response.text,
        )
        self.assertEqual(
            acte.texte_integral_acte,
            "Texte corrigé.",
            correction_response.text,
        )

        person = acte.enfant_id
        status_response = self.url_open(
            f"/api/v1/personnes/{person.id}",
            data=json.dumps({"statut_vital": "decede"}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(status_response.status_code, 400, status_response.text)
        self.assertEqual(person.statut_vital, "vivant")

    def test_api_logout_requires_json_post(self):
        self.authenticate(self.agent.login, self.password)
        get_response = self.url_open("/api/v1/auth/logout")
        self.assertEqual(get_response.status_code, 405)

        form_response = self.url_open(
            "/api/v1/auth/logout",
            data="logout=1",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(form_response.status_code, 415)

        json_response = self.url_open(
            "/api/v1/auth/logout",
            data=json.dumps({}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(json_response.status_code, 200, json_response.text)

    def test_api_health_does_not_disclose_the_database_name(self):
        response = self.url_open("/api/v1/health")
        self.assertEqual(response.status_code, 200, response.text)
        payload = json.loads(response.content)
        self.assertEqual(payload["status"], "ok")
        self.assertNotIn("database", payload)

    def test_api_mutations_reject_json_sent_as_plain_text(self):
        self.authenticate(self.agent.login, self.password)
        name = "CSRF Content-Type Rejection"
        payload = {
            "nom": name,
            "prenoms": "Test",
            "sexe": "M",
            "date_naissance": "2000-01-01",
        }

        response = self.url_open(
            "/api/v1/personnes",
            data=json.dumps(payload),
            headers={"Content-Type": "text/plain"},
        )

        self.assertEqual(response.status_code, 415, response.text)
        self.assertFalse(
            self.env["etat.civil.individu"].sudo().search_count([("nom", "=", name)])
        )

        acte = self._create_act("naissance", "content-type")
        self._transmit(acte)
        self.authenticate(self.officer.login, self.password)
        response = self.url_open(
            f"/api/v1/actes/naissance/{acte.id}/valider",
            data="{}",
            headers={"Content-Type": "text/plain"},
        )
        self.assertEqual(response.status_code, 415, response.text)
        self.assertEqual(acte.statut, "en_attente")

        for path in (
            "/api/v1/actes/mariage/999999999/valider",
            "/api/v1/actes/deces/999999999/valider",
            "/api/v1/actes/invalide/999999999/valider",
            "/api/v1/mentions/999999999/valider",
        ):
            with self.subTest(path=path):
                response = self.url_open(
                    path,
                    data="{}",
                    headers={"Content-Type": "text/plain"},
                )
                self.assertEqual(response.status_code, 415, response.text)

    def test_api_rejects_invalid_piece_images_without_partial_updates(self):
        self.authenticate(self.agent.login, self.password)
        acte = self._create_act("naissance", "invalid-piece-image")
        piece = acte.piece_ids[0]

        image_buffer = io.BytesIO()
        Image.new("RGB", (1, 1)).save(image_buffer, format="PNG")
        valid_png = base64.b64encode(image_buffer.getvalue()).decode("ascii")
        invalid_images = (
            (base64.b64encode(b"not an image").decode("ascii"), "image/jpeg"),
            (valid_png, "image/jpeg"),
        )

        for index, (image_data, mimetype) in enumerate(invalid_images):
            with self.subTest(index=index):
                response = self.url_open(
                    f"/api/v1/actes/naissance/{acte.id}",
                    data=json.dumps({
                        "texte_integral_acte": f"Ne doit pas être enregistré {index}.",
                        "pieces": [{
                            "code": piece.name,
                            "etat": "recu",
                            "image_base64": image_data,
                            "image_mimetype": mimetype,
                        }],
                    }),
                    headers={"Content-Type": "application/json"},
                )

                self.assertEqual(response.status_code, 400, response.text)
                acte.invalidate_recordset(["texte_integral_acte"])
                piece.invalidate_recordset(["etat", "attachment_ids"])
                self.assertNotEqual(
                    acte.texte_integral_acte,
                    f"Ne doit pas être enregistré {index}.",
                )
                self.assertEqual(piece.etat, "a_fournir")
                self.assertFalse(piece.attachment_ids)

        child_name = "Rejected Image Child"
        mother_name = "Rejected Image Mother"
        response = self.url_open(
            "/api/v1/actes/naissance",
            data=json.dumps({
                "registre_id": self.registers["naissance"].id,
                "enfant_nom": child_name,
                "mere_nom": mother_name,
                "date_naissance": "2026-01-01",
                "texte_integral_acte": "Acte rejeté à cause du fichier image.",
                "pieces": [{
                    "code": piece.name,
                    "etat": "recu",
                    "image_base64": base64.b64encode(b"not an image").decode("ascii"),
                    "image_mimetype": "image/jpeg",
                }],
            }),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertFalse(
            self.env["etat.civil.individu"].sudo().search_count([
                ("nom", "=", child_name),
            ])
        )
        self.assertFalse(
            self.env["etat.civil.individu"].sudo().search_count([
                ("nom", "=", mother_name),
            ])
        )
        self.assertFalse(
            self.env["etat.civil.acte.naissance"].sudo().search_count([
                ("enfant_id.nom", "=", child_name),
            ])
        )

    def test_api_accepts_valid_piece_images_and_infers_mimetype(self):
        self.authenticate(self.agent.login, self.password)
        acte = self._create_act("naissance", "valid-piece-image")
        piece = acte.piece_ids[0]

        image_buffer = io.BytesIO()
        Image.new("RGB", (1, 1)).save(image_buffer, format="PNG")
        image_data = base64.b64encode(image_buffer.getvalue()).decode("ascii")
        response = self.url_open(
            f"/api/v1/actes/naissance/{acte.id}",
            data=json.dumps({
                "pieces": [{
                    "code": piece.name,
                    "etat": "recu",
                    "image_base64": image_data,
                }],
            }),
            headers={"Content-Type": "application/json"},
        )

        self.assertEqual(response.status_code, 200, response.text)
        piece.invalidate_recordset(["etat", "attachment_ids"])
        self.assertEqual(piece.etat, "recu")
        self.assertEqual(len(piece.attachment_ids), 1)
        self.assertEqual(piece.attachment_ids.mimetype, "image/png")

    def test_attachment_preview_route_respects_civil_centre_access(self):
        acte = self._create_act("naissance", "private-attachment")
        piece = acte.piece_ids[0]
        image_buffer = io.BytesIO()
        Image.new("RGB", (1, 1)).save(image_buffer, format="PNG")
        attachment = self.env["ir.attachment"].sudo().create({
            "name": "cin_parent.png",
            "datas": base64.b64encode(image_buffer.getvalue()),
            "res_model": "etat.civil.piece.justificative",
            "res_id": piece.id,
            "public": False,
        })
        piece.sudo().write({"attachment_ids": [(4, attachment.id)]})

        self.authenticate(self.agent.login, self.password)
        allowed = self.url_open(f"/web/content/{attachment.id}?download=false")
        self.assertEqual(allowed.status_code, 200, allowed.text)
        self.assertIn("image/png", allowed.headers.get("Content-Type", ""))
        self.assertNotIn(
            "attachment",
            allowed.headers.get("Content-Disposition", "").lower(),
        )

        self.authenticate(self.outsider.login, self.password)
        denied = self.url_open(f"/web/content/{attachment.id}?download=false")
        self.assertIn(denied.status_code, (403, 404), denied.text)

    def test_authenticated_api_routes_reject_anonymous_writes(self):
        self.authenticate(self.agent.login, self.password)
        logout_response = self.url_open(
            "/api/v1/auth/logout",
            data=json.dumps({}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(logout_response.status_code, 200, logout_response.text)

        name = "Anonymous API Write Rejection"
        response = self.url_open(
            "/api/v1/personnes",
            data=json.dumps({
                "nom": name,
                "prenoms": "Test",
                "sexe": "M",
                "date_naissance": "2000-01-01",
            }),
            headers={"Content-Type": "application/json"},
            allow_redirects=False,
        )

        self.assertIn(response.status_code, (301, 302, 303, 307, 308))
        self.assertIn("/web/login", response.headers.get("Location", ""))
        self.assertFalse(
            self.env["etat.civil.individu"].sudo().search_count([("nom", "=", name)])
        )

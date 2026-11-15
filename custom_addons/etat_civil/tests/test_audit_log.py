import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from odoo.addons.base.models.res_users import Users as BaseUsers
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEtatCivilAuditLog(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.agent = cls.env["res.users"].sudo().create({
            "name": "Agent audit test",
            "login": "agent-audit-test",
            "groups_id": [(6, 0, [
                cls.env.ref("etat_civil.group_etat_civil_agent").id,
            ])],
            "tz": "Indian/Antananarivo",
        })
        cls.admin = cls.env["res.users"].sudo().create({
            "name": "Administrateur audit test",
            "login": "admin-audit-test",
            "groups_id": [(6, 0, [
                cls.env.ref("etat_civil.group_etat_civil_admin").id,
            ])],
        })

    def test_create_update_delete_are_logged_without_personal_values(self):
        person = self.env["etat.civil.individu"].with_user(self.agent).create({
            "nom": "Nom confidentiel audit",
            "prenoms": "Prénom confidentiel audit",
            "sexe": "F",
            "date_naissance": "1990-01-01",
        })
        audit_model = self.env["etat.civil.audit.log"]
        create_event = audit_model.with_user(self.admin).search([
            ("action_type", "=", "create"),
            ("record_model", "=", person._name),
            ("record_id", "=", person.id),
        ], order="id desc", limit=1)
        self.assertTrue(create_event)
        self.assertEqual(create_event.user_id, self.agent)
        self.assertEqual(create_event.role, "Agent d'état civil")
        self.assertEqual(create_event.event_timezone, "Indian/Antananarivo")
        self.assertNotIn("Nom confidentiel audit", str(create_event.read()[0]))

        person.with_user(self.agent).write({"nom": "Nom mis à jour"})
        update_event = audit_model.with_user(self.admin).search([
            ("action_type", "=", "update"),
            ("record_model", "=", person._name),
            ("record_id", "=", person.id),
            ("user_id", "=", self.agent.id),
        ], order="id desc", limit=1)
        self.assertEqual(json.loads(update_event.changed_fields), ["nom"])
        self.assertFalse(update_event.old_values)
        self.assertFalse(update_event.new_values)
        self.assertNotIn("Nom mis à jour", str(update_event.read()[0]))

        person.with_user(self.admin).unlink()
        delete_event = audit_model.with_user(self.admin).search([
            ("action_type", "=", "delete"),
            ("record_model", "=", "etat.civil.individu"),
            ("record_id", "=", person.id),
        ], order="id desc", limit=1)
        self.assertTrue(delete_event)

    def test_audit_entries_are_read_only_and_admin_only(self):
        event = self.env["etat.civil.audit.log"]._record_event("other")
        self.assertTrue(event.event_uuid)
        with self.assertRaises(AccessError):
            event.with_user(self.admin).write({"result": "failed"})
        with self.assertRaises(AccessError):
            event.sudo().unlink()
        with self.assertRaises(AccessError):
            self.env["etat.civil.audit.log"].with_user(self.admin).create({
                "event_uuid": "forged",
                "event_datetime_local": "2026-01-01 00:00:00",
                "event_timezone": "UTC",
                "action_type": "other",
            })
        with self.assertRaises(AccessError):
            self.env["etat.civil.audit.log"].with_user(self.agent).search([])

    def test_login_succeeds_when_audit_write_fails(self):
        audit_model = type(self.env["etat.civil.audit.log"])

        with (
            patch.object(BaseUsers, "_login", return_value=self.agent.id),
            patch.object(
                audit_model,
                "_record_event",
                side_effect=RuntimeError("simulated audit storage failure"),
            ),
            self.assertLogs(
                "odoo.addons.etat_civil.models.res_users", level="ERROR"
            ) as captured,
        ):
            user_id = self.env["res.users"]._login(
                self.env.cr.dbname,
                self.agent.login,
                "already-verified",
                {},
            )

        self.assertEqual(user_id, self.agent.id)
        self.assertIn(
            "Failed to record successful civil-registry login audit event",
            captured.output[0],
        )

    def test_events_capture_commune_and_only_whitelisted_transition_values(self):
        centre = self.env["etat.civil.centre"].sudo().create({
            "code_centre": "AUDIT-COMMUNE",
            "nom_centre": "Centre de test audit",
            "commune": "Commune audit",
        })
        event = self.env["etat.civil.audit.log"].with_user(self.agent)._record_event(
            "validate",
            record=centre,
            old_values={"statut": "en_attente", "nom": "Donnée privée"},
            new_values={"statut": "valide", "cin": "123456789012"},
        )
        self.assertEqual(event.centre_id, centre)
        self.assertEqual(event.commune, "Commune audit")
        self.assertEqual(json.loads(event.old_values), {"statut": "en_attente"})
        self.assertEqual(json.loads(event.new_values), {"statut": "valide"})

    def test_role_changes_are_logged_without_group_payloads(self):
        officer_group = self.env.ref("etat_civil.group_etat_civil_officier")
        self.agent.sudo().write({"groups_id": [(6, 0, [officer_group.id])]})
        event = self.env["etat.civil.audit.log"].with_user(self.admin).search([
            ("action_type", "=", "update"),
            ("record_model", "=", "res.users"),
            ("record_id", "=", self.agent.id),
            ("changed_fields", "ilike", "groups_id"),
        ], order="id desc", limit=1)
        self.assertTrue(event)
        self.assertEqual(json.loads(event.old_values), {
            "role": "Agent d'état civil",
        })
        self.assertEqual(json.loads(event.new_values), {
            "role": "Officier d'état civil",
        })

    def test_explicit_piece_download_is_audited_but_preview_is_not(self):
        from ..controllers import binary as binary_controller
        from odoo.addons.web.controllers.binary import Binary
        from odoo.http import Response

        attachment = SimpleNamespace(
            _name="ir.attachment",
            res_model="etat.civil.piece.justificative",
            res_id=42,
        )
        piece = object()
        binary_model = MagicMock()
        binary_model._find_record.return_value = attachment
        piece_model = MagicMock()
        piece_model.sudo.return_value.browse.return_value.exists.return_value = piece
        audit_model = MagicMock()
        writable_env = MagicMock()
        writable_env.__getitem__.side_effect = lambda model: {
            "etat.civil.piece.justificative": piece_model,
            "etat.civil.audit.log": audit_model,
        }[model]
        cursor = MagicMock()
        cursor_manager = MagicMock()
        cursor_manager.__enter__.return_value = cursor
        request_env = MagicMock()
        request_env.uid = self.agent.id
        request_env.registry.cursor.return_value = cursor_manager
        request_env.__getitem__.side_effect = lambda model: {
            "ir.binary": binary_model,
        }[model]
        fake_request = SimpleNamespace(env=request_env)
        controller = binary_controller.EtatCivilAuditBinaryController()
        response = Response("pdf", content_type="application/pdf")

        with (
            patch.object(Binary, "content_common", return_value=response),
            patch.object(binary_controller, "request", fake_request),
            patch.object(binary_controller.api, "Environment", return_value=writable_env),
        ):
            result = controller.content_common(id=42, download="true")
            self.assertIs(result, response)
            audit_model._record_event.assert_called_once_with(
                "download",
                record=piece,
                record_model=None,
                record_id=None,
                user_id=self.agent.id,
            )
            cursor.commit.assert_called_once()

            audit_model.reset_mock()
            controller.content_common(id=42, download=False)
            audit_model._record_event.assert_not_called()
            cursor.commit.assert_called_once()

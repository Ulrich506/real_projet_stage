import base64
import csv
import io
from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEtatCivilImportExportAdmin(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        admin_group = cls.env.ref("etat_civil.group_etat_civil_admin")
        cls.admin = cls.env["res.users"].create({
            "name": "Import Export Admin",
            "login": "import-export-admin",
            "groups_id": [(6, 0, [admin_group.id])],
        })
        cls.Individu = cls.env["etat.civil.individu"].with_user(cls.admin)
        cls.ImportWizard = cls.env["etat.civil.import.wizard"].with_user(cls.admin)
        cls.ExportWizard = cls.env["etat.civil.export.wizard"].with_user(cls.admin)

    def _create_person(self, name, birthday, sex="F", vital="vivant", marital="celibataire"):
        person = self.Individu.create({
            "nom": name,
            "sexe": sex,
            "date_naissance": birthday,
        })
        status = {}
        if vital != "vivant":
            status["statut_vital"] = vital
        if marital != "celibataire":
            status["situation_matrimoniale"] = marital
        if status:
            person._write_civil_status(status)
        return person

    def test_export_filters_keep_vital_and_marital_status_separate(self):
        today = fields.Date.context_today(self.env.user)
        birthday = today - timedelta(days=365 * 30)
        target = self._create_person(
            "Filtre cible", birthday, sex="F", vital="decede", marital="celibataire"
        )
        self._create_person(
            "Autre situation", birthday, sex="F", vital="vivant", marital="marie"
        )

        wizard = self.ExportWizard.create({
            "export_filter": "decede",
            "marital_filter": "celibataire",
            "sex_filter": "F",
            "filter_age_min": True,
            "age_min": 20,
            "filter_age_max": True,
            "age_max": 40,
            "selection_mode": "selected",
            "selected_individu_ids": [(6, 0, [
                target.id,
                self.Individu.search([("nom", "=", "Autre situation")], limit=1).id,
            ])],
        })

        self.assertEqual(wizard._get_records(), target)

    def test_import_preview_blocks_writes_until_invalid_lines_are_fixed(self):
        csv_content = (
            "nom,prenoms,sexe,date_naissance,cin\n"
            "Import test,Personne,X,1994-04-04,\n"
        )
        wizard = self.ImportWizard.create({
            "file_data": base64.b64encode(csv_content.encode("utf-8")),
            "file_name": "citoyens.csv",
        })
        wizard.action_detect_columns()
        wizard.action_preview()
        line = wizard.line_ids

        self.assertEqual(wizard.result_errors, 1)
        self.assertTrue(line.error_message)
        wizard.action_import()
        self.assertEqual(wizard.state, "preview")
        self.assertFalse(self.Individu.search([("nom", "=", "Import test")]))

        line.write({"sexe": "F"})
        wizard.action_validate_preview()
        self.assertEqual(wizard.result_errors, 0)
        wizard.action_import()

        self.assertEqual(wizard.result_imported, 1)
        self.assertEqual(
            self.Individu.search([("nom", "=", "Import test")]).sexe, "F"
        )
        import_log = self.env["etat.civil.exchange.log"].sudo().search([
            ("operation", "=", "import"),
            ("file_name", "=", "citoyens.csv"),
            ("user_id", "=", self.admin.id),
        ], order="id desc", limit=1)
        self.assertTrue(import_log)
        import_audit_event = self.env["etat.civil.audit.log"].sudo().search([
            ("action_type", "=", "import"),
            ("record_model", "=", "etat.civil.exchange.log"),
            ("record_id", "=", import_log.id),
            ("user_id", "=", self.admin.id),
        ], limit=1)
        self.assertTrue(import_audit_event)

    def test_downloadable_import_template_uses_supported_csv_columns(self):
        wizard = self.ImportWizard.create({})
        action = wizard.action_download_template()
        content = base64.b64decode(wizard.template_file).decode("utf-8-sig")
        headers = next(csv.reader(io.StringIO(content)))

        self.assertEqual(wizard.template_file_name, "modele_import_citoyens.csv")
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertIn("Nom", headers)
        self.assertIn("Date de naissance", headers)
        self.assertIn("Situation matrimoniale", headers)

    def test_export_formats_are_generated_and_logged(self):
        person = self._create_person("Exports", "1990-01-01")
        for export_format in ("xlsx", "csv", "ods", "json", "xml"):
            wizard = self.ExportWizard.create({
                "export_format": export_format,
                "language": "fr_FR",
                "selection_mode": "selected",
                "selected_individu_ids": [(6, 0, [person.id])],
            })
            wizard.action_export()

            self.assertTrue(wizard.result_file, export_format)
            self.assertTrue(wizard.result_file_name.endswith("." + export_format))
            log = self.env["etat.civil.exchange.log"].sudo().search([
                ("operation", "=", "export"),
                ("file_name", "=", wizard.result_file_name),
                ("user_id", "=", self.admin.id),
            ], order="id desc", limit=1)
            self.assertTrue(log, export_format)
            self.assertEqual(log.file_format, export_format)
            self.assertEqual(log.language, "fr_FR")
            self.assertIn("date_naissance", log.exported_fields)
            self.assertIn("selected_ids", log.criteria)
            audit_event = self.env["etat.civil.audit.log"].sudo().search([
                ("action_type", "=", "export"),
                ("record_model", "=", "etat.civil.exchange.log"),
                ("record_id", "=", log.id),
                ("user_id", "=", self.admin.id),
            ], limit=1)
            self.assertTrue(audit_event, export_format)
        for pdf_layout in ("table", "individual"):
            wizard = self.ExportWizard.create({
                "export_format": "pdf",
                "pdf_layout": pdf_layout,
                "language": "fr_FR",
                "selection_mode": "selected",
                "selected_individu_ids": [(6, 0, [person.id])],
            })
            wizard.action_export()
            self.assertTrue(wizard.result_file, pdf_layout)
            self.assertTrue(wizard.result_file_name.endswith(".pdf"))
            self.assertTrue(
                base64.b64decode(wizard.result_file).startswith(b"%PDF"),
                "The PDF option must return an actual PDF file.",
            )
            audit_event = self.env["etat.civil.audit.log"].sudo().search([
                ("action_type", "=", "export"),
                ("record_model", "=", "etat.civil.exchange.log"),
                ("user_id", "=", self.admin.id),
            ], order="id desc", limit=1)
            self.assertTrue(audit_event)

    def test_malagasy_translation_is_used_in_interface_and_export(self):
        language_model = self.env["res.lang"].with_context(active_test=False)
        malagasy = language_model.search([("code", "=", "mg_MG")], limit=1)
        if not malagasy:
            language_model._create_lang("mg_MG", lang_name="Malagasy")
        elif not malagasy.active:
            malagasy.active = True
        self.env.ref("base.module_etat_civil")._update_translations(
            ["mg_MG"], overwrite=True
        )

        fields_info = self.env["etat.civil.individu"].with_context(
            lang="mg_MG"
        ).fields_get(["nom", "sexe", "statut_vital"], ["string", "selection"])
        self.assertEqual(fields_info["nom"]["string"], "Anarana")
        self.assertEqual(fields_info["sexe"]["selection"][0][1], "Lahy")

        view_arch = self.env.ref(
            "etat_civil.view_etat_civil_export_wizard_form"
        ).with_context(lang="mg_MG").arch_db
        self.assertIn("Sivana momba ny mponina", view_arch)

        person = self._create_person("Malagasy", "1990-01-01")
        wizard = self.ExportWizard.create({
            "export_format": "csv",
            "language": "mg_MG",
            "selection_mode": "selected",
            "selected_individu_ids": [(6, 0, [person.id])],
        })
        wizard.action_export()
        csv_text = base64.b64decode(wizard.result_file).decode("utf-8-sig")

        self.assertIn("Anarana", csv_text)
        self.assertIn("Lahy", csv_text)

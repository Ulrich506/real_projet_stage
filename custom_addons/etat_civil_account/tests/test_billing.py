import os
from io import BytesIO
from pathlib import Path

from odoo.exceptions import AccessError, UserError
from odoo.tools.pdf import PdfReader
from odoo.addons.etat_civil.tests.test_acte_workflow import ActeWorkflowFixtures, ACT_TYPES
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEtatCivilCopyBilling(ActeWorkflowFixtures, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.centre = cls.env["etat.civil.centre"].sudo().create({
            "code_centre": "COPY-BILLING-TEST",
            "nom_centre": "Centre de test facturation des copies",
            "commune": "Commune de test",
        })
        cls.registers = {}
        for index, acte_type in enumerate(ACT_TYPES, 1):
            cls.registers[acte_type] = cls.env["etat.civil.registre"].sudo().create({
                "annee": 2026,
                "type_registre": acte_type,
                "numero_volume": 40 + index,
                "centre_id": cls.centre.id,
            })
        cls.agent = cls.env["res.users"].sudo().create({
            "name": "Agent facturation copies",
            "login": "agent-copy-billing-test",
            "email": "agent-copy-billing-test@example.test",
            "groups_id": [(6, 0, [cls.env.ref("etat_civil.group_etat_civil_agent").id])],
            "etat_civil_centre_ids": [(6, 0, [cls.centre.id])],
        })
        cls.officer = cls.env["res.users"].sudo().create({
            "name": "Officier facturation copies",
            "login": "officer-copy-billing-test",
            "email": "officer-copy-billing-test@example.test",
            "groups_id": [(6, 0, [cls.env.ref("etat_civil.group_etat_civil_officier").id])],
            "etat_civil_centre_ids": [(6, 0, [cls.centre.id])],
        })
        cls.regisseur = cls.env["res.users"].sudo().create({
            "name": "Régisseur facturation copies",
            "login": "regisseur-copy-billing-test",
            "email": "regisseur-copy-billing-test@example.test",
            "groups_id": [(6, 0, [cls.env.ref("etat_civil_account.group_etat_civil_regisseur").id])],
            "etat_civil_centre_ids": [(6, 0, [cls.centre.id])],
        })
        cls.partner = cls.env["res.partner"].create({"name": "Demandeur facturation test"})
        cls.mga = cls.env.ref("base.MGA")
        cls.mga.active = True
        cls.env["res.currency.rate"].create({
            "name": "2026-01-01",
            "rate": 0.0002,
            "currency_id": cls.mga.id,
            "company_id": cls.env.company.id,
        })
        cls.product = cls.env["product.product"].create({
            "name": "Service copie état civil test",
            "detailed_type": "service",
            "taxes_id": [(5, 0, 0)],
        })
        cls.income_account = cls.env["account.account"].search([
            ("company_id", "=", cls.env.company.id),
            ("account_type", "=", "income"),
            ("deprecated", "=", False),
        ], limit=1)
        if cls.income_account:
            cls.product.with_company(cls.env.company).property_account_income_id = cls.income_account
        cls.tariff = cls.env["etat.civil.copy.tariff"].create({
            "name": "Extrait de naissance — test",
            "document_type": "naissance",
            "copy_kind": "extrait",
            "product_id": cls.product.id,
            "price": 2000,
            "currency_id": cls.mga.id,
            "company_id": cls.env.company.id,
            "center_id": cls.centre.id,
        })
        cls.copy_tariffs = {"naissance": cls.tariff}
        for document_type in ("mariage", "deces"):
            cls.copy_tariffs[document_type] = cls.env[
                "etat.civil.copy.tariff"
            ].create({
                "name": f"Extrait de {document_type} — test",
                "document_type": document_type,
                "copy_kind": "extrait",
                "product_id": cls.product.id,
                "price": 2000,
                "currency_id": cls.mga.id,
                "company_id": cls.env.company.id,
                "center_id": cls.centre.id,
            })

    def _render_receipt_pdf(self, report, receipt, artifact_name=None):
        pdf, content_type = report.with_context(
            force_report_rendering=True
        )._render_qweb_pdf(report.id, [receipt.id])
        self.assertEqual(content_type, "pdf")
        self.assertTrue(pdf.startswith(b"%PDF"))
        output_dir = os.environ.get("ETAT_CIVIL_REPORT_OUTPUT_DIR")
        if output_dir and artifact_name:
            path = Path(output_dir) / artifact_name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(pdf)
        return pdf

    def _create_copy_request(self, act, quantity=1):
        document_type, act_field = {
            "etat.civil.acte.naissance": ("naissance", "acte_naissance_id"),
            "etat.civil.acte.mariage": ("mariage", "acte_mariage_id"),
            "etat.civil.acte.deces": ("deces", "acte_deces_id"),
        }[act._name]
        values = {
            "document_type": document_type,
            "center_id": self.centre.id,
            "partner_id": self.partner.id,
            "copy_kind": "extrait",
            "copy_quantity": quantity,
            act_field: act.id,
        }
        return self.env["etat.civil.copy.request"].with_user(self.agent).create(values)

    def _render_copy_pdf(self, request, artifact_name):
        report = self.env.ref("etat_civil_account.action_report_copy_document")
        pdf, content_type = report.with_user(self.agent).with_context(
            force_report_rendering=True
        )._render_qweb_pdf(report.id, [request.id])
        self.assertEqual(content_type, "pdf")
        self.assertTrue(pdf.startswith(b"%PDF"))
        output_dir = os.environ.get("ETAT_CIVIL_REPORT_OUTPUT_DIR")
        if output_dir:
            path = Path(output_dir) / artifact_name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(pdf)
        return pdf

    def _authorize_paid_copy_request(self, request):
        request = request.with_user(self.regisseur)
        request.action_create_invoice()
        invoice = request.account_move_id.sudo()
        invoice.action_post()
        cash_journal = self.env["account.journal"].search([
            ("company_id", "=", self.env.company.id),
            ("type", "=", "cash"),
        ], limit=1)
        payment_register = self.env["account.payment.register"].with_context(
            active_model="account.move",
            active_ids=invoice.ids,
        ).create({
            "journal_id": cash_journal.id,
            "payment_date": "2026-11-08",
        })
        payment_register._create_payments()
        request.invalidate_recordset()
        request.action_confirm_payment()
        request.invalidate_recordset()
        self.assertEqual(request.state, "authorized")

    def _validated_birth_act(self, suffix):
        act = self._create_act("naissance", suffix)
        self._transmit(act)
        self._verify_and_validate(act)
        return act

    def test_authorized_copy_report_identifies_request_without_claiming_delivery(self):
        act = self._validated_birth_act("copy-report")
        request = self._create_copy_request(act)
        request.action_submit()
        self.assertEqual(request.state, "authorized")

        report = self.env.ref("etat_civil_account.action_report_copy_document")
        html, _ = report.with_user(self.agent)._render_qweb_html(
            report.id, [request.id]
        )
        html = html.decode("utf-8") if isinstance(html, bytes) else html

        self.assertIn(request.name, html)
        self.assertIn("KOPIA VOALOHANY", html)
        self.assertIn("Demande", html)
        self.assertNotIn("Délivrée le", html)

    def test_delivered_first_copy_report_shows_its_number_and_delivery_date(self):
        act = self._validated_birth_act("delivered-copy-report")
        request = self._create_copy_request(act)
        request.action_submit()
        request.action_deliver()
        self.assertEqual(request.copy_number, 1)

        report = self.env.ref("etat_civil_account.action_report_copy_document")
        html, _ = report.with_user(self.agent)._render_qweb_html(
            report.id, [request.id]
        )
        html = html.decode("utf-8") if isinstance(html, bytes) else html

        self.assertIn("KOPIA VOALOHANY", html)
        self.assertIn("Délivrée le", html)

    def test_copy_reports_generate_pdf_for_each_act_type(self):
        act_fields = {
            "naissance": {},
            "mariage": {"date_mariage": "2020-02-02"},
            "deces": {},
        }
        for document_type in ("naissance", "mariage", "deces"):
            with self.subTest(document_type=document_type):
                act = self._create_act(document_type, f"copy-pdf-{document_type}")
                if act_fields[document_type]:
                    act.write(act_fields[document_type])
                self._transmit(act)
                self._verify_and_validate(act)

                request = self._create_copy_request(act)
                request.action_submit()
                if request.state == "waiting_payment":
                    self._authorize_paid_copy_request(request)
                self.assertEqual(request.state, "authorized")
                request.action_deliver()
                pdf = self._render_copy_pdf(
                    request, f"copie-{document_type}-demo.pdf"
                )
                self.assertEqual(
                    len(PdfReader(BytesIO(pdf)).pages),
                    1,
                    f"The {document_type} copy should fit on one A4 page.",
                )

    def test_birth_tariff_defaults_to_first_copy_free(self):
        self.assertTrue(self.tariff.first_copy_free)
        self.assertEqual(self.tariff.currency_id, self.mga)
        self.assertEqual(self.tariff.price, 2000)

    def test_first_copy_is_free_and_later_copy_is_charged(self):
        act = self._validated_birth_act("first-free")
        first = self._create_copy_request(act)
        first.action_submit()
        self.assertTrue(first.is_free)
        self.assertEqual(first.free_copy_quantity, 1)
        self.assertEqual(first.billable_quantity, 0)
        first.action_deliver()

        later = self._create_copy_request(act)
        later.action_submit()
        self.assertFalse(later.is_free)
        self.assertEqual(later.free_copy_quantity, 0)
        self.assertEqual(later.amount, 2000)

    def test_first_of_multiple_copies_is_free_and_remainder_billed(self):
        act = self._validated_birth_act("multiple-copy")
        request = self._create_copy_request(act, quantity=3)
        request.action_submit()

        self.assertFalse(request.is_free)
        self.assertEqual(request.free_copy_quantity, 1)
        self.assertEqual(request.billable_quantity, 2)
        self.assertEqual(request.amount, 4000)

    def test_invoice_is_created_in_mga_with_billable_quantity(self):
        act = self._validated_birth_act("mga-invoice")
        request = self._create_copy_request(act, quantity=3)
        request.action_submit()
        request.with_user(self.regisseur).action_create_invoice()

        request = request.with_user(self.regisseur)
        invoice = request.account_move_id
        self.assertTrue(invoice)
        self.assertEqual(invoice.currency_id, self.mga)
        self.assertEqual(invoice.partner_id, self.partner)
        self.assertEqual(invoice.invoice_line_ids.quantity, 2)
        self.assertEqual(invoice.amount_total, 4000)
        self.assertEqual(invoice.state, "draft")

    def test_payment_reconciliation_is_checked_in_invoice_currency(self):
        act = self._validated_birth_act("mga-payment")
        request = self._create_copy_request(act, quantity=2)
        request.action_submit()
        request.with_user(self.regisseur).action_create_invoice()
        invoice = request.account_move_id.sudo()
        invoice.action_post()

        cash_journal = self.env["account.journal"].search([
            ("company_id", "=", self.env.company.id),
            ("type", "=", "cash"),
        ], limit=1)
        payment_register = self.env["account.payment.register"].with_context(
            active_model="account.move",
            active_ids=invoice.ids,
        ).create({
            "journal_id": cash_journal.id,
            "payment_date": "2026-11-08",
        })
        payment_register._create_payments()

        self.assertTrue(request.sudo()._payment_is_satisfied())

    def test_regisseur_registers_partial_and_final_versments_with_quittances(self):
        act = self._validated_birth_act("partial-accounting-payment")
        request = self._create_copy_request(act, quantity=2)
        request.action_submit()
        request = request.with_user(self.regisseur)
        request.action_create_invoice()
        request.action_post_invoice()

        cash_journal = self.env["account.journal"].search([
            ("company_id", "=", self.env.company.id),
            ("type", "=", "cash"),
        ], limit=1)
        payment_method_line = cash_journal.inbound_payment_method_line_ids[:1]
        self.assertTrue(payment_method_line)

        for amount in (1000, 1000):
            wizard = self.env["etat.civil.copy.payment.wizard"].with_user(
                self.regisseur
            ).create({
                "request_id": request.id,
                "amount": amount,
                "journal_id": cash_journal.id,
                "payment_method_line_id": payment_method_line.id,
                "payment_date": "2026-11-08",
                "communication": request.name,
            })
            action = wizard.action_register_payment()
            self.assertEqual(action["type"], "ir.actions.report")
            request.invalidate_recordset()

        self.assertEqual(request.state, "authorized")
        self.assertEqual(len(request.payment_ids), 2)
        self.assertEqual(sum(request.payment_ids.mapped("amount")), 2000)
        self.assertEqual(len(request.payment_ids.mapped("account_payment_id")), 2)

        report = self.env.ref(
            "etat_civil_account.action_report_copy_payment_receipt"
        )
        self.assertEqual(report.paperformat_id.format, "custom")
        self.assertEqual(report.paperformat_id.page_width, 80)
        self.assertEqual(report.paperformat_id.page_height, 170)
        receipts = request.payment_ids.sorted("id")
        receipt_names = receipts.mapped("name")
        receipt_count = self.env["etat.civil.copy.payment"].search_count([])
        for number, receipt in enumerate(receipts, start=1):
            html, _ = report.with_user(self.regisseur)._render_qweb_html(
                report.id, [receipt.id]
            )
            html = html.decode("utf-8") if isinstance(html, bytes) else html
            self.assertIn(receipt.name, html)
            self.assertIn(self.partner.name, html)
            self.assertIn("Montant reçu", html)
            self.assertIn("Prix unitaire", html)
            self.assertIn("Copies facturables", html)
            normalized_html = html.replace("\u202f", " ").replace("\xa0", " ")
            self.assertIn("2 000,00 Ar", normalized_html)
            self.assertIn("1 000,00 Ar", normalized_html)
            self.assertIn("mille Ariary", html)
            self.assertNotIn("One Thousand", html)
            self.assertNotIn("Ar MGA", html)

            self._render_receipt_pdf(
                report.with_user(self.regisseur),
                receipt,
                f"quittance-demo-versement-{number}.pdf",
            )

        payment_audit_events = self.env["etat.civil.audit.log"].sudo().search([
            ("action_type", "=", "payment"),
            ("record_model", "=", request._name),
            ("record_id", "=", request.id),
        ])
        self.assertTrue(payment_audit_events)
        receipt_print_events = self.env["etat.civil.audit.log"].sudo().search([
            ("action_type", "=", "print"),
            ("record_model", "=", "etat.civil.copy.payment"),
            ("record_id", "in", receipts.ids),
        ])
        self.assertEqual(len(receipt_print_events), 2 * len(receipts))

        self.assertEqual(receipts.mapped("name"), receipt_names)
        self.assertEqual(
            self.env["etat.civil.copy.payment"].search_count([]),
            receipt_count,
            "La réimpression ne doit créer aucune nouvelle quittance.",
        )

        unauthorized = self.env["res.users"].sudo().create({
            "name": "Utilisateur sans rôle de quittance",
            "login": "no-copy-receipt-access",
            "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        with self.assertRaises(AccessError):
            report.with_user(unauthorized)._render_qweb_html(
                report.id, [receipts[0].id]
            )
        original_amount = receipts[0].amount
        self.env.cr.execute(
            "UPDATE etat_civil_copy_payment SET amount = amount + 1 WHERE id = %s",
            [receipts[0].id],
        )
        receipts[0].invalidate_recordset(["amount"])
        try:
            with self.assertRaises(UserError):
                report.with_user(self.regisseur)._render_qweb_html(
                    report.id, [receipts[0].id]
                )
        finally:
            self.env.cr.execute(
                "UPDATE etat_civil_copy_payment SET amount = %s WHERE id = %s",
                [original_amount, receipts[0].id],
            )
            receipts[0].invalidate_recordset(["amount"])

    def test_birth_only_default_gratuity_does_not_apply_to_other_act_types(self):
        marriage_tariff = self.env["etat.civil.copy.tariff"].create({
            "name": "Copie de mariage — test",
            "document_type": "mariage",
            "copy_kind": "extrait",
            "product_id": self.product.id,
            "price": 2000,
            "currency_id": self.mga.id,
            "company_id": self.env.company.id,
            "center_id": self.centre.id,
        })
        self.assertFalse(marriage_tariff.first_copy_free)

import io

from odoo.addons.point_of_sale.tests.common import TestPoSCommon
from odoo.addons.etat_civil.tests.test_acte_workflow import ACT_TYPES, ActeWorkflowFixtures
from odoo.exceptions import AccessError, UserError
from odoo.tools import config
from odoo.tools.pdf import OdooPdfFileReader
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestEtatCivilPosBillingFlow(ActeWorkflowFixtures, TestPoSCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.centre = cls.env["etat.civil.centre"].sudo().create({
            "code_centre": "POS-COPY-TEST",
            "nom_centre": "Centre de test encaissement POS",
            "commune": "Commune de test",
        })
        cls.registers = {}
        for index, acte_type in enumerate(ACT_TYPES, 1):
            cls.registers[acte_type] = cls.env["etat.civil.registre"].sudo().create({
                "annee": 2026,
                "type_registre": acte_type,
                "numero_volume": 70 + index,
                "centre_id": cls.centre.id,
            })
        cls.agent = cls.env["res.users"].sudo().create({
            "name": "Agent POS copy test",
            "login": "agent-pos-copy-flow-test",
            "email": "agent-pos-copy-flow-test@example.test",
            "groups_id": [(6, 0, [cls.env.ref("etat_civil.group_etat_civil_agent").id])],
            "etat_civil_centre_ids": [(6, 0, [cls.centre.id])],
        })
        cls.officer = cls.env["res.users"].sudo().create({
            "name": "Officier POS copy test",
            "login": "officer-pos-copy-flow-test",
            "email": "officer-pos-copy-flow-test@example.test",
            "groups_id": [(6, 0, [cls.env.ref("etat_civil.group_etat_civil_officier").id])],
            "etat_civil_centre_ids": [(6, 0, [cls.centre.id])],
        })
        cls.regisseur = cls.env["res.users"].sudo().create({
            "name": "Régisseur POS copy test",
            "login": "regisseur-pos-copy-flow-test",
            "email": "regisseur-pos-copy-flow-test@example.test",
            "groups_id": [(
                6, 0, [cls.env.ref("etat_civil_account.group_etat_civil_regisseur").id]
            )],
            "etat_civil_centre_ids": [(6, 0, [cls.centre.id])],
        })
        cls.partner = cls.env["res.partner"].create({
            "name": "Demandeur POS copy test",
        })
        cls.company = cls.company_data["company"]
        cls.currency = cls.company.currency_id
        cls.restricted_category = cls.env["pos.category"].create({
            "name": "Catégorie POS sans produit de paiement",
        })
        cls.basic_config.write({
            "limit_categories": True,
            "iface_available_categ_ids": [(6, 0, [cls.restricted_category.id])],
        })
        cls.product = cls.env["product.product"].create({
            "name": "Service copie POS test",
            "detailed_type": "service",
            "taxes_id": [(5, 0, 0)],
        })
        cls.income_account = cls.env["account.account"].search([
            ("company_id", "=", cls.company.id),
            ("account_type", "=", "income"),
            ("deprecated", "=", False),
        ], limit=1)
        if cls.income_account:
            cls.product.with_company(cls.company).property_account_income_id = (
                cls.income_account
            )
        cls.env["etat.civil.copy.tariff"].sudo().create({
            "name": "Extrait POS test",
            "document_type": "naissance",
            "copy_kind": "extrait",
            "product_id": cls.product.id,
            "price": 10,
            "currency_id": cls.currency.id,
            "company_id": cls.company.id,
            "center_id": cls.centre.id,
        })

    def setUp(self):
        super().setUp()
        self.config = self.basic_config
        self.open_new_session()
        self.regisseur.sudo().write({
            "company_id": self.pos_session.company_id.id,
            "company_ids": [(6, 0, [self.pos_session.company_id.id])],
        })

    def _create_waiting_request(self):
        acte = self._create_act("naissance", "pos-payment")
        self._transmit(acte)
        self._verify_and_validate(acte)
        request = self.env["etat.civil.copy.request"].with_user(self.agent).create({
            "document_type": "naissance",
            "acte_naissance_id": acte.id,
            "center_id": self.centre.id,
            "partner_id": self.partner.id,
            "copy_kind": "extrait",
            "copy_quantity": 2,
        })
        request.action_submit()
        request = request.with_user(self.regisseur)
        request.action_create_invoice()
        request.action_post_invoice()
        return request

    def _make_pos_payment(self, request, amount, uid):
        payment_product = self.env.ref(
            "etat_civil_pos.product_template_copy_payment"
        ).product_variant_id
        order_data = self.create_ui_order_data(
            [(payment_product, 1)],
            customer=self.partner,
            uid=uid,
        )
        data = order_data["data"]
        line = data["lines"][0][2]
        line.update({
            "price_unit": amount,
            "price_subtotal": amount,
            "price_subtotal_incl": amount,
            "discount": 0.0,
            "tax_ids": [(6, 0, [])],
        })
        data.update({
            "amount_paid": amount,
            "amount_total": amount,
            "amount_tax": 0,
            "etat_civil_copy_request_id": request.id,
            "user_id": self.regisseur.id,
        })
        data["statement_ids"][0][2]["amount"] = amount
        order_data["to_invoice"] = True
        order_id = self.env["pos.order"].with_user(self.regisseur).create_from_ui(
            [order_data]
        )[0]["id"]
        return self.env["pos.order"].sudo().browse(order_id)

    def test_payment_product_is_loaded_but_hidden_from_the_product_catalog(self):
        payment_product = self.env.ref(
            "etat_civil_pos.product_template_copy_payment"
        ).product_variant_id
        loaded_products = self.env["product.product"].search(
            self.config._get_available_product_domain()
        )
        self.assertIn(payment_product, loaded_products)
        self.assertIn(payment_product, self.config._get_special_products())

    def test_partial_and_final_pos_payments_reconcile_one_invoice(self):
        request = self._create_waiting_request()
        invoice = request.account_move_id
        self.assertEqual(invoice.currency_id, self.pos_session.currency_id)
        self.assertEqual(invoice.amount_residual, 10)
        self.assertEqual(self.pos_session.state, "opened")
        self.assertIn(
            self.pos_session.company_id.id,
            self.regisseur.company_ids.ids,
        )

        pending = self.env["etat.civil.copy.request"].with_user(
            self.regisseur
        ).pos_get_pending_copy_requests(self.pos_session.id)
        self.assertEqual([item["id"] for item in pending], [request.id])

        first_order = self._make_pos_payment(request, 4, "pos-copy-partial-01")
        request.invalidate_recordset()
        self.assertEqual(first_order.account_move, invoice)
        self.assertEqual(first_order.state, "invoiced")
        self.assertEqual(first_order.etat_civil_copy_payment_applied, True)
        self.assertEqual(request.state, "waiting_payment")
        self.assertEqual(invoice.amount_residual, 6)
        self.assertEqual(request.payment_ids.mapped("amount"), [4])
        self.assertEqual(
            self.env["account.move"].search_count([
                ("etat_civil_copy_request_ids", "=", request.id),
            ]),
            1,
        )
        with self.assertRaises(UserError):
            request.with_user(self.agent).action_deliver()

        second_order = self._make_pos_payment(request, 6, "pos-copy-partial-02")
        request.invalidate_recordset()
        self.assertEqual(second_order.account_move, invoice)
        self.assertEqual(invoice.amount_residual, 0)
        self.assertEqual(request.state, "authorized")
        self.assertEqual(sum(request.payment_ids.mapped("amount")), 10)
        self.assertEqual(len(request.pos_order_ids), 2)
        receipt_report = self.env.ref(
            "etat_civil_account.action_report_copy_payment_receipt"
        ).with_user(self.regisseur).with_context(force_report_rendering=True)
        receipt_pdf, _ = receipt_report._render_qweb_pdf(
            receipt_report.report_name, request.payment_ids.ids
        )
        self.assertTrue(receipt_pdf.startswith(b"%PDF-"))

    def test_paid_pos_invoice_pdf_embeds_facturx_attachment(self):
        request = self._create_waiting_request()
        order = self._make_pos_payment(request, 10, "pos-copy-invoice-pdf")
        invoice = request.account_move_id
        self.assertEqual(order.account_move, invoice)
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(
            self.env["account.move"].search_count([
                ("etat_civil_copy_request_ids", "=", request.id),
            ]),
            1,
        )

        pdf, content_type = self.env["ir.actions.report"].with_context(
            force_report_rendering=True
        ).with_company(invoice.company_id)._render_qweb_pdf(
            "account.account_invoices", invoice.ids
        )
        self.assertEqual(content_type, "pdf")
        self.assertTrue(pdf.startswith(b"%PDF-"))
        invoice_data = {
            "pdf_attachment_values": {"raw": pdf},
            "ubl_cii_xml_options": {"ubl_cii_format": "facturx"},
            "ubl_cii_xml_attachment_values": {"raw": b"<Invoice/>"},
        }

        previous_test_mode = config["test_enable"]
        config["test_enable"] = False
        try:
            self.env["account.move.send"]._hook_invoice_document_after_pdf_report_render(
                invoice, invoice_data
            )
        finally:
            config["test_enable"] = previous_test_mode

        rendered_pdf = invoice_data["pdf_attachment_values"]["raw"]
        self.assertTrue(rendered_pdf.startswith(b"%PDF-"))
        reader = OdooPdfFileReader(io.BytesIO(rendered_pdf), strict=False)
        self.assertEqual(
            dict(reader.getAttachments()).get("factur-x.xml"),
            b"<Invoice/>",
        )

    def test_pos_ticket_is_unpaid_and_idempotent(self):
        ticket_model = self.env["etat.civil.demande.guichet"].with_user(
            self.regisseur
        )
        values = {
            "center_id": self.centre.id,
            "requester_name": "Demandeur ticket POS",
            "phone": "0340000000",
            "person_name": "Personne concernée POS",
            "document_type": "naissance",
            "copy_kind": "extrait",
            "copy_quantity": 2,
            "act_reference": "",
            "request_uuid": "pos-ticket-idempotent-test",
        }

        created = ticket_model.pos_create_ticket(self.pos_session.id, values)
        retried = ticket_model.pos_create_ticket(self.pos_session.id, values)
        ticket = self.env["etat.civil.demande.guichet"].sudo().browse(created["id"])

        self.assertEqual(created, retried)
        self.assertEqual(ticket.statut, "en_attente")
        self.assertEqual(ticket.copy_request_ids, self.env["etat.civil.copy.request"])
        self.assertFalse(ticket.copy_request_ids.account_move_id)
        self.assertEqual(ticket.copy_quantity, 2)
        self.assertEqual(ticket.requester_partner_id.name, "Demandeur ticket POS")
        self.assertEqual(
            ticket.service_product_id,
            self.env.ref("etat_civil_pos.product_template_copy_birth_extract").product_variant_id,
        )
        self.assertEqual(
            self.env["res.partner"].sudo().search_count([
                ("name", "=", "Demandeur ticket POS"),
            ]),
            1,
        )
        self.assertEqual(
            self.env["etat.civil.demande.guichet"].with_user(self.agent).search_count([
                ("id", "=", ticket.id),
            ]),
            1,
        )
        self.assertEqual(
            self.env["etat.civil.demande.guichet"].with_user(self.officer).search_count([
                ("id", "=", ticket.id),
            ]),
            0,
        )
        report = self.env.ref("etat_civil_pos.action_report_guichet_ticket").with_user(
            self.regisseur
        ).with_context(force_report_rendering=True)
        pdf, _ = report._render_qweb_pdf(report.report_name, [ticket.id])
        self.assertTrue(pdf.startswith(b"%PDF-"))

    def test_regisseur_cannot_create_ticket_outside_the_pos_endpoint(self):
        with self.assertRaises(AccessError):
            self.env["etat.civil.demande.guichet"].with_user(
                self.regisseur
            ).create({})

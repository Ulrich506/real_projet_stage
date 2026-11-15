from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCopyRequestSecurity(TransactionCase):
    def test_typed_act_is_required(self):
        request = self.env["etat.civil.copy.request"].new({"document_type": "naissance"})
        with self.assertRaises(ValidationError):
            request._check_exactly_one_act()

    def test_direct_state_write_is_rejected(self):
        with self.assertRaises(AccessError):
            self.env["etat.civil.copy.request"].write({"state": "authorized"})

    def test_payment_confirmation_requires_regisseur(self):
        with self.assertRaises(AccessError):
            self.env["etat.civil.copy.request"].action_confirm_payment()

    def test_officer_cannot_access_copy_requests_or_payment_records(self):
        officer = self.env["res.users"].sudo().create({
            "name": "Officer without copy access",
            "login": "officer-copy-access-test",
            "groups_id": [(6, 0, [
                self.env.ref("etat_civil.group_etat_civil_officier").id,
            ])],
        })
        for model_name in (
            "etat.civil.copy.request",
            "etat.civil.copy.payment",
        ):
            with self.assertRaises(AccessError):
                self.env[model_name].with_user(officer).check_access_rights("read")

        for report_xmlid in (
            "etat_civil_account.action_report_copy_document",
            "etat_civil_account.action_report_copy_payment_receipt",
        ):
            report = self.env.ref(report_xmlid)
            self.assertFalse(officer.groups_id & report.groups_id)
            self.assertFalse(report.groups_id & self.env.ref(
                "etat_civil.group_etat_civil_officier"
            ))

    def test_missing_invoice_never_satisfies_payment_gate(self):
        request = self.env["etat.civil.copy.request"].new({})
        self.assertFalse(request._payment_is_satisfied())

    def test_negative_tariff_is_rejected(self):
        product = self.env["product.product"].create({
            "name": "Synthetic copy service",
            "detailed_type": "service",
        })
        with self.assertRaises(ValidationError):
            self.env["etat.civil.copy.tariff"].create({
                "name": "Synthetic invalid tariff",
                "document_type": "naissance",
                "copy_kind": "integrale",
                "product_id": product.id,
                "price": -1,
            })

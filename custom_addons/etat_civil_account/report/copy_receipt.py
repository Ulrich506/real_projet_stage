from odoo import _, api, models
from odoo.exceptions import AccessError, UserError
from odoo.tools.float_utils import float_compare
from babel.numbers import format_decimal

from odoo.addons.etat_civil.models.malagasy_date_utils import montant_to_malagasy_words


class ReportEtatCivilCopyPaymentReceipt(models.AbstractModel):
    _name = "report.etat_civil_account.copy_payment_receipt"
    _description = "Rapport de quittance de versement d'état civil"

    @api.model
    def _get_report_values(self, docids, data=None):
        docids = list(docids or [])
        allowed_groups = (
            "etat_civil.group_etat_civil_admin",
            "etat_civil_account.group_etat_civil_regisseur",
        )
        if not self.env.su and not any(
            self.env.user.has_group(group) for group in allowed_groups
        ):
            raise AccessError(_("Vous n'êtes pas autorisé à imprimer cette quittance."))

        payments = self.env["etat.civil.copy.payment"].browse(docids).exists()
        if len(payments) != len(docids):
            raise AccessError(_("Une quittance est introuvable ou inaccessible."))
        payments.check_access_rights("read")
        payments.check_access_rule("read")

        requests_by_receipt = {}
        receipt_display_by_id = {}
        for payment in payments:
            request = payment.request_id
            request.check_access_rights("read")
            request.check_access_rule("read")
            request._check_center_access()
            finance_request = request.sudo()
            invoice = finance_request.account_move_id
            if (
                not finance_request._invoice_matches_request(invoice)
                or invoice.state != "posted"
                or payment.company_id != request.company_id
                or payment.currency_id != request.currency_id
            ):
                raise UserError(_("La quittance ne correspond plus à une facture comptabilisée conforme."))

            amount, transaction_date = self._get_reconciled_receipt_amount(
                payment.sudo(), finance_request, invoice
            )
            if (
                float_compare(
                    amount,
                    payment.amount,
                    precision_rounding=payment.currency_id.rounding,
                )
                != 0
                or amount <= 0
                or transaction_date != payment.payment_date
            ):
                raise UserError(_("Le montant de cette quittance n'est plus justifié par son encaissement rapproché."))
            requests_by_receipt[payment.id] = finance_request
            receipt_display_by_id[payment.id] = {
                "payment_date": payment.payment_date.strftime("%d/%m/%Y"),
                "unit_price": self._format_receipt_amount(
                    request.unit_price, request.currency_id
                ),
                "request_total": self._format_receipt_amount(
                    request.amount, request.currency_id
                ),
                "paid_amount": self._format_receipt_amount(
                    payment.amount, payment.currency_id
                ),
                "amount_in_words": self._amount_in_words(
                    payment.currency_id, payment.amount
                ),
            }
            self.env["etat.civil.audit.log"]._record_event(
                "print",
                record=payment,
                details={
                    "amount": payment.amount,
                    "currency_id": payment.currency_id.id,
                },
            )

        settings = self.env["etat.civil.copy.receipt.settings"].sudo().search([
            ("company_id", "in", payments.mapped("company_id").ids),
        ])
        return {
            "doc_ids": payments.ids,
            "doc_model": "etat.civil.copy.payment",
            "docs": payments.sudo(),
            "request_by_receipt_id": requests_by_receipt,
            "receipt_display_by_id": receipt_display_by_id,
            "settings_by_company": {
                item.company_id.id: item for item in settings
            },
        }

    @api.model
    def _format_receipt_amount(self, amount, currency):
        pattern = "#,##0"
        if currency.decimal_places:
            pattern += "." + ("0" * currency.decimal_places)
        amount = currency.round(amount)
        return "{} {}".format(
            format_decimal(amount, format=pattern, locale="fr_FR"),
            currency.symbol or currency.name,
        )

    @api.model
    def _amount_in_words(self, currency, amount):
        rounded = currency.round(amount)
        return montant_to_malagasy_words(rounded)

    @api.model
    def _get_reconciled_receipt_amount(self, receipt, request, invoice):
        source_payment = receipt.account_payment_id
        source_move = receipt.pos_payment_move_id
        if bool(source_payment) == bool(source_move):
            raise UserError(_("La quittance doit référencer un seul encaissement."))

        if source_payment:
            payment = source_payment.sudo()
            if (
                payment.state != "posted"
                or payment.payment_type != "inbound"
                or payment.partner_type != "customer"
                or payment.partner_id != request.partner_id
                or payment.company_id != request.company_id
                or payment.move_id.state != "posted"
                or invoice not in payment.reconciled_invoice_ids
            ):
                raise UserError(_("Le paiement comptable lié à la quittance n'est pas valide."))
            transaction_date = payment.date
        else:
            payment_move = source_move.sudo()
            if (
                payment_move.state != "posted"
                or payment_move.company_id != request.company_id
                or payment_move.currency_id != request.currency_id
            ):
                raise UserError(_("L'encaissement POS lié à la quittance n'est pas valide."))
            transaction_date = payment_move.date

        receivable_lines = invoice.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        )
        partials = request.env["account.partial.reconcile"]
        for line in receivable_lines:
            partials |= line.matched_debit_ids | line.matched_credit_ids

        reconciled_amount = 0.0
        for partial in partials:
            if partial.debit_move_id.move_id == invoice:
                counterpart = partial.credit_move_id
                amount = partial.debit_amount_currency
                currency = partial.debit_currency_id
            elif partial.credit_move_id.move_id == invoice:
                counterpart = partial.debit_move_id
                amount = partial.credit_amount_currency
                currency = partial.credit_currency_id
            else:
                continue
            if currency != receipt.currency_id:
                continue

            if source_payment and counterpart.move_id.payment_id == source_payment:
                reconciled_amount += amount
            elif source_move and counterpart.move_id == source_move:
                source_kind, pos_payments = request._get_invoice_payment_source(
                    counterpart, invoice
                )
                if (
                    source_kind == "pos"
                    and request._is_valid_pos_payment_source(pos_payments, invoice)
                ):
                    reconciled_amount += amount

        return reconciled_amount, transaction_date

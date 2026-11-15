from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.float_utils import float_compare


class PosOrder(models.Model):
    _inherit = "pos.order"

    etat_civil_copy_request_id = fields.Many2one(
        "etat.civil.copy.request", string="Demande de copie",
        readonly=True, copy=False, index=True, ondelete="restrict",
    )
    etat_civil_copy_payment_applied = fields.Boolean(
        string="Paiement de copie rapproché", readonly=True, copy=False,
    )

    @api.model
    def _order_fields(self, ui_order):
        copy_request_id = ui_order.get("etat_civil_copy_request_id")
        if copy_request_id:
            user = self.env.user
            if not (
                user.has_group("etat_civil_account.group_etat_civil_regisseur")
                or user.has_group("etat_civil.group_etat_civil_admin")
            ):
                raise AccessError(_("Le paiement POS d'une copie est réservé au régisseur."))
            request = self.env["etat.civil.copy.request"].browse(copy_request_id).exists()
            if not request:
                raise ValidationError(_("La demande de copie indiquée n'existe pas."))
            request._check_center_access()
        values = super()._order_fields(ui_order)
        values["etat_civil_copy_request_id"] = copy_request_id or False
        return values

    def _validate_etat_civil_copy_payment(self):
        self.ensure_one()
        user = self.env.user
        if not (
            user.has_group("etat_civil_account.group_etat_civil_regisseur")
            or user.has_group("etat_civil.group_etat_civil_admin")
        ):
            raise AccessError(_("Le paiement POS d'une copie est réservé au régisseur."))

        copy_request = self.etat_civil_copy_request_id
        copy_request._check_center_access()
        invoice = copy_request.sudo().account_move_id
        if (
            copy_request.state != "waiting_payment"
            or not copy_request._invoice_matches_request(invoice)
            or invoice.state != "posted"
        ):
            raise UserError(_("La demande doit avoir une facture comptabilisée conforme."))
        if (
            self.session_id.state != "opened"
            or self.company_id != copy_request.company_id
            or self.partner_id != copy_request.partner_id
            or self.currency_id != invoice.currency_id
        ):
            raise ValidationError(_("La session, le demandeur, la société et la devise POS doivent correspondre à la facture."))
        if self.account_move and self.account_move != invoice:
            raise ValidationError(_("La commande POS possède déjà une autre facture."))
        if len(self.lines) != 1:
            raise ValidationError(_("Une commande POS liée à une copie doit contenir une seule ligne d'encaissement."))

        template = self.env.ref("etat_civil_pos.product_template_copy_payment")
        payment_product = self.env["product.product"].sudo().search(
            [("product_tmpl_id", "=", template.id)], limit=1
        )
        line = self.lines
        if (
            not payment_product
            or line.product_id != payment_product
            or float_compare(line.qty, 1, precision_digits=6) != 0
            or float_compare(line.discount, 0, precision_digits=6) != 0
            or line.tax_ids
            or not self.currency_id.is_zero(line.price_subtotal_incl - self.amount_total)
        ):
            raise ValidationError(_("La ligne POS doit être le produit technique de versement, sans remise ni taxe."))
        if not self.payment_ids or any(
            payment.payment_method_id.type == "pay_later"
            for payment in self.payment_ids
        ):
            raise ValidationError(_("Un paiement POS réel est requis; le paiement différé est interdit."))
        net_paid = sum(self.payment_ids.mapped("amount"))
        if (
            float_compare(net_paid, self.amount_total, precision_rounding=self.currency_id.rounding) != 0
            or float_compare(self.amount_total, invoice.amount_residual, precision_rounding=self.currency_id.rounding) > 0
            or self.currency_id.is_zero(self.amount_total)
        ):
            raise ValidationError(_("Le montant encaissé doit être positif et ne pas dépasser le solde de la facture."))
        return copy_request, invoice

    def _process_saved_order(self, draft):
        self.ensure_one()
        service_product_ids = self.env["product.product"]
        for xml_id in (
            "etat_civil_pos.product_template_copy_birth_full",
            "etat_civil_pos.product_template_copy_birth_extract",
            "etat_civil_pos.product_template_copy_marriage_full",
            "etat_civil_pos.product_template_copy_marriage_extract",
            "etat_civil_pos.product_template_copy_death_full",
            "etat_civil_pos.product_template_copy_death_extract",
        ):
            template = self.env.ref(xml_id, raise_if_not_found=False)
            if template:
                service_product_ids |= template.product_variant_id
        service_product_ids |= self.env["etat.civil.copy.tariff"].sudo().search([
            ("company_id", "=", self.company_id.id),
        ]).mapped("product_id")
        if not self.etat_civil_copy_request_id and self.lines.filtered(
            lambda line: line.product_id in service_product_ids
        ):
            raise UserError(_(
                "Les prestations d'état civil doivent être créées comme tickets de guichet; "
                "elles ne peuvent pas être encaissées avant l'identification de l'acte."
            ))
        if not self.etat_civil_copy_request_id or draft:
            return super()._process_saved_order(draft)
        if self.etat_civil_copy_payment_applied:
            return super()._process_saved_order(draft)

        copy_request, invoice = self._validate_etat_civil_copy_payment()
        self.sudo().write({
            "account_move": invoice.id,
            "to_invoice": True,
        })
        self.invalidate_recordset(["account_move", "to_invoice"])
        result = super()._process_saved_order(draft)
        self.invalidate_recordset()
        if self.state != "paid":
            raise UserError(_("La commande POS n'a pas terminé son encaissement."))

        payment_moves = self._apply_invoice_payments(
            self.session_id.state == "closed"
        )
        if not payment_moves or any(move.state != "posted" for move in payment_moves):
            raise UserError(_("Odoo n'a pas comptabilisé le paiement POS sur la facture de copie."))
        self.sudo().write({
            "state": "invoiced",
            "etat_civil_copy_payment_applied": True,
        })
        receipts = copy_request._sync_payment_receipts()
        if not receipts.sudo().filtered(
            lambda item: item.pos_payment_move_id in payment_moves
        ):
            raise UserError(_("Le paiement POS est rapproché mais aucune quittance n'a été créée."))
        copy_request.action_confirm_payment()
        return result


class EtatCivilCopyRequest(models.Model):
    _inherit = "etat.civil.copy.request"

    pos_order_ids = fields.One2many(
        "pos.order", "etat_civil_copy_request_id",
        string="Encaissements POS", readonly=True,
    )

    def _get_invoice_payment_source(self, counterpart_line, invoice):
        source_kind, source = super()._get_invoice_payment_source(
            counterpart_line, invoice
        )
        if source_kind:
            return source_kind, source
        pos_payments = counterpart_line.move_id.sudo().pos_payment_ids
        if pos_payments:
            return "pos", pos_payments
        return source_kind, source

    def _is_valid_pos_payment_source(self, pos_payments, invoice):
        self.ensure_one()
        pos_payments = pos_payments.sudo()
        orders = pos_payments.mapped("pos_order_id")
        if len(orders) != 1:
            return False
        order = orders
        return bool(
            order.etat_civil_copy_request_id == self
            and order.account_move == invoice
            and order.state == "invoiced"
            and order.etat_civil_copy_payment_applied
            and order.company_id == self.company_id
            and order.partner_id == self.partner_id
            and order.currency_id == invoice.currency_id
            and not any(
                payment.payment_method_id.type == "pay_later"
                for payment in pos_payments
            )
        )

    def _sync_payment_receipts(self):
        receipts = super()._sync_payment_receipts()
        for request in self:
            invoice = request.sudo().account_move_id
            if not request._invoice_matches_request(invoice):
                continue
            receivable_lines = invoice.line_ids.filtered(
                lambda line: line.account_id.account_type == "asset_receivable"
            )
            partials = request.sudo().env["account.partial.reconcile"]
            for line in receivable_lines:
                partials |= line.matched_debit_ids | line.matched_credit_ids
            amounts_by_move = {}
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
                payment_move = counterpart.move_id.sudo()
                if (
                    currency != invoice.currency_id
                    or not payment_move.pos_payment_ids
                    or not request._is_valid_pos_payment_source(
                        payment_move.pos_payment_ids, invoice
                    )
                ):
                    continue
                move, accumulated = amounts_by_move.get(
                    payment_move.id, (payment_move, 0.0)
                )
                amounts_by_move[payment_move.id] = (move, accumulated + amount)

            for payment_move, amount in amounts_by_move.values():
                if amount <= 0:
                    continue
                receipt = self.env["etat.civil.copy.payment"].sudo().search(
                    [("pos_payment_move_id", "=", payment_move.id)], limit=1
                )
                if receipt:
                    receipts |= receipt
                    continue
                pos_payments = payment_move.pos_payment_ids
                methods = sorted(set(
                    pos_payment.payment_method_id.display_name
                    for pos_payment in pos_payments
                    if not pos_payment.is_change and pos_payment.amount > 0
                ))
                receipt = self.env["etat.civil.copy.payment"].sudo().create({
                    "request_id": request.id,
                    "pos_payment_move_id": payment_move.id,
                    "amount": amount,
                    "currency_id": invoice.currency_id.id,
                    "company_id": request.company_id.id,
                    "payment_date": payment_move.date,
                    "payment_method": ", ".join(methods) or _("Point de vente"),
                    "received_by_id": self.env.uid,
                })
                receipts |= receipt
                request.sudo()._log_event(
                    "payment",
                    _("Versement POS reçu; quittance %s.", receipt.name),
                    invoice,
                    receipt,
                )
        return receipts

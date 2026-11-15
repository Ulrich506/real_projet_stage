from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError


class EtatCivilCopyRequest(models.Model):
    _inherit = "etat.civil.copy.request"

    def action_submit(self):
        for request in self:
            ticket = request.guichet_ticket_id
            if ticket and ticket.service_product_id:
                tariff = self.env["etat.civil.copy.tariff"]._for_request(
                    request.document_type,
                    request.copy_kind,
                    request.center_id,
                    fields.Date.today(),
                )
                if tariff.product_id != ticket.service_product_id:
                    raise UserError(_(
                        "Le tarif configuré ne correspond pas à la prestation du ticket POS."
                    ))
        return super().action_submit()

    @api.model
    def pos_get_pending_copy_requests(self, session_id):
        if not (
            self.env.user.has_group("etat_civil_account.group_etat_civil_regisseur")
            or self.env.user.has_group("etat_civil.group_etat_civil_admin")
        ):
            raise AccessError(_("Le point de vente est réservé au régisseur et à l'administrateur d'état civil."))
        session = self.env["pos.session"].browse(session_id).exists()
        if (
            not session
            or session.state != "opened"
            or session.company_id not in self.env.user.company_ids
        ):
            raise UserError(_("La session POS doit être ouverte dans une société autorisée."))
        currency = session.config_id.currency_id
        if not currency:
            raise UserError(_("Configurez une liste de prix et une devise sur le point de vente."))

        product_template = self.env.ref("etat_civil_pos.product_template_copy_payment")
        payment_product = self.env["product.product"].search(
            [("product_tmpl_id", "=", product_template.id)], limit=1
        )
        if not payment_product or not payment_product.available_in_pos:
            raise UserError(_("Le produit technique d'encaissement n'est pas disponible dans le point de vente."))

        requests = self.search(
            [
                ("state", "=", "waiting_payment"),
                ("account_move_id.state", "=", "posted"),
                ("company_id", "=", session.company_id.id),
            ],
            order="request_date, id",
        )
        result = []
        for copy_request in requests:
            copy_request._check_center_access()
            invoice = copy_request.sudo().account_move_id
            if (
                invoice.currency_id != currency
                or currency.is_zero(invoice.amount_residual)
                or invoice.amount_residual < 0
            ):
                continue
            result.append({
                "id": copy_request.id,
                "name": copy_request.name,
                "partner_id": copy_request.partner_id.id,
                "partner_name": copy_request.partner_id.display_name,
                "subject": {
                    "naissance": _("Acte de naissance"),
                    "mariage": _("Acte de mariage"),
                    "deces": _("Acte de décès"),
                }[copy_request.document_type],
                "amount_due": invoice.amount_residual,
                "currency_name": currency.name,
                "currency_symbol": currency.symbol,
                "payment_product_id": payment_product.id,
            })
        return result

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.float_utils import float_compare


class EtatCivilCopyPayment(models.Model):
    _name = "etat.civil.copy.payment"
    _description = "Quittance de versement pour copie d'état civil"
    _order = "payment_date desc, id desc"

    name = fields.Char(required=True, readonly=True, copy=False, default="/")
    request_id = fields.Many2one(
        "etat.civil.copy.request", required=True, index=True, ondelete="restrict"
    )
    account_payment_id = fields.Many2one(
        "account.payment", readonly=True, copy=False, ondelete="restrict", index=True
    )
    pos_payment_move_id = fields.Many2one(
        "account.move", readonly=True, copy=False, ondelete="restrict", index=True
    )
    amount = fields.Monetary(required=True, readonly=True, currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", required=True, readonly=True)
    company_id = fields.Many2one("res.company", required=True, readonly=True)
    payment_date = fields.Date(required=True, readonly=True)
    payment_method = fields.Char(required=True, readonly=True)
    received_by_id = fields.Many2one("res.users", required=True, readonly=True)

    _sql_constraints = [
        ("account_payment_unique", "unique(account_payment_id)", "Un paiement comptable ne peut avoir qu'une quittance."),
        ("pos_payment_move_unique", "unique(pos_payment_move_id)", "Un encaissement POS ne peut avoir qu'une quittance."),
        ("positive_amount", "CHECK(amount > 0)", "Le montant de la quittance doit être positif."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "etat.civil.copy.payment"
                ) or "/"
            if bool(vals.get("account_payment_id")) == bool(vals.get("pos_payment_move_id")):
                raise ValidationError(_("Une quittance doit référencer un seul encaissement comptable ou POS."))
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(_("Une quittance émise ne peut pas être modifiée."))

    def unlink(self):
        raise AccessError(_("Une quittance émise ne peut pas être supprimée."))

    def action_print_receipt(self):
        self.ensure_one()
        self.request_id._check_center_access()
        return self.env.ref(
            "etat_civil_account.action_report_copy_payment_receipt"
        ).report_action(self)


class EtatCivilCopyPaymentWizard(models.TransientModel):
    _name = "etat.civil.copy.payment.wizard"
    _description = "Enregistrer un versement pour une copie d'état civil"
    _check_company_auto = True

    request_id = fields.Many2one(
        "etat.civil.copy.request", required=True, readonly=True
    )
    company_id = fields.Many2one(
        "res.company", related="request_id.company_id", readonly=True
    )
    currency_id = fields.Many2one(
        "res.currency", related="request_id.currency_id", readonly=True
    )
    amount = fields.Monetary(
        required=True, currency_field="currency_id",
        help="Un montant inférieur au solde enregistre un paiement partiel.",
    )
    journal_id = fields.Many2one(
        "account.journal", required=True, check_company=True,
        domain="[('company_id', '=', company_id), ('type', 'in', ('cash', 'bank'))]",
    )
    payment_method_line_id = fields.Many2one(
        "account.payment.method.line", required=True, check_company=True,
        domain="[('journal_id', '=', journal_id), ('payment_type', '=', 'inbound')]",
    )
    payment_date = fields.Date(
        required=True, default=fields.Date.context_today
    )
    communication = fields.Char(required=True)

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        request_id = values.get("request_id") or self.env.context.get("default_request_id")
        request = self.env["etat.civil.copy.request"].browse(request_id).exists()
        if request:
            request._check_center_access()
            invoice = request.sudo().account_move_id
            values.setdefault("request_id", request.id)
            values.setdefault("amount", invoice.amount_residual)
            values.setdefault("communication", request.name)
        return values

    @api.constrains("amount")
    def _check_amount(self):
        for wizard in self:
            if wizard.amount <= 0:
                raise ValidationError(_("Le montant du versement doit être positif."))

    def action_register_payment(self):
        self.ensure_one()
        user = self.env.user
        if not (
            user.has_group("etat_civil_account.group_etat_civil_regisseur")
            or user.has_group("etat_civil.group_etat_civil_admin")
        ):
            raise AccessError(_("Seul le régisseur peut enregistrer un versement."))

        request = self.request_id
        request._check_center_access()
        self.env.cr.execute(
            "SELECT id FROM etat_civil_copy_request WHERE id = %s FOR UPDATE",
            [request.id],
        )
        request.invalidate_recordset()
        invoice = request.sudo().account_move_id
        if (
            request.state != "waiting_payment"
            or not request._invoice_matches_request(invoice)
            or invoice.state != "posted"
            or invoice.payment_state == "reversed"
        ):
            raise UserError(_("La facture doit être comptabilisée et conforme avant l'encaissement."))
        if self.journal_id.company_id != request.company_id or self.journal_id.type not in ("cash", "bank"):
            raise ValidationError(_("Choisissez un journal de caisse ou de banque de la société de la demande."))
        if (
            self.payment_method_line_id.journal_id != self.journal_id
            or self.payment_method_line_id.payment_type != "inbound"
        ):
            raise ValidationError(_("Le moyen de paiement doit être un moyen entrant du journal choisi."))
        if float_compare(
            self.amount,
            invoice.amount_residual,
            precision_rounding=invoice.currency_id.rounding,
        ) > 0:
            raise ValidationError(_("Le versement ne peut pas dépasser le solde de la facture."))

        payment_register = self.env["account.payment.register"].sudo().with_context(
            active_model="account.move",
            active_ids=invoice.ids,
        ).create({
            "amount": self.amount,
            "currency_id": invoice.currency_id.id,
            "journal_id": self.journal_id.id,
            "payment_method_line_id": self.payment_method_line_id.id,
            "payment_date": self.payment_date,
            "communication": self.communication,
            "group_payment": False,
            "payment_difference_handling": "open",
        })
        payments = payment_register._create_payments()
        if (
            len(payments) != 1
            or payments.state != "posted"
            or payments.payment_type != "inbound"
            or invoice not in payments.reconciled_invoice_ids
        ):
            raise UserError(_("Odoo n'a pas rapproché le versement à la facture de cette demande."))

        receipts = request._sync_payment_receipts()
        receipt = receipts.filtered(
            lambda item: item.account_payment_id == payments
        )[:1]
        if not receipt:
            raise UserError(_("Le versement est comptabilisé mais sa quittance n'a pas pu être créée."))
        request.action_confirm_payment()
        return self.env.ref(
            "etat_civil_account.action_report_copy_payment_receipt"
        ).report_action(receipt)


class EtatCivilCopyReceiptSettings(models.Model):
    _name = "etat.civil.copy.receipt.settings"
    _description = "Configuration des quittances d'état civil"
    _rec_name = "company_id"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company,
        ondelete="cascade",
    )
    header = fields.Char(string="En-tête")
    legal_notice = fields.Text(string="Mentions à valider par la commune")
    footer = fields.Char(string="Pied de page")

    _sql_constraints = [
        ("company_unique", "unique(company_id)", "Une configuration de quittance est autorisée par société."),
    ]

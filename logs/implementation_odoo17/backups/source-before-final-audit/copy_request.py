from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError


_TRANSITION_TOKEN = object()
_ACT_TYPES = {
    "naissance": "etat.civil.acte.naissance",
    "mariage": "etat.civil.acte.mariage",
    "deces": "etat.civil.acte.deces",
}


class EtatCivilCopyRequest(models.Model):
    _name = "etat.civil.copy.request"
    _description = "Demande de copie d'acte d'état civil"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "request_date desc, id desc"
    _check_company_auto = True

    name = fields.Char(required=True, readonly=True, copy=False, default="Nouveau")
    document_type = fields.Selection(
        [(key, label) for key, label in [
            ("naissance", "Naissance"), ("mariage", "Mariage"), ("deces", "Décès")
        ]], required=True, readonly=True,
    )
    acte_naissance_id = fields.Many2one("etat.civil.acte.naissance", ondelete="restrict")
    acte_mariage_id = fields.Many2one("etat.civil.acte.mariage", ondelete="restrict")
    acte_deces_id = fields.Many2one("etat.civil.acte.deces", ondelete="restrict")
    center_id = fields.Many2one("etat.civil.centre", required=True, readonly=True, index=True)
    partner_id = fields.Many2one(
        "res.partner", string="Demandeur / facturation", required=True,
        ondelete="restrict", check_company=True,
    )
    copy_kind = fields.Selection(
        [("integrale", "Copie intégrale"), ("extrait", "Extrait")],
        required=True, default="integrale", readonly=True,
    )
    copy_number = fields.Integer(readonly=True, copy=False)
    is_free = fields.Boolean(readonly=True, copy=False)
    tariff_id = fields.Many2one("etat.civil.copy.tariff", readonly=True, ondelete="restrict")
    amount = fields.Monetary(readonly=True, currency_field="currency_id", copy=False)
    currency_id = fields.Many2one("res.currency", readonly=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company,
        readonly=True, index=True,
    )
    account_move_id = fields.Many2one(
        "account.move", string="Facture", readonly=True, copy=False,
        ondelete="restrict", check_company=True, index=True,
    )
    state = fields.Selection(
        [
            ("draft", "Brouillon"), ("waiting_payment", "En attente de paiement"),
            ("payment_confirmed", "Paiement confirmé"),
            ("authorized", "Autorisée à délivrer"), ("delivered", "Délivrée"),
            ("cancelled", "Annulée"),
        ], default="draft", required=True, tracking=True, index=True,
    )
    request_date = fields.Datetime(default=fields.Datetime.now, required=True, readonly=True)
    requested_by_id = fields.Many2one(
        "res.users", required=True, readonly=True, default=lambda self: self.env.user
    )
    payment_confirmed_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    payment_confirmed_at = fields.Datetime(readonly=True, copy=False)
    delivered_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    delivered_at = fields.Datetime(readonly=True, copy=False)
    event_ids = fields.One2many("etat.civil.finance.event", "request_id", readonly=True)

    _sql_constraints = [
        ("account_move_unique", "unique(account_move_id)", "Une facture ne peut servir qu'à une demande."),
    ]

    @api.constrains(
        "document_type", "acte_naissance_id", "acte_mariage_id", "acte_deces_id", "center_id"
    )
    def _check_exactly_one_act(self):
        for record in self:
            acts = [record.acte_naissance_id, record.acte_mariage_id, record.acte_deces_id]
            selected = [act for act in acts if act]
            if len(selected) != 1:
                raise ValidationError(_("Une demande doit être liée à exactement un acte."))
            expected = _ACT_TYPES[record.document_type]
            if selected[0]._name != expected:
                raise ValidationError(_("Le type d'acte ne correspond pas à l'acte sélectionné."))
            if selected[0].registre_id.centre_id != record.center_id:
                raise ValidationError(_("Le centre doit correspondre au registre de l'acte."))

    def _selected_act(self):
        self.ensure_one()
        act = self.acte_naissance_id or self.acte_mariage_id or self.acte_deces_id
        if not act:
            raise ValidationError(_("Aucun acte n'est associé à cette demande."))
        act.check_access_rights("read")
        act.check_access_rule("read")
        self._check_center_access()
        return act

    def _check_center_access(self):
        self.ensure_one()
        user = self.env.user
        if user.has_group("etat_civil.group_etat_civil_admin"):
            return
        if not user.has_group("etat_civil.group_etat_civil_agent") and not user.has_group(
            "etat_civil.group_etat_civil_officier"
        ) and not user.has_group("etat_civil_account.group_etat_civil_regisseur"):
            raise AccessError(_("Vous n'êtes pas autorisé à consulter cette demande."))
        if self.center_id not in user.etat_civil_centre_ids:
            raise AccessError(_("Cette demande appartient à un autre centre."))

    @api.model_create_multi
    def create(self, vals_list):
        clean_vals = []
        for original in vals_list:
            vals = dict(original)
            for protected in (
                "state", "copy_number", "is_free", "tariff_id", "amount",
                "currency_id", "account_move_id", "payment_confirmed_by_id",
                "payment_confirmed_at", "delivered_by_id", "delivered_at", "name",
            ):
                vals.pop(protected, None)
            vals["state"] = "draft"
            if vals.get("name", "Nouveau") == "Nouveau":
                vals["name"] = self.env["ir.sequence"].next_by_code("etat.civil.copy.request") or "Nouveau"
            clean_vals.append(vals)
        records = super().create(clean_vals)
        for record in records:
            record._selected_act()
            record._log_event("created", _("Demande créée en brouillon."))
        return records

    def write(self, vals):
        protected = {
            "state", "copy_number", "is_free", "tariff_id", "amount", "currency_id",
            "account_move_id", "payment_confirmed_by_id", "payment_confirmed_at",
            "delivered_by_id", "delivered_at", "name", "center_id", "document_type",
        }
        if protected.intersection(vals) and self.env.context.get("copy_request_transition") is not _TRANSITION_TOKEN:
            raise AccessError(_("Les statuts et données financières sont gérés par les actions serveur."))
        if self.filtered(lambda rec: rec.state != "draft") and set(vals) & {
            "acte_naissance_id", "acte_mariage_id", "acte_deces_id", "partner_id", "copy_kind"
        }:
            raise UserError(_("Une demande soumise ne peut plus changer d'acte ni de bénéficiaire."))
        result = super().write(vals)
        if set(vals) & {"acte_naissance_id", "acte_mariage_id", "acte_deces_id", "document_type", "center_id"}:
            self._check_exactly_one_act()
        return result

    def unlink(self):
        if self.filtered(lambda rec: rec.state != "draft" or rec.account_move_id):
            raise UserError(_("Une demande soumise doit être annulée et conservée dans l'historique."))
        return super().unlink()

    def _log_event(self, event_type, note=None, invoice=None):
        self.ensure_one()
        self.env["etat.civil.finance.event"].sudo().create({
            "request_id": self.id,
            "event_type": event_type,
            "user_id": self.env.uid,
            "note": note,
            "account_move_id": invoice.id if invoice else False,
        })

    def _transition_write(self, vals):
        # Explicit actions perform role, center, state and accounting checks.
        # Elevation is limited to their server-built transition values.
        return self.sudo().with_context(copy_request_transition=_TRANSITION_TOKEN).write(vals)

    def _require_copy_operator(self):
        user = self.env.user
        if not (
            user.has_group("etat_civil.group_etat_civil_admin")
            or user.has_group("etat_civil.group_etat_civil_agent")
            or user.has_group("etat_civil.group_etat_civil_officier")
        ):
            raise AccessError(_("Votre rôle ne permet pas de gérer la délivrance des copies."))

    def action_submit(self):
        self._require_copy_operator()
        for record in self:
            if record.state != "draft":
                raise UserError(_("Seule une demande brouillon peut être soumise."))
            act = record._selected_act()
            if act.statut not in ("valide", "rectifie"):
                raise UserError(_("Seul un acte validé peut faire l'objet d'une copie."))
            table = self.env[act._name]._table
            self.env.cr.execute("SELECT id FROM %s WHERE id = %%s FOR UPDATE" % table, [act.id])
            previous_deliveries = self.search_count([
                ("state", "=", "delivered"), ("acte_naissance_id", "=", act.id if act._name == _ACT_TYPES["naissance"] else False),
                ("acte_mariage_id", "=", act.id if act._name == _ACT_TYPES["mariage"] else False),
                ("acte_deces_id", "=", act.id if act._name == _ACT_TYPES["deces"] else False),
            ])
            active_first = self.search_count([
                ("id", "!=", record.id), ("copy_number", "=", 1),
                ("state", "not in", ("cancelled", "delivered")),
                ("acte_naissance_id", "=", act.id if act._name == _ACT_TYPES["naissance"] else False),
                ("acte_mariage_id", "=", act.id if act._name == _ACT_TYPES["mariage"] else False),
                ("acte_deces_id", "=", act.id if act._name == _ACT_TYPES["deces"] else False),
            ])
            if active_first and not previous_deliveries:
                raise UserError(_("Une première copie est déjà en cours de traitement."))
            tariff = self.env["etat.civil.copy.tariff"]._for_request(
                record.document_type, record.copy_kind, record.center_id, fields.Date.today()
            )
            is_free = bool(tariff.first_copy_free and not previous_deliveries)
            amount = 0.0 if is_free else tariff.price
            state = "authorized" if is_free else "waiting_payment"
            record._transition_write({
                "copy_number": previous_deliveries + 1,
                "is_free": is_free,
                "tariff_id": tariff.id,
                "amount": amount,
                "currency_id": tariff.currency_id.id,
                "state": state,
            })
            record._log_event("submitted", _("Demande soumise; gratuité et tarif déterminés."))
            if is_free:
                record._log_event("authorized", _("Délivrance autorisée sans paiement."))
        return True

    def action_create_invoice(self):
        for record in self:
            record._check_center_access()
            if record.state != "waiting_payment" or record.is_free:
                raise UserError(_("Cette demande ne nécessite pas de facture payable."))
            if record.account_move_id:
                return record.account_move_id
            if not self.env.user.has_group("account.group_account_invoice") and not self.env.user.has_group(
                "account.group_account_user"
            ):
                raise AccessError(_("Un utilisateur comptable habilité doit créer la facture."))
            if not record.tariff_id or record.amount <= 0:
                raise ValidationError(_("Le tarif payable n'est pas configuré."))
            move = self.env["account.move"].create({
                "move_type": "out_invoice",
                "partner_id": record.partner_id.id,
                "invoice_date": fields.Date.today(),
                "company_id": record.company_id.id,
                "invoice_line_ids": [(0, 0, {
                    "product_id": record.tariff_id.product_id.id,
                    "name": "%s — %s %s" % (record.name, record.copy_kind, record.document_type),
                    "quantity": 1,
                    "price_unit": record.amount,
                    "tax_ids": [(6, 0, record.tariff_id.product_id.taxes_id.filtered(
                        lambda tax: tax.company_id == record.company_id
                    ).ids)],
                })],
            })
            record._transition_write({"account_move_id": move.id})
            record._log_event("invoice", _("Facture brouillon créée dans Odoo Accounting."), move)
        return True

    def _payment_is_satisfied(self):
        self.ensure_one()
        # The caller must first validate access to the copy request and center.
        # Finance records are inspected under a narrow sudo and only a Boolean
        # result is returned, so agents can print authorized copies without
        # receiving general accounting read permissions.
        finance_request = self.sudo()
        move = finance_request.account_move_id
        if not move or move.move_type != "out_invoice" or move.state != "posted":
            return False
        if move.payment_state != "paid" or not move.currency_id.is_zero(move.amount_residual):
            return False
        payments = finance_request.env["account.payment"].search([
            ("reconciled_invoice_ids", "in", move.id), ("state", "=", "posted"),
        ])
        if not payments:
            return False
        require_bank = finance_request.env["ir.config_parameter"].get_param(
            "etat_civil_account.require_bank_match", "False"
        ) == "True"
        if require_bank and not all(payments.mapped("is_matched")):
            return False
        return True

    def action_confirm_payment(self):
        user = self.env.user
        if not user.has_group("etat_civil_account.group_etat_civil_regisseur") and not user.has_group(
            "etat_civil.group_etat_civil_admin"
        ):
            raise AccessError(_("Seul un régisseur habilité peut confirmer l'encaissement."))
        for record in self:
            record._check_center_access()
            self.env.cr.execute(
                "SELECT id FROM etat_civil_copy_request WHERE id = %s FOR UPDATE", [record.id]
            )
            record.invalidate_recordset()
            if record.state == "payment_confirmed":
                return True
            if record.state != "waiting_payment" or not record._payment_is_satisfied():
                raise UserError(_("La facture doit être postée, soldée et rapprochée avant confirmation."))
            record._transition_write({
                "state": "payment_confirmed",
                "payment_confirmed_by_id": user.id,
                "payment_confirmed_at": fields.Datetime.now(),
            })
            record._log_event("payment_confirmed", _("Paiement comptablement soldé confirmé par le régisseur."), record.account_move_id)
            record._transition_write({"state": "authorized"})
            record._log_event("authorized", _("Délivrance autorisée après confirmation financière."), record.account_move_id)
        return True

    def action_deliver(self):
        self._require_copy_operator()
        for record in self:
            record._check_center_access()
            if record.state != "authorized":
                raise UserError(_("La demande n'est pas autorisée à être délivrée."))
            if not record.is_free and not record._payment_is_satisfied():
                raise UserError(_("Le paiement n'est plus conforme; délivrance bloquée."))
            record._transition_write({
                "state": "delivered", "delivered_by_id": self.env.uid,
                "delivered_at": fields.Datetime.now(),
            })
            record._log_event("delivered", _("Copie délivrée."), record.account_move_id)
        return True

    def action_print_copy(self):
        self.ensure_one()
        self._check_center_access()
        if self.state not in ("authorized", "delivered"):
            raise UserError(_("Le document ne peut être consulté avant l'autorisation de délivrance."))
        if not self.is_free and not self._payment_is_satisfied():
            raise UserError(_("Le paiement n'est plus conforme; accès au document bloqué."))
        return self.env.ref("etat_civil_account.action_report_copy_document").report_action(self)

    def action_cancel(self):
        self._require_copy_operator()
        for record in self:
            record._check_center_access()
            if record.state in ("delivered", "cancelled"):
                raise UserError(_("Une demande délivrée ou déjà annulée ne peut pas être annulée."))
            if record.account_move_id and record.account_move_id.state == "posted":
                raise UserError(_("La facture est comptabilisée : utilisez le flux comptable d'avoir/remboursement."))
            if record.account_move_id and record.account_move_id.state == "draft":
                # Keep the accounting document and its audit trail; use Odoo's
                # native cancellation transition rather than unlinking it.
                record.account_move_id.button_cancel()
            record._transition_write({"state": "cancelled"})
            record._log_event("cancelled", _("Demande annulée; les documents comptables sont conservés."), record.account_move_id)
        return True


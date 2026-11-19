from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.float_utils import float_compare


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
    entitlement_individu_id = fields.Many2one(
        "etat.civil.individu", string="Individu bénéficiaire de la gratuité",
        readonly=True, copy=False, index=True, ondelete="restrict",
    )
    guichet_ticket_id = fields.Many2one(
        "etat.civil.demande.guichet", string="Ticket guichet",
        copy=False, ondelete="restrict",
    )
    center_id = fields.Many2one("etat.civil.centre", required=True, readonly=True, index=True)
    partner_id = fields.Many2one(
        "res.partner", string="Demandeur / facturation", required=True,
        ondelete="restrict", check_company=True,
    )
    copy_kind = fields.Selection(
        [("integrale", "Copie intégrale"), ("extrait", "Extrait")],
        required=True, default="integrale", readonly=True,
    )
    copy_quantity = fields.Integer(
        string="Nombre de copies",
        required=True,
        default=1,
        copy=False,
    )
    copy_number = fields.Integer(readonly=True, copy=False)
    free_copy_quantity = fields.Integer(
        string="Copies gratuites",
        readonly=True,
        copy=False,
    )
    billable_quantity = fields.Integer(
        string="Copies facturables",
        compute="_compute_billable_quantity",
    )
    is_free = fields.Boolean(readonly=True, copy=False)
    tariff_id = fields.Many2one("etat.civil.copy.tariff", readonly=True, ondelete="restrict")
    product_snapshot_id = fields.Many2one("product.product", readonly=True, ondelete="restrict")
    tax_snapshot_ids = fields.Many2many(
        "account.tax", "etat_civil_copy_request_tax_rel", "request_id", "tax_id",
        string="Taxes figées à la soumission", readonly=True,
    )
    unit_price = fields.Monetary(readonly=True, currency_field="currency_id", copy=False)
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
    invoice_state = fields.Selection(
        related="account_move_id.state", string="État de la facture", readonly=True
    )
    state = fields.Selection(
        [
            ("draft", "Brouillon"), ("waiting_payment", "En attente de paiement"),
            ("payment_confirmed", "Paiement confirmé"),
            ("authorized", "Autorisée à délivrer"), ("delivered", "Délivrée"),
            ("cancelled", "Annulée"), ("acte_not_found", "Acte non retrouvé"),
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
    payment_ids = fields.One2many(
        "etat.civil.copy.payment", "request_id", string="Quittances",
        readonly=True,
    )

    # Changement 4 : Acte introuvable (ancien registre papier non numérisé)
    acte_introuvable_note = fields.Text(
        string="Note sur l'acte introuvable",
        help="Renseignez les détails de recherche lorsque l'acte demandé n'existe pas dans le système (registre papier non numérisé, etc.).",
    )

    # Changement 7 : Champs optionnels pour la traçabilité du demandeur
    requester_id_type = fields.Selection(
        [
            ("cin", "CIN"),
            ("passeport", "Passeport"),
            ("carte_vitale", "Carte vitale"),
            ("autre", "Autre"),
        ],
        string="Type de pièce d'identité du demandeur",
    )
    requester_id_number = fields.Char(
        string="Numéro de pièce d'identité du demandeur",
    )
    requester_quality = fields.Selection(
        [
            ("interesse", "Intéressé(e) lui-même"),
            ("parent", "Parent"),
            ("representant_legal", "Représentant légal"),
            ("mandataire", "Mandataire"),
            ("autre", "Autre qualité"),
        ],
        string="Qualité du demandeur",
    )

    _sql_constraints = [
        ("account_move_unique", "unique(account_move_id)", "Une facture ne peut servir qu'à une demande."),
        ("copy_quantity_positive", "CHECK(copy_quantity > 0)", "Le nombre de copies doit être supérieur à zéro."),
        ("guichet_ticket_unique", "unique(guichet_ticket_id)", "Un ticket guichet ne peut servir qu'à une demande de copie."),
    ]

    @api.depends("copy_quantity", "free_copy_quantity")
    def _compute_billable_quantity(self):
        for record in self:
            record.billable_quantity = max(
                record.copy_quantity - record.free_copy_quantity, 0
            )

    @api.constrains(
        "document_type", "acte_naissance_id", "acte_mariage_id", "acte_deces_id",
        "center_id", "entitlement_individu_id", "guichet_ticket_id", "state",
    )
    def _check_exactly_one_act(self):
        for record in self:
            # Changement 4 : l'état "acte_not_found" n'exige pas de lien avec un acte
            if record.state == "acte_not_found":
                continue
            acts = [record.acte_naissance_id, record.acte_mariage_id, record.acte_deces_id]
            selected = [act for act in acts if act]
            if len(selected) != 1:
                raise ValidationError(_("Une demande doit être liée à exactement un acte."))
            expected = _ACT_TYPES[record.document_type]
            if selected[0]._name != expected:
                raise ValidationError(_("Le type d'acte ne correspond pas à l'acte sélectionné."))
            if selected[0].registre_id.centre_id != record.center_id:
                raise ValidationError(_("Le centre doit correspondre au registre de l'acte."))
            expected_individual = (
                selected[0].enfant_id
                if selected[0]._name == _ACT_TYPES["naissance"]
                else self.env["etat.civil.individu"]
            )
            if record.state != "draft" and record.entitlement_individu_id != expected_individual:
                raise ValidationError(_("L'individu bénéficiaire doit correspondre à l'acte de naissance."))
            if record.guichet_ticket_id:
                ticket = record.guichet_ticket_id
                if (
                    ticket.type_acte != record.document_type
                    or ticket.type_demande not in ("copie_integrale", "extrait")
                    or ticket.statut == "annule"
                ):
                    raise ValidationError(_("Le ticket guichet doit concerner une copie du même type d'acte et ne pas être annulé."))

    def _selected_act(self):
        self.ensure_one()
        if self.state == "acte_not_found":
            return self.env["etat.civil.acte.officiel"]
        act = self.acte_naissance_id or self.acte_mariage_id or self.acte_deces_id
        if not act:
            raise ValidationError(_("Aucun acte n'est associé à cette demande."))
        act.check_access_rights("read")
        act.check_access_rule("read")
        self._check_center_access()
        return act

    def _assert_deliverable_act(self):
        self.ensure_one()
        act = self._selected_act()
        if act.statut not in ("valide", "rectifie"):
            raise UserError(_("L'acte n'est plus dans un état autorisant la délivrance."))
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
                "state", "copy_number", "is_free", "tariff_id", "product_snapshot_id",
                "tax_snapshot_ids", "unit_price", "amount",
                "currency_id", "account_move_id", "payment_confirmed_by_id",
                "payment_confirmed_at", "delivered_by_id", "delivered_at", "name",
                "free_copy_quantity", "entitlement_individu_id",
            ):
                vals.pop(protected, None)
            vals["state"] = "draft"
            if vals.get("name", "Nouveau") == "Nouveau":
                vals["name"] = self.env["ir.sequence"].next_by_code("etat.civil.copy.request") or "Nouveau"
            clean_vals.append(vals)
        records = super().create(clean_vals)
        for record in records:
            record._log_event("created", _("Demande créée en brouillon."))
        # Changement 3 : avertissement anti-doublon
        for record in records:
            record._check_duplicate_warning()
        return records

    def _check_duplicate_warning(self):
        """Avertir si une demande identique (même acte, même type de copie) existe
        avec un état actif dans les dernières 24 heures, sans bloquer la création."""
        self.ensure_one()
        if self.state == "acte_not_found":
            return
        if not self.acte_naissance_id and not self.acte_mariage_id and not self.acte_deces_id:
            return
        cutoff = fields.Datetime.now() - timedelta(hours=24)
        scope_domain = [
            ("acte_naissance_id", "=", self.acte_naissance_id.id if self.acte_naissance_id else False),
            ("acte_mariage_id", "=", self.acte_mariage_id.id if self.acte_mariage_id else False),
            ("acte_deces_id", "=", self.acte_deces_id.id if self.acte_deces_id else False),
            ("copy_kind", "=", self.copy_kind),
            ("state", "not in", ("cancelled", "delivered", "acte_not_found")),
            ("request_date", ">=", cutoff),
            ("id", "!=", self.id),
        ]
        duplicates = self.search(scope_domain)
        if duplicates:
            dup_names = ", ".join(duplicates.mapped("name"))
            raise UserError(_(
                "Attention : une demande de copie similaire est déjà en cours de traitement "
                "pour cet acte (%s). Vérifiez qu'il ne s'agit pas d'un doublon avant de "
                "poursuivre.") % dup_names)

    def write(self, vals):
        protected = {
            "state", "copy_number", "is_free", "tariff_id", "product_snapshot_id",
            "tax_snapshot_ids", "unit_price", "amount", "currency_id",
            "account_move_id", "free_copy_quantity", "payment_confirmed_by_id",
            "payment_confirmed_at",
            "delivered_by_id", "delivered_at", "name", "center_id", "document_type",
            "entitlement_individu_id",
        }
        if protected.intersection(vals) and self.env.context.get("copy_request_transition") is not _TRANSITION_TOKEN:
            raise AccessError(_("Les statuts et données financières sont gérés par les actions serveur."))
        if self.filtered(lambda rec: rec.state != "draft") and set(vals) & {
            "acte_naissance_id", "acte_mariage_id", "acte_deces_id", "partner_id",
            "copy_kind", "copy_quantity", "guichet_ticket_id",
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

    def _log_event(self, event_type, note=None, invoice=None, payment=None):
        self.ensure_one()
        finance_event = self.env["etat.civil.finance.event"].sudo().create({
            "request_id": self.id,
            "event_type": event_type,
            "user_id": self.env.uid,
            "note": note,
            "account_move_id": invoice.id if invoice else False,
            "payment_id": payment.id if payment else False,
        })
        audit_action = {
            "created": "copy_request",
            "submitted": "copy_request",
            "payment": "payment",
            "payment_confirmed": "payment",
            "delivered": "delivery",
            "cancelled": "cancel",
            "refund": "refund",
            "acte_not_found": "copy_request",
        }.get(event_type, "other")
        state_by_event = {
            "created": "draft",
            "submitted": "waiting_payment",
            "invoice": "waiting_payment",
            "invoice_posted": "waiting_payment",
            "payment_confirmed": "payment_confirmed",
            "authorized": "authorized",
            "delivered": "delivered",
            "cancelled": "cancelled",
            "acte_not_found": "acte_not_found",
        }
        details = {
            "finance_event_type": event_type,
            "related_id": finance_event.id,
        }
        if payment:
            details.update({
                "amount": payment.amount,
                "currency_id": payment.currency_id.id,
            })
        state_value = state_by_event.get(event_type)
        self.env["etat.civil.audit.log"]._record_event(
            audit_action,
            record=self,
            new_values={"state": state_value} if state_value else {},
            details=details,
        )

    def _transition_write(self, vals):
        # Explicit actions perform role, center, state and accounting checks.
        # Elevation is limited to their server-built transition values.
        return self.sudo().with_context(copy_request_transition=_TRANSITION_TOKEN).write(vals)

    def _require_copy_operator(self):
        user = self.env.user
        if not (
            user.has_group("etat_civil.group_etat_civil_admin")
            or user.has_group("etat_civil.group_etat_civil_agent")
            or user.has_group("etat_civil_account.group_etat_civil_regisseur")
        ):
            raise AccessError(_("Votre rôle ne permet pas de gérer la délivrance des copies."))

    def action_mark_acte_not_found(self):
        """Changement 4 : Marquer une demande comme 'acte non retrouvé'.
        Utilisé lorsque l'acte demandé n'existe pas dans le système
        (ancien registre papier non numérisé, etc.)."""
        self._require_copy_operator()
        for record in self.sorted("id"):
            record._check_center_access()
            self.env.cr.execute(
                "SELECT id FROM etat_civil_copy_request WHERE id = %s FOR UPDATE",
                [record.id],
            )
            record.invalidate_recordset()
            if record.state != "draft":
                raise UserError(_("Seule une demande brouillon peut être marquée comme acte non retrouvé."))
            if not (record.acte_introuvable_note or "").strip():
                raise UserError(_(
                    "Veuillez renseigner une note expliquant pourquoi l'acte est introuvable "
                    "(détails de la recherche, registre papier concerné, etc.)."
                ))
            record._transition_write({"state": "acte_not_found"})
            record._log_event(
                "acte_not_found",
                _("Acte non retrouvé : %s") % (record.acte_introuvable_note[:200],),
            )
        return True

    def action_submit(self):
        self._require_copy_operator()
        for record in self.sorted("id"):
            record._check_center_access()
            # Serialize submissions of the same request before examining state.
            self.env.cr.execute(
                "SELECT id FROM etat_civil_copy_request WHERE id = %s FOR UPDATE",
                [record.id],
            )
            record.invalidate_recordset()
            if record.state not in ("draft",):
                raise UserError(_("Seule une demande brouillon peut être soumise."))
            act = record._selected_act()
            table = self.env[act._name]._table
            self.env.cr.execute("SELECT id FROM %s WHERE id = %%s FOR UPDATE" % table, [act.id])
            act.invalidate_recordset()
            if act.statut not in ("valide", "rectifie"):
                raise UserError(_("Seul un acte validé peut faire l'objet d'une copie."))
            entitlement_individu = (
                act.enfant_id if act._name == _ACT_TYPES["naissance"]
                else self.env["etat.civil.individu"]
            )
            if entitlement_individu:
                self.env.cr.execute(
                    "SELECT id FROM etat_civil_individu WHERE id = %s FOR UPDATE",
                    [entitlement_individu.id],
                )
                scope_domain = [("entitlement_individu_id", "=", entitlement_individu.id)]
            else:
                scope_domain = [
                    ("acte_naissance_id", "=", act.id if act._name == _ACT_TYPES["naissance"] else False),
                    ("acte_mariage_id", "=", act.id if act._name == _ACT_TYPES["mariage"] else False),
                    ("acte_deces_id", "=", act.id if act._name == _ACT_TYPES["deces"] else False),
                ]
            previous_requests = self.search(scope_domain + [("state", "=", "delivered")])
            previous_deliveries = sum(previous_requests.mapped("copy_quantity"))
            active_first = self.search_count([
                ("id", "!=", record.id),
                ("copy_number", "=", 1),
                ("state", "not in", ("cancelled", "delivered")),
            ] + scope_domain)
            if active_first and not previous_deliveries:
                raise UserError(_("Une première copie est déjà en cours de traitement."))
            tariff = self.env["etat.civil.copy.tariff"]._for_request(
                record.document_type, record.copy_kind, record.center_id, fields.Date.today()
            )
            company = record.company_id
            taxes = tariff.product_id.taxes_id.filtered(
                lambda tax: tax.company_id == company
            )
            fiscal_position = record.partner_id.with_company(company).property_account_position_id
            if fiscal_position:
                taxes = fiscal_position.map_tax(taxes)
            free_copy_quantity = int(
                tariff.first_copy_free
                and previous_deliveries == 0
                and record.copy_quantity > 0
            )
            billable_quantity = record.copy_quantity - free_copy_quantity
            billable_totals = taxes.compute_all(
                tariff.price,
                currency=tariff.currency_id,
                quantity=billable_quantity,
                product=tariff.product_id,
                partner=record.partner_id,
            )
            is_free = billable_quantity == 0
            amount = billable_totals["total_included"]
            state = "authorized" if is_free else "waiting_payment"
            record._transition_write({
                "copy_number": previous_deliveries + 1,
                "entitlement_individu_id": entitlement_individu.id if entitlement_individu else False,
                "is_free": is_free,
                "free_copy_quantity": free_copy_quantity,
                "tariff_id": tariff.id,
                "product_snapshot_id": tariff.product_id.id,
                "tax_snapshot_ids": [(6, 0, taxes.ids)],
                "unit_price": tariff.price,
                "amount": amount,
                "currency_id": tariff.currency_id.id,
                "state": state,
            })
            record._log_event("submitted", _("Demande soumise; gratuité et tarif déterminés."))
            if is_free:
                record._log_event("authorized", _("Délivrance autorisée sans paiement."))
        return True

    def action_create_invoice(self):
        self.ensure_one()
        self._check_center_access()
        self.env.cr.execute(
            "SELECT id FROM etat_civil_copy_request WHERE id = %s FOR UPDATE",
            [self.id],
        )
        self.invalidate_recordset()
        if self.state != "waiting_payment" or self.is_free:
            raise UserError(_("Cette demande ne nécessite pas de facture payable."))
        if not (
            self.env.user.has_group("etat_civil_account.group_etat_civil_regisseur")
            or self.env.user.has_group("etat_civil.group_etat_civil_admin")
        ):
            raise AccessError(_("Un utilisateur habilité ne peut pas créer la facture."))
        if self.account_move_id:
            return self._action_open_invoice()
        if not self.tariff_id or self.amount <= 0:
            raise ValidationError(_("Le tarif payable n'est pas configuré."))
        if self.tariff_id.currency_id != self.company_id.currency_id:
            exchange_rate = self.env["res.currency.rate"].search(
                [
                    ("currency_id", "=", self.currency_id.id),
                    ("name", "<=", fields.Date.today()),
                    ("company_id", "in", [False, self.company_id.id]),
                ],
                order="company_id desc, name desc",
                limit=1,
            )
            if not exchange_rate:
                raise ValidationError(_(
                    "Aucun taux de change %s n'est configuré au %s."
                ) % (self.currency_id.display_name, fields.Date.today()))
        move = self.env["account.move"].sudo().create({
            "move_type": "out_invoice",
            "partner_id": self.partner_id.id,
            "invoice_date": fields.Date.today(),
            "company_id": self.company_id.id,
            "currency_id": self.currency_id.id,
            "invoice_line_ids": [(0, 0, {
                "product_id": self.product_snapshot_id.id,
                "name": "%s — %s %s — %s copie(s)" % (
                    self.name,
                    self.copy_kind,
                    self.document_type,
                    self.billable_quantity,
                ),
                "quantity": self.billable_quantity,
                "price_unit": self.unit_price,
                "tax_ids": [(6, 0, self.tax_snapshot_ids.ids)],
            })],
        })
        self._transition_write({"account_move_id": move.id})
        self._log_event("invoice", _("Facture brouillon créée dans Odoo Accounting."), move)
        return self._action_open_invoice()

    def _action_open_invoice(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Facture de copie"),
            "res_model": "account.move",
            "view_mode": "form",
            "res_id": self.account_move_id.id,
            "target": "current",
        }

    def _invoice_matches_request(self, move):
        """Validate the exact accounting document and line tied to this request."""
        self.ensure_one()
        if not move or move.move_type != "out_invoice":
            return False
        if (
            move.company_id != self.company_id
            or move.partner_id != self.partner_id
            or move.currency_id != self.currency_id
        ):
            return False
        lines = move.invoice_line_ids
        if len(lines) != 1:
            return False
        line = lines[0]
        if (
            line.product_id != self.product_snapshot_id
            or float_compare(line.quantity, self.billable_quantity, precision_digits=6) != 0
            or float_compare(line.price_unit, self.unit_price, precision_rounding=self.currency_id.rounding) != 0
            or set(line.tax_ids.ids) != set(self.tax_snapshot_ids.ids)
        ):
            return False
        return self.currency_id.is_zero(move.amount_total - self.amount)

    def _payment_is_satisfied(self):
        self.ensure_one()
        finance_request = self.sudo()
        move = finance_request.account_move_id
        if not finance_request._invoice_matches_request(move) or move.state != "posted":
            return False
        if finance_request.env["account.move"].search_count([
            ("reversed_entry_id", "=", move.id), ("state", "=", "posted"),
        ]):
            return False
        if move.payment_state not in ("paid", "in_payment") or not move.currency_id.is_zero(move.amount_residual):
            return False
        # A paid state may also result from a credit note or write-off. Require
        # the invoice receivable balance to be reconciled exclusively against
        # posted inbound customer payments linked to this exact invoice.
        partials = finance_request.env["account.partial.reconcile"]
        receivable_lines = move.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        )
        for line in receivable_lines:
            partials |= line.matched_debit_ids | line.matched_credit_ids
        reconciled_invoice_amount = 0.0
        payments = finance_request.env["account.payment"]
        has_pos_payment = False
        for partial in partials:
            if partial.debit_move_id.move_id == move:
                counter_line = partial.credit_move_id
                partial_amount = partial.debit_amount_currency
                partial_currency = partial.debit_currency_id
            elif partial.credit_move_id.move_id == move:
                counter_line = partial.debit_move_id
                partial_amount = partial.credit_amount_currency
                partial_currency = partial.credit_currency_id
            else:
                return False
            if partial_currency != move.currency_id:
                return False
            payment = counter_line.move_id.payment_id
            if not payment:
                if partial.exchange_move_id and move.currency_id.is_zero(partial_amount):
                    continue
                source_kind, source = finance_request._get_invoice_payment_source(
                    counter_line, move
                )
                if source_kind != "pos" or not finance_request._is_valid_pos_payment_source(
                    source, move
                ):
                    return False
                has_pos_payment = True
            else:
                payments |= payment
            reconciled_invoice_amount += partial_amount
        if not payments and not has_pos_payment:
            return False
        if any(
            payment.state != "posted"
            or payment.payment_type != "inbound"
            or payment.partner_type != "customer"
            or payment.partner_id != self.partner_id
            or payment.company_id != self.company_id
            or payment.move_id.state != "posted"
            or move not in payment.reconciled_invoice_ids
            for payment in payments
        ):
            return False
        if float_compare(
            reconciled_invoice_amount,
            move.amount_total,
            precision_rounding=move.currency_id.rounding,
        ) != 0:
            return False
        require_bank = finance_request.env["ir.config_parameter"].get_param(
            "etat_civil_account.require_bank_match", "False"
        ) == "True"
        if require_bank and payments and not all(payments.mapped("is_matched")):
            return False
        return True

    def _get_invoice_payment_source(self, counterpart_line, invoice):
        return False, self.env["account.payment"]

    def _is_valid_pos_payment_source(self, pos_payments, invoice):
        return False

    def _sync_account_payment_receipts(self):
        receipts = self.env["etat.civil.copy.payment"]
        for record in self:
            finance_request = record.sudo()
            invoice = finance_request.account_move_id
            if not finance_request._invoice_matches_request(invoice):
                continue
            receivable_lines = invoice.line_ids.filtered(
                lambda line: line.account_id.account_type == "asset_receivable"
            )
            partials = finance_request.env["account.partial.reconcile"]
            for line in receivable_lines:
                partials |= line.matched_debit_ids | line.matched_credit_ids
            amounts_by_payment = {}
            for partial in partials:
                if partial.debit_move_id.move_id == invoice:
                    counter_line = partial.credit_move_id
                    amount = partial.debit_amount_currency
                    currency = partial.debit_currency_id
                elif partial.credit_move_id.move_id == invoice:
                    counter_line = partial.debit_move_id
                    amount = partial.credit_amount_currency
                    currency = partial.credit_currency_id
                else:
                    continue
                payment = counter_line.move_id.payment_id
                if payment and currency == invoice.currency_id:
                    existing_payment, existing_amount = amounts_by_payment.get(
                        payment.id, (payment, 0.0)
                    )
                    amounts_by_payment[payment.id] = (
                        existing_payment, existing_amount + amount
                    )
            for payment, amount in amounts_by_payment.values():
                if (
                    amount <= 0
                    or payment.state != "posted"
                    or payment.payment_type != "inbound"
                    or payment.partner_type != "customer"
                    or payment.partner_id != finance_request.partner_id
                    or payment.company_id != finance_request.company_id
                    or payment.move_id.state != "posted"
                ):
                    continue
                receipt = receipts.sudo().search(
                    [("account_payment_id", "=", payment.id)], limit=1
                )
                if receipt:
                    receipts |= receipt
                    continue
                receipt = receipts.sudo().create({
                    "request_id": finance_request.id,
                    "account_payment_id": payment.id,
                    "amount": amount,
                    "currency_id": invoice.currency_id.id,
                    "company_id": finance_request.company_id.id,
                    "payment_date": payment.date,
                    "payment_method": payment.payment_method_line_id.display_name,
                    "received_by_id": self.env.uid,
                })
                receipts |= receipt
                record._log_event(
                    "payment",
                    _("Versement reçu; quittance %s.", receipt.name),
                    invoice,
                    receipt,
                )
        return receipts

    def _sync_payment_receipts(self):
        return self._sync_account_payment_receipts()

    def action_post_invoice(self):
        self.ensure_one()
        user = self.env.user
        if not (
            user.has_group("etat_civil_account.group_etat_civil_regisseur")
            or user.has_group("etat_civil.group_etat_civil_admin")
        ):
            raise AccessError(_("Seul le régisseur peut comptabiliser cette facture."))
        self._check_center_access()
        invoice = self.sudo().account_move_id
        if (
            self.state != "waiting_payment"
            or not self._invoice_matches_request(invoice)
            or invoice.state != "draft"
        ):
            raise UserError(_("Seule la facture brouillon conforme à cette demande peut être comptabilisée."))
        invoice.action_post()
        self._log_event("invoice_posted", _("Facture comptabilisée avant encaissement."), invoice)
        return True

    def action_register_payment(self):
        self.ensure_one()
        self._check_center_access()
        if not (
            self.env.user.has_group("etat_civil_account.group_etat_civil_regisseur")
            or self.env.user.has_group("etat_civil.group_etat_civil_admin")
        ):
            raise AccessError(_("Seul le régisseur peut enregistrer un versement."))
        if self.state != "waiting_payment":
            raise UserError(_("La demande n'est pas en attente de paiement."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Enregistrer un versement"),
            "res_model": "etat.civil.copy.payment.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_request_id": self.id,
            },
        }

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
            if record.state in ("payment_confirmed", "authorized", "delivered"):
                return True
            if record.state != "waiting_payment":
                raise UserError(_("La demande n'est pas en attente de paiement."))
            record._sync_payment_receipts()
            if not record._payment_is_satisfied():
                return True
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
        for record in self.sorted("id"):
            record._check_center_access()
            # A request may be submitted by two workers at once. Lock and reload
            # it so only the first transaction can record a delivery.
            self.env.cr.execute(
                "SELECT id FROM etat_civil_copy_request WHERE id = %s FOR UPDATE",
                [record.id],
            )
            record.invalidate_recordset()
            if record.state != "authorized":
                raise UserError(_("La demande n'est pas autorisée à être délivrée."))
            record._assert_deliverable_act()
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
        self._assert_deliverable_act()
        if not self.is_free and not self._payment_is_satisfied():
            raise UserError(_("Le paiement n'est plus conforme; accès au document bloqué."))
        return self.env.ref("etat_civil_account.action_report_copy_document").report_action(self)

    def action_cancel(self):
        self._require_copy_operator()
        for record in self.sorted("id"):
            record._check_center_access()
            self.env.cr.execute(
                "SELECT id FROM etat_civil_copy_request WHERE id = %s FOR UPDATE", [record.id]
            )
            record.invalidate_recordset()
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

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


class EtatCivilDemandeGuichet(models.Model):
    _inherit = "etat.civil.demande.guichet"

    copy_request_ids = fields.One2many(
        "etat.civil.copy.request", "guichet_ticket_id",
        string="Demandes de copie liées", readonly=True,
    )

    # Champ vers la première demande de copie liée (pour l'affichage rapide)
    copy_request_id = fields.Many2one(
        "etat.civil.copy.request", string="Demande de copie",
        compute="_compute_copy_request_info", readonly=True,
    )
    copy_request_state = fields.Selection(
        selection=[
            ("draft", "Brouillon"),
            ("waiting_payment", "En attente de paiement"),
            ("payment_confirmed", "Paiement confirmé"),
            ("authorized", "Autorisée à délivrer"),
            ("delivered", "Délivrée"),
            ("cancelled", "Annulée"),
        ],
        compute="_compute_copy_request_info", string="État du paiement",
        readonly=True,
    )
    copy_request_amount = fields.Monetary(
        compute="_compute_copy_request_info",
        string="Montant dû", currency_field="copy_request_currency_id",
        readonly=True,
    )
    copy_request_currency_id = fields.Many2one(
        "res.currency", compute="_compute_copy_request_info", readonly=True,
    )
    has_payment = fields.Boolean(
        compute="_compute_copy_request_info",
        help="Vrai si la demande a au moins une quittance enregistrée.",
    )
    can_encaisser = fields.Boolean(
        compute="_compute_copy_request_info",
        help="Vrai si le régisseur peut encaisser cette demande.",
    )

    @api.depends("copy_request_ids", "copy_request_ids.state",
                 "copy_request_ids.amount", "copy_request_ids.currency_id",
                 "copy_request_ids.account_move_id.state",
                 "copy_request_ids.payment_ids")
    def _compute_copy_request_info(self):
        for record in self:
            # Prendre la première demande de copie liée (unique par contrainte SQL)
            request = record.copy_request_ids[:1]
            if request:
                record.copy_request_id = request.id
                record.copy_request_state = request.state
                record.copy_request_amount = request.amount
                record.copy_request_currency_id = request.currency_id
                record.has_payment = bool(request.payment_ids)
                # Peut encaisser si : état waiting_payment, facture comptabilisée, pas annulé
                record.can_encaisser = (
                    request.state == "waiting_payment"
                    and request.account_move_id.state == "posted"
                    and record.statut != "annule"
                )
            else:
                record.copy_request_id = False
                record.copy_request_state = False
                record.copy_request_amount = 0.0
                record.copy_request_currency_id = False
                record.has_payment = False
                record.can_encaisser = False

    def action_encaisser(self):
        """Ouvrir le wizard d'encaissement depuis la file d'attente.
        Réservé au régisseur et à l'administrateur."""
        self.ensure_one()
        user = self.env.user
        is_regisseur = user.has_group('etat_civil_account.group_etat_civil_regisseur')
        is_admin = user.has_group('etat_civil.group_etat_civil_admin')
        if not (is_regisseur or is_admin):
            raise AccessError(
                "Impossible d'encaisser : cette action est réservée aux régisseurs "
                "et aux administrateurs. Votre profil ne permet pas cette opération."
            )
        if self.statut == "annule":
            raise UserError(
                f"Impossible d'encaisser le ticket {self.ticket_numero} : "
                f"cette demande est annulée. Un ticket annulé ne peut faire l'objet "
                f"d'aucun encaissement."
            )
        request = self.copy_request_ids[:1]
        if not request:
            raise UserError(
                f"Impossible d'encaisser le ticket {self.ticket_numero} : "
                f"aucune demande de copie n'est liée à ce ticket. "
                f"Vérifiez que la demande de copie a bien été créée."
            )
        if request.state == "cancelled":
            raise UserError(
                f"Impossible d'encaisser le ticket {self.ticket_numero} : "
                f"la demande de copie associée est annulée. "
                f"Une demande annulée ne peut être encaissée."
            )
        if request.state in ("payment_confirmed", "authorized", "delivered"):
            raise UserError(
                f"Impossible d'encaisser le ticket {self.ticket_numero} : "
                f"cette demande est déjà payée (état « {dict(request._fields['state'].selection).get(request.state, request.state)} »). "
                f"Un nouvel encaissement n'est pas nécessaire."
            )
        if request.state != "waiting_payment":
            raise UserError(
                f"Impossible d'encaisser le ticket {self.ticket_numero} : "
                f"la demande de copie est à l'état « {dict(request._fields['state'].selection).get(request.state, request.state)} ». "
                f"Seule une demande en attente de paiement peut être encaissée."
            )
        invoice = request.sudo().account_move_id
        if not invoice or invoice.state != "posted":
            raise UserError(
                f"Impossible d'encaisser le ticket {self.ticket_numero} : "
                f"la facture n'est pas encore comptabilisée. "
                f"Veuillez d'abord créer et comptabiliser la facture depuis la demande de copie."
            )
        # Ouvrir le wizard d'encaissement
        return {
            "name": "Encaissement — Ticket %s" % self.ticket_numero,
            "type": "ir.actions.act_window",
            "res_model": "etat.civil.copy.payment.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_request_id": request.id},
        }

    def action_open_copy_request(self):
        """Ouvrir la demande de copie liée depuis la file d'attente."""
        self.ensure_one()
        request = self.copy_request_ids[:1]
        if not request:
            raise UserError(
                f"Aucune demande de copie n'est liée au ticket {self.ticket_numero}."
            )
        return {
            "name": "Demande de copie — Ticket %s" % self.ticket_numero,
            "type": "ir.actions.act_window",
            "res_model": "etat.civil.copy.request",
            "res_id": request.id,
            "view_mode": "form",
            "target": "current",
        }

    def _get_latest_receipt(self):
        """Retourner la dernière quittance du ticket, avec vérifications d'accès."""
        self.ensure_one()
        user = self.env.user
        is_regisseur = user.has_group('etat_civil_account.group_etat_civil_regisseur')
        is_admin = user.has_group('etat_civil.group_etat_civil_admin')
        if not (is_regisseur or is_admin):
            raise AccessError(
                "Impossible d'accéder à la quittance : cette action est réservée aux régisseurs "
                "et aux administrateurs. Votre profil ne permet pas cette opération."
            )
        request = self.copy_request_ids[:1]
        if not request:
            raise UserError(
                f"Aucune demande de copie n'est liée au ticket {self.ticket_numero}. "
                f"Vérifiez que la demande de copie a bien été créée."
            )
        if not request.payment_ids:
            raise UserError(
                f"Aucun versement n'a été enregistré pour le ticket {self.ticket_numero}. "
                f"Veuillez d'abord encaisser la demande."
            )
        return request.payment_ids.sorted("payment_date")[-1]

    def action_view_quittance(self):
        """Voir la quittance — affiche la quittance dans une fenêtre modale HTML.
        Utilise le même template QWeb que le PDF pour que l'aperçu soit identique."""
        self.ensure_one()
        receipt = self._get_latest_receipt()
        # Utiliser _get_report_values du rapport pour préparer les données du template
        report_model = self.env["report.etat_civil_account.copy_payment_receipt"]
        report_values = report_model._get_report_values(receipt.ids, None)
        # Rendre le template QWeb en HTML pur
        html = self.env["ir.actions.report"]._render_template(
            "etat_civil_account.copy_payment_receipt", report_values
        )
        if isinstance(html, bytes):
            html = html.decode('utf-8')
        # Créer un enregistrement temporaire dans le wizard d'aperçu
        preview = self.env["etat.civil.receipt.preview"].sudo().create({
            "receipt_id": receipt.id,
            "html_content": html,
        })
        return {
            "name": "Aperçu de la quittance %s" % receipt.name,
            "type": "ir.actions.act_window",
            "res_model": "etat.civil.receipt.preview",
            "view_mode": "form",
            "target": "new",
            "res_id": preview.id,
        }

    def action_print_quittance(self):
        """Imprimer la quittance depuis la file d'attente.
        Réservé au régisseur et à l'administrateur."""
        self.ensure_one()
        receipt = self._get_latest_receipt()
        return receipt.action_print_receipt()

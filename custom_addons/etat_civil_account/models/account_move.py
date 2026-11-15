from odoo import _, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    etat_civil_copy_request_ids = fields.One2many(
        "etat.civil.copy.request",
        "account_move_id",
        string="Demandes de copie d'état civil",
        readonly=True,
    )

    def action_post(self):
        result = super().action_post()
        requests = self.env["etat.civil.copy.request"].sudo()
        for credit_note in self.filtered(
            lambda move: move.move_type == "out_refund" and move.reversed_entry_id
        ):
            linked_requests = requests.search([
                ("account_move_id", "=", credit_note.reversed_entry_id.id),
            ])
            for copy_request in linked_requests:
                copy_request._log_event(
                    "refund",
                    _("Avoir client comptabilisé pour la demande de copie."),
                    credit_note,
                )
        return result

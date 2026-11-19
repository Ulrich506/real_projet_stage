from odoo import fields, models


class ReceiptPreview(models.TransientModel):
    _name = "etat.civil.receipt.preview"
    _description = "Aperçu de la quittance de versement"

    receipt_id = fields.Many2one(
        "etat.civil.copy.payment", string="Quittance", required=True, readonly=True
    )
    receipt_name = fields.Char(related="receipt_id.name", readonly=True)
    html_content = fields.Html(string="Aperçu de la quittance", readonly=True)

    def action_print_receipt(self):
        """Imprimer la quittance depuis l'aperçu."""
        self.ensure_one()
        return self.receipt_id.action_print_receipt()

    def action_close(self):
        return {"type": "ir.actions.act_window_close"}

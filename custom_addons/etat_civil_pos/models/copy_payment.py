from odoo import fields, models


class EtatCivilCopyPayment(models.Model):
    _inherit = "etat.civil.copy.payment"

    pos_payment_ids = fields.One2many(
        "pos.payment",
        related="pos_payment_move_id.pos_payment_ids",
        string="Lignes de paiement POS",
        readonly=True,
    )

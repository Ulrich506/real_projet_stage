from odoo import fields, models


class EtatCivilDemandeGuichet(models.Model):
    _inherit = "etat.civil.demande.guichet"

    copy_request_ids = fields.One2many(
        "etat.civil.copy.request", "guichet_ticket_id",
        string="Demandes de copie liées", readonly=True,
    )

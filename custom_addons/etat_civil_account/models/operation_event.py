from odoo import fields, models, _
from odoo.exceptions import AccessError


class EtatCivilFinanceEvent(models.Model):
    _name = "etat.civil.finance.event"
    _description = "Historique immuable des demandes de copie"
    _order = "event_date desc, id desc"

    request_id = fields.Many2one(
        "etat.civil.copy.request", required=True, index=True, ondelete="restrict"
    )
    event_type = fields.Selection(
        [
            ("created", "Demande créée"),
            ("submitted", "Demande soumise"), ("invoice", "Facture associée"),
            ("payment_confirmed", "Paiement confirmé"),
            ("authorized", "Délivrance autorisée"),
            ("delivered", "Copie délivrée"), ("cancelled", "Demande annulée"),
        ], required=True,
    )
    event_date = fields.Datetime(required=True, default=fields.Datetime.now, readonly=True)
    user_id = fields.Many2one("res.users", required=True, readonly=True)
    note = fields.Char(readonly=True)
    account_move_id = fields.Many2one("account.move", readonly=True, ondelete="restrict")

    def write(self, vals):
        raise AccessError(_("L'historique financier ne peut pas être modifié."))

    def unlink(self):
        raise AccessError(_("L'historique financier ne peut pas être supprimé."))


from odoo import api, fields, models, _
from odoo.exceptions import AccessError


class TicketPreview(models.TransientModel):
    _name = "etat.civil.ticket.preview"
    _description = "Aperçu du ticket de guichet"

    ticket_id = fields.Many2one(
        "etat.civil.demande.guichet", string="Ticket", required=True, readonly=True
    )
    ticket_numero = fields.Char(related="ticket_id.ticket_numero", readonly=True)
    statut = fields.Selection(related="ticket_id.statut", readonly=True)
    html_content = fields.Html(string="Aperçu du ticket", readonly=True)
    citoyen_nom = fields.Char(readonly=True)
    citoyen_cin = fields.Char(readonly=True)
    type_acte = fields.Selection([
        ("naissance", "Naissance"),
        ("mariage", "Mariage"),
        ("deces", "Décès"),
    ], readonly=True)
    type_demande = fields.Selection([
        ("copie_integrale", "Copie intégrale"),
        ("extrait", "Extrait d'acte"),
        ("declaration_immediate", "Déclaration immédiate"),
    ], readonly=True)
    requester_phone = fields.Char(readonly=True)
    concerned_person_name = fields.Char(readonly=True)
    act_reference = fields.Char(readonly=True)
    copy_quantity = fields.Integer(readonly=True)
    create_date = fields.Datetime(readonly=True)
    create_uid_name = fields.Char(string="Créé par", readonly=True)
    center_id = fields.Many2one("etat.civil.centre", string="Centre", readonly=True)
    service_product_name = fields.Char(string="Prestation", readonly=True)
    unit_price = fields.Float(readonly=True)
    total_amount = fields.Float(readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get("active_id"):
            ticket = self.env["etat.civil.demande.guichet"].browse(self.env.context["active_id"])
            ticket.check_access_rights("read")
            ticket.check_access_rule("read")
            res.update({
                "ticket_id": ticket.id,
                "citoyen_nom": ticket.citoyen_nom,
                "citoyen_cin": ticket.citoyen_cin,
                "type_acte": ticket.type_acte,
                "type_demande": ticket.type_demande,
                "requester_phone": ticket.requester_phone,
                "concerned_person_name": ticket.concerned_person_name,
                "act_reference": ticket.act_reference,
                "copy_quantity": ticket.copy_quantity,
                "create_date": ticket.create_date,
                "create_uid_name": ticket.create_uid.name if ticket.create_uid else "",
                "center_id": ticket.center_id.id if hasattr(ticket, 'center_id') and ticket.center_id else False,
                "service_product_name": ticket.service_product_id.name if hasattr(ticket, 'service_product_id') and ticket.service_product_id else "",
                "unit_price": ticket.service_product_id.list_price if hasattr(ticket, 'service_product_id') and ticket.service_product_id else 0.0,
                "total_amount": (ticket.service_product_id.list_price * ticket.copy_quantity) if hasattr(ticket, 'service_product_id') and ticket.service_product_id else 0.0,
            })
        return res

    def action_print_ticket(self):
        self.ensure_one()
        return self.ticket_id.action_print_ticket()

    def action_download_ticket(self):
        self.ensure_one()
        return self.ticket_id.action_download_ticket()

    def action_close(self):
        return {"type": "ir.actions.act_window_close"}

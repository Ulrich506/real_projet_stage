from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


class EtatCivilCopyTariff(models.Model):
    _name = "etat.civil.copy.tariff"
    _description = "Tarif des copies d'état civil"
    _order = "date_start desc, id desc"

    name = fields.Char(required=True)
    document_type = fields.Selection(
        [("naissance", "Naissance"), ("mariage", "Mariage"), ("deces", "Décès")],
        required=True,
    )
    copy_kind = fields.Selection(
        [("integrale", "Copie intégrale"), ("extrait", "Extrait")], required=True
    )
    product_id = fields.Many2one("product.product", required=True, ondelete="restrict")
    price = fields.Monetary(required=True, currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency", required=True, default=lambda self: self.env.company.currency_id
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    center_id = fields.Many2one("etat.civil.centre", ondelete="restrict")
    first_copy_free = fields.Boolean(
        string="Première copie gratuite", default=False,
        help="Règle métier configurable, à activer après validation par la commune.",
    )
    date_start = fields.Date(required=True, default=fields.Date.context_today)
    date_end = fields.Date()
    active = fields.Boolean(default=True)

    @api.constrains("price", "date_start", "date_end")
    def _check_price_and_period(self):
        for record in self:
            if record.price < 0:
                raise ValidationError(_("Le tarif ne peut pas être négatif."))
            if record.date_end and record.date_end < record.date_start:
                raise ValidationError(_("La fin de validité doit suivre le début."))

    @api.model
    def _for_request(self, document_type, copy_kind, center, date_value):
        domain = [
            ("active", "=", True), ("document_type", "=", document_type),
            ("copy_kind", "=", copy_kind), ("date_start", "<=", date_value),
            "|", ("date_end", "=", False), ("date_end", ">=", date_value),
            ("company_id", "=", self.env.company.id),
            "|", ("center_id", "=", False), ("center_id", "=", center.id),
        ]
        candidates = self.search(domain, order="center_id desc, date_start desc, id desc")
        exact = candidates.filtered(lambda tariff: tariff.center_id == center)
        matches = exact or candidates.filtered(lambda tariff: not tariff.center_id)
        if len(matches) != 1:
            raise ValidationError(_(
                "Un tarif unique doit être configuré pour ce document, ce centre et cette date."
            ))
        return matches

    def write(self, vals):
        if not self.env.user.has_group("etat_civil.group_etat_civil_admin"):
            raise AccessError(_("Seul un administrateur d'état civil peut modifier les tarifs."))
        return super().write(vals)

    def unlink(self):
        if not self.env.user.has_group("etat_civil.group_etat_civil_admin"):
            raise AccessError(_("Seul un administrateur d'état civil peut supprimer un tarif."))
        if self.filtered(lambda tariff: self.env["etat.civil.copy.request"].search_count([
            ("tariff_id", "=", tariff.id),
        ])):
            raise ValidationError(_("Un tarif utilisé doit être archivé, pas supprimé."))
        return super().unlink()


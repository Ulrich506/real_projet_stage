from odoo import api, fields, models
from odoo.osv.expression import AND, OR


class PosConfig(models.Model):
    _inherit = "pos.config"

    @api.model_create_multi
    def create(self, vals_list):
        if "module_pos_restaurant" in self._fields:
            for vals in vals_list:
                vals.setdefault("module_pos_restaurant", False)
        return super().create(vals_list)

    def _get_available_product_domain(self):
        self.ensure_one()
        domain = super()._get_available_product_domain()
        date_today = fields.Date.context_today(self)
        tariffs = self.env["etat.civil.copy.tariff"].sudo().search([
            ("active", "=", True),
            ("company_id", "=", self.company_id.id),
            ("date_start", "<=", date_today),
            "|", ("date_end", "=", False), ("date_end", ">=", date_today),
        ])
        service_products = tariffs.mapped("product_id")
        for xml_id in (
            "etat_civil_pos.product_template_copy_birth_full",
            "etat_civil_pos.product_template_copy_birth_extract",
            "etat_civil_pos.product_template_copy_marriage_full",
            "etat_civil_pos.product_template_copy_marriage_extract",
            "etat_civil_pos.product_template_copy_death_full",
            "etat_civil_pos.product_template_copy_death_extract",
        ):
            template = self.env.ref(xml_id, raise_if_not_found=False)
            if template:
                service_products |= template.product_variant_id

        template = self.env.ref(
            "etat_civil_pos.product_template_copy_payment",
            raise_if_not_found=False,
        )
        service_domain = AND([domain, [("id", "in", service_products.ids)]])
        if not template or not template.product_variant_id.available_in_pos:
            return service_domain
        payment_product_domain = AND([
            self.env["product.product"]._check_company_domain(self.company_id),
            [
                ("id", "=", template.product_variant_id.id),
                ("available_in_pos", "=", True),
                ("sale_ok", "=", True),
            ],
        ])
        return OR([service_domain, payment_product_domain])

    def _get_special_products(self):
        products = super()._get_special_products()
        for xml_id in (
            "etat_civil_pos.product_template_copy_payment",
            "etat_civil_pos.product_template_copy_birth_full",
            "etat_civil_pos.product_template_copy_birth_extract",
            "etat_civil_pos.product_template_copy_marriage_full",
            "etat_civil_pos.product_template_copy_marriage_extract",
            "etat_civil_pos.product_template_copy_death_full",
            "etat_civil_pos.product_template_copy_death_extract",
        ):
            template = self.env.ref(xml_id, raise_if_not_found=False)
            if template:
                products |= template.product_variant_id
        products |= self.env["etat.civil.copy.tariff"].sudo().search([]).mapped(
            "product_id"
        )
        return products


class EtatCivilCopyTariff(models.Model):
    _inherit = "etat.civil.copy.tariff"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("product_id") or not vals.get("document_type") or not vals.get("copy_kind"):
                continue
            suffix = {
                ("naissance", "integrale"): "birth_full",
                ("naissance", "extrait"): "birth_extract",
                ("mariage", "integrale"): "marriage_full",
                ("mariage", "extrait"): "marriage_extract",
                ("deces", "integrale"): "death_full",
                ("deces", "extrait"): "death_extract",
            }.get((vals["document_type"], vals["copy_kind"]))
            if suffix:
                vals["product_id"] = self.env.ref(
                    "etat_civil_pos.product_template_copy_%s" % suffix
                ).product_variant_id.id
        return super().create(vals_list)

    @api.onchange("document_type", "copy_kind")
    def _onchange_document_service_product(self):
        product_suffix = {
            ("naissance", "integrale"): "birth_full",
            ("naissance", "extrait"): "birth_extract",
            ("mariage", "integrale"): "marriage_full",
            ("mariage", "extrait"): "marriage_extract",
            ("deces", "integrale"): "death_full",
            ("deces", "extrait"): "death_extract",
        }.get((self.document_type, self.copy_kind))
        if product_suffix:
            template = self.env.ref(
                "etat_civil_pos.product_template_copy_%s" % product_suffix,
                raise_if_not_found=False,
            )
            if template:
                self.product_id = template.product_variant_id

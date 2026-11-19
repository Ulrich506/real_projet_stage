from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError


_POS_TICKET_TOKEN = object()


class EtatCivilDemandeGuichet(models.Model):
    _inherit = "etat.civil.demande.guichet"

    center_id = fields.Many2one(
        "etat.civil.centre", string="Centre", index=True, ondelete="restrict",
        readonly=True,
    )
    requester_partner_id = fields.Many2one(
        "res.partner", string="Demandeur", readonly=True, ondelete="restrict"
    )
    service_product_id = fields.Many2one(
        "product.product", string="Prestation", readonly=True, ondelete="restrict"
    )
    requester_phone = fields.Char(string="Téléphone du demandeur")
    concerned_person_name = fields.Char(string="Personne concernée")
    act_reference = fields.Char(string="Numéro ou référence de l'acte")
    copy_quantity = fields.Integer(string="Nombre de copies", default=1)
    pos_session_id = fields.Many2one(
        "pos.session", string="Session de caisse", readonly=True, ondelete="restrict"
    )
    pos_request_uuid = fields.Char(
        string="Identifiant de requête POS",
        readonly=True,
        copy=False,
        index=True,
    )

    _sql_constraints = [
        (
            "pos_request_uuid_unique",
            "unique(pos_request_uuid)",
            "Cette requête POS a déjà créé un ticket.",
        ),
        (
            "copy_quantity_positive",
            "CHECK(copy_quantity > 0)",
            "Le nombre de copies doit être supérieur à zéro.",
        ),
    ]

    def _pos_ticket_session(self, session_id):
        user = self.env.user
        if not (
            user.has_group("etat_civil_account.group_etat_civil_regisseur")
            or user.has_group("etat_civil.group_etat_civil_admin")
        ):
            raise AccessError(_("La création de tickets POS est réservée au régisseur."))

        if isinstance(session_id, bool) or not isinstance(session_id, int) or session_id <= 0:
            raise ValidationError(_("La session de caisse indiquée est invalide."))
        session = self.env["pos.session"].sudo().browse(session_id).exists()
        if not session or session.state != "opened":
            raise UserError(_("Une session de caisse ouverte est nécessaire."))
        if session.company_id not in user.company_ids:
            raise AccessError(_("Vous n'êtes pas autorisé à utiliser cette société."))
        return session

    @api.model_create_multi
    def create(self, vals_list):
        if (
            self.env.user.has_group("etat_civil_account.group_etat_civil_regisseur")
            and self.env.context.get("etat_civil_pos_ticket_token")
            is not _POS_TICKET_TOKEN
        ):
            raise AccessError(
                _("Les régisseurs doivent créer les tickets depuis une session POS ouverte.")
            )
        return super().create(vals_list)

    def write(self, vals):
        protected_fields = {
            "center_id",
            "requester_partner_id",
            "service_product_id",
            "pos_session_id",
            "pos_request_uuid",
            "citoyen_nom",
            "citoyen_cin",
            "requester_phone",
            "concerned_person_name",
            "act_reference",
            "type_acte",
            "type_demande",
        }
        if protected_fields.intersection(vals) and any(self.mapped("pos_request_uuid")):
            raise UserError(
                _("Les données du ticket POS sont conservées telles qu'enregistrées.")
            )
        return super().write(vals)

    @api.model
    def pos_get_available_centers(self, session_id):
        self._pos_ticket_session(session_id)
        if self.env.user.has_group("etat_civil.group_etat_civil_admin"):
            centers = self.env["etat.civil.centre"].sudo().search([])
        else:
            centers = self.env.user.etat_civil_centre_ids
        if not centers:
            raise UserError(_("Aucun centre n'est affecté à votre compte."))
        return [
            {"id": center.id, "label": center.display_name}
            for center in centers.sudo().sorted("nom_centre")
        ]

    @api.model
    def pos_create_ticket(self, session_id, values):
        session = self._pos_ticket_session(session_id)
        user = self.env.user
        if not isinstance(values, dict):
            raise ValidationError(_("Les informations du ticket sont invalides."))

        request_uuid = values.get("request_uuid")
        if not isinstance(request_uuid, str) or not request_uuid.strip():
            raise ValidationError(_("L'identifiant de la requête POS est obligatoire."))
        request_uuid = request_uuid.strip()
        if len(request_uuid) > 128:
            raise ValidationError(_("L'identifiant de la requête POS est trop long."))

        existing = self.sudo().search(
            [("pos_request_uuid", "=", request_uuid)], limit=1
        )
        if existing:
            existing_center_id = existing.center_id.id if existing.center_id else False
            if (
                existing.create_uid != user
                or existing.pos_session_id != session
                or existing_center_id != values.get("center_id")
                or existing.citoyen_nom != values.get("requester_name")
                or existing.requester_phone != (values.get("phone") or "")
                or existing.concerned_person_name != values.get("person_name")
                or existing.act_reference != (values.get("act_reference") or "")
                or existing.type_acte != values.get("document_type")
                or existing.type_demande != values.get("copy_kind")
                or existing.copy_quantity != values.get("copy_quantity")
            ):
                raise ValidationError(
                    _("Cette requête POS existe déjà avec des informations différentes.")
                )
            return {"id": existing.id, "ticket_number": existing.ticket_numero}

        center_id = values.get("center_id")
        if isinstance(center_id, bool) or not isinstance(center_id, int) or center_id <= 0:
            raise ValidationError(_("Le centre indiqué est invalide."))
        center = self.env["etat.civil.centre"].sudo().browse(center_id).exists()
        if not center or (
            not user.has_group("etat_civil.group_etat_civil_admin")
            and center not in user.etat_civil_centre_ids
        ):
            raise AccessError(_("Ce centre ne fait pas partie de vos centres affectés."))

        requester_name = values.get("requester_name")
        person_name = values.get("person_name")
        phone = values.get("phone") or ""
        act_reference = values.get("act_reference") or ""
        document_type = values.get("document_type")
        copy_kind = values.get("copy_kind")
        quantity = values.get("copy_quantity")
        if not isinstance(requester_name, str) or not requester_name.strip():
            raise ValidationError(_("Le nom du demandeur est obligatoire."))
        if not isinstance(person_name, str) or not person_name.strip():
            raise ValidationError(_("Le nom de la personne concernée est obligatoire."))
        if not isinstance(phone, str) or len(phone) > 64:
            raise ValidationError(_("Le numéro de téléphone est invalide."))
        if not isinstance(act_reference, str) or len(act_reference) > 128:
            raise ValidationError(_("La référence de l'acte est trop longue."))
        if document_type not in ("naissance", "mariage", "deces"):
            raise ValidationError(_("Le type d'acte sélectionné est invalide."))
        if copy_kind not in ("copie_integrale", "extrait"):
            raise ValidationError(_("Le format de copie sélectionné est invalide."))
        if (
            isinstance(quantity, bool)
            or not isinstance(quantity, int)
            or quantity <= 0
            or quantity > 2_147_483_647
        ):
            raise ValidationError(_("Le nombre de copies doit être un entier positif."))

        product_suffix = {
            ("naissance", "copie_integrale"): "birth_full",
            ("naissance", "extrait"): "birth_extract",
            ("mariage", "copie_integrale"): "marriage_full",
            ("mariage", "extrait"): "marriage_extract",
            ("deces", "copie_integrale"): "death_full",
            ("deces", "extrait"): "death_extract",
        }[(document_type, copy_kind)]
        service_product = self.env.ref(
            "etat_civil_pos.product_template_copy_%s" % product_suffix
        ).product_variant_id
        partner_model = self.env["res.partner"].sudo()
        requester = partner_model.browse()
        if phone.strip():
            requester = partner_model.search([
                ("name", "=", requester_name.strip()),
                ("phone", "=", phone.strip()),
                ("company_id", "=", False),
            ], limit=1)
        if not requester:
            requester = partner_model.create({
                "name": requester_name.strip(),
                "phone": phone.strip() or False,
                "company_id": False,
            })
        ticket = self.sudo().with_context(
            etat_civil_pos_ticket_token=_POS_TICKET_TOKEN
        ).create({
            "citoyen_nom": requester_name.strip(),
            "type_acte": document_type,
            "type_demande": copy_kind,
            "center_id": center.id,
            "requester_partner_id": requester.id,
            "service_product_id": service_product.id,
            "requester_phone": phone.strip(),
            "concerned_person_name": person_name.strip(),
            "act_reference": act_reference.strip(),
            "copy_quantity": quantity,
            "pos_session_id": session.id,
            "pos_request_uuid": request_uuid,
        })
        return {"id": ticket.id, "ticket_number": ticket.ticket_numero}

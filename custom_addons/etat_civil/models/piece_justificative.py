from markupsafe import Markup, escape

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


_PROCEDURE_TOKEN = object()

PIECE_TYPES = [
    ("declaration_hopital", "Déclaration de l’hôpital"),
    ("livret_famille", "Livret de famille"),
    ("residence_parent", "Certificat de résidence du parent"),
    ("cin_parent", "Photocopie CIN du parent"),
    ("celibat_conjoint_1", "Certificat de célibat du premier conjoint"),
    ("celibat_conjoint_2", "Certificat de célibat du second conjoint"),
    ("cin_conjoint_1", "Photocopie CIN du premier conjoint"),
    ("cin_conjoint_2", "Photocopie CIN du second conjoint"),
    ("cin_temoin_1", "Photocopie CIN du premier témoin"),
    ("cin_temoin_2", "Photocopie CIN du second témoin"),
    ("residence_conjoint_1", "Certificat de résidence du premier conjoint"),
    ("residence_conjoint_2", "Certificat de résidence du second conjoint"),
    ("residence_temoin_1", "Certificat de résidence du premier témoin"),
    ("residence_temoin_2", "Certificat de résidence du second témoin"),
    ("capacite_mariage_1", "Autorisation de capacité de mariage du premier conjoint"),
    ("capacite_mariage_2", "Autorisation de capacité de mariage du second conjoint"),
    ("passeport_1", "Passeport du premier conjoint étranger"),
    ("passeport_2", "Passeport du second conjoint étranger"),
    ("residence_etranger_1", "Certificat de résidence du premier conjoint étranger"),
    ("residence_etranger_2", "Certificat de résidence du second conjoint étranger"),
    ("cin_pere_reconnaissant", "Photocopie CIN du père reconnaissant"),
    ("residence_pere_reconnaissant", "Certificat de résidence du père reconnaissant"),
    ("lettre_fokontany_reconnaissance", "Lettre authentique du chef fokontany"),
    ("cin_enfant_majeur", "Photocopie CIN de l’enfant majeur"),
    ("residence_enfant_majeur", "Certificat de résidence de l’enfant majeur"),
    ("lettre_accord_famille", "Lettre d’accord de la famille"),
    ("lettre_fokontany_adoption", "Lettre authentique du chef fokontany"),
    ("cin_adoptant", "Photocopie CIN du parent adoptant"),
    ("residence_adoptant", "Certificat de résidence du parent adoptant"),
    ("cin_declarant_deces", "Photocopie CIN du déclarant du décès"),
    ("residence_declarant_deces", "Certificat de résidence du déclarant du décès"),
]


class EtatCivilPieceJustificative(models.Model):
    _name = "etat.civil.piece.justificative"
    _description = "Pièce justificative d’état civil"
    _inherit = ["mail.thread"]
    _order = "obligatoire desc, id"

    name = fields.Selection(PIECE_TYPES, string="Document", required=True)
    obligatoire = fields.Boolean(string="Obligatoire", default=True, readonly=True)
    etat = fields.Selection(
        [
            ("a_fournir", "À fournir"),
            ("recu", "Reçu"),
            ("verifie", "Reçu et vérifié"),
        ],
        string="État",
        required=True,
        default="a_fournir",
    )
    recu_par_id = fields.Many2one(
        "res.users", string="Réception enregistrée par", readonly=True, copy=False
    )
    date_reception = fields.Datetime(
        string="Date de réception", readonly=True, copy=False
    )
    verifie_par_id = fields.Many2one(
        "res.users", string="Vérification enregistrée par", readonly=True, copy=False
    )
    date_verification = fields.Datetime(
        string="Date de vérification", readonly=True, copy=False
    )
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "etat_civil_piece_attachment_rel",
        "piece_id",
        "attachment_id",
        string="Photos ou scans (facultatifs)",
    )
    acte_naissance_id = fields.Many2one(
        "etat.civil.acte.naissance", ondelete="cascade", index=True
    )
    acte_mariage_id = fields.Many2one(
        "etat.civil.acte.mariage", ondelete="cascade", index=True
    )
    acte_deces_id = fields.Many2one(
        "etat.civil.acte.deces", ondelete="cascade", index=True
    )
    mention_id = fields.Many2one(
        "etat.civil.mention.marginale", ondelete="cascade", index=True
    )

    @api.constrains(
        "acte_naissance_id",
        "acte_mariage_id",
        "acte_deces_id",
        "mention_id",
        "name",
        "etat",
    )
    def _check_owner_and_state(self):
        for record in self:
            owners = [
                record.acte_naissance_id,
                record.acte_mariage_id,
                record.acte_deces_id,
                record.mention_id,
            ]
            if sum(bool(owner) for owner in owners) != 1:
                raise ValidationError(
                    "Une pièce justificative doit appartenir à un seul dossier."
                )
            if record.etat == "verifie":
                if not record.obligatoire and not record.name:
                    raise ValidationError("Sélectionnez le document vérifié.")
            owner_field = next(
                (
                    field_name
                    for field_name, owner in zip(
                        (
                            "acte_naissance_id",
                            "acte_mariage_id",
                            "acte_deces_id",
                            "mention_id",
                        ),
                        owners,
                    )
                    if owner
                ),
                None,
            )
            if owner_field and record.name:
                duplicate = self.search(
                    [
                        (owner_field, "=", record[owner_field].id),
                        ("name", "=", record.name),
                        ("id", "!=", record.id),
                    ],
                    limit=1,
                )
                if duplicate:
                    raise ValidationError(
                        "Ce document figure déjà dans la liste du dossier."
                    )

    def _ensure_owner_mutable(self, vals, owner_values=None):
        if self.env.context.get("etat_civil_bulk_piece_receive"):
            user = self.env.user
            if not (
                self.env.su
                or user.has_group("etat_civil.group_etat_civil_agent")
                or user.has_group("etat_civil.group_etat_civil_officier")
                or user._is_etat_civil_admin()
            ):
                raise AccessError("Seul un agent, un officier ou un administrateur peut recevoir les pièces.")
            return
        if self.env.su or self.env.user.has_group("base.group_system"):
            return
        owner_values = owner_values or vals
        owner_fields = (
            "acte_naissance_id",
            "acte_mariage_id",
            "acte_deces_id",
            "mention_id",
        )
        records = [(record, owner_values) for record in self] if self else [
            (False, owner_values)
        ]
        for record, values in records:
            owner = False
            for field_name in owner_fields:
                owner_id = values.get(
                    field_name,
                    record[field_name].id if record else False,
                )
                if owner_id:
                    owner = self.env[self._fields[field_name].comodel_name].browse(
                        owner_id
                    ).exists()
                    break
            if not owner:
                raise ValidationError(
                    "La pièce justificative doit être liée à un dossier existant."
                )

            if owner._name == "etat.civil.mention.marginale":
                owner._ensure_officier()
                owner._ensure_competence_territoriale()
                if owner.statut != "brouillon":
                    raise UserError(
                        "Les pièces d'une mention validée ne peuvent plus être modifiées."
                    )
                continue

            owner._ensure_competence_territoriale()
            if owner.statut in ("brouillon", "a_corriger"):
                owner._ensure_agent()
                if values.get("etat", record.etat if record else "a_fournir") == "verifie":
                    raise AccessError(
                        "Seul l'officier désigné peut vérifier une pièce justificative."
                    )
            elif owner.statut == "en_attente":
                owner._ensure_officier()
                owner._ensure_officier_responsable()
                if record and set(vals) - {"etat"}:
                    raise UserError(
                        "Les pièces d'un acte en attente ne peuvent être modifiées "
                        "que pour enregistrer leur vérification."
                    )
            else:
                raise UserError(
                    "Les pièces d'un acte traité ou archivé ne peuvent plus être modifiées."
                )

    @api.model_create_multi
    def _create_required(self, vals_list):
        return self.with_context(
            etat_civil_piece_procedure_token=_PROCEDURE_TOKEN
        ).create(vals_list)

    def _set_required_from_procedure(self, required):
        return self.with_context(
            etat_civil_piece_procedure_token=_PROCEDURE_TOKEN
        ).write({"obligatoire": required})

    @api.model_create_multi
    def create(self, vals_list):
        if (
            self.env.context.get("etat_civil_piece_procedure_token")
            is not _PROCEDURE_TOKEN
        ):
            for vals in vals_list:
                self._ensure_owner_mutable(vals, vals)
        if any(vals.get("etat") == "verifie" for vals in vals_list):
            self._ensure_verificateur()
        unique_vals_list = []
        merged_records = self.browse()
        owner_fields = (
            "acte_naissance_id",
            "acte_mariage_id",
            "acte_deces_id",
            "mention_id",
        )
        for vals in vals_list:
            owner_field = next((name for name in owner_fields if vals.get(name)), None)
            name = vals.get("name")
            if owner_field and name:
                duplicate = self.search([
                    (owner_field, "=", vals[owner_field]),
                    ("name", "=", name),
                ], limit=1)
                if duplicate:
                    attachment_ids = vals.get("attachment_ids")
                    if attachment_ids:
                        duplicate.write({"attachment_ids": attachment_ids})
                    merged_records |= duplicate
                    continue
            unique_vals_list.append(vals)
        if not unique_vals_list:
            return merged_records
        records = super().create(unique_vals_list)
        owner_fields = (
            "acte_naissance_id",
            "acte_mariage_id",
            "acte_deces_id",
            "mention_id",
        )
        for record in records:
            owner_field = next(
                (field_name for field_name in owner_fields if record[field_name]),
                None,
            )
            if owner_field and record.name:
                record._set_required_from_procedure(
                    record.name in record[owner_field]._required_piece_codes()
                )
        (records | merged_records)._normalize_attachment_metadata()
        return records | merged_records

    def _normalize_attachment_metadata(self):
        """Associate linked attachments with this piece for ir.attachment ACL checks."""
        for piece in self.sudo():
            for attachment in piece.attachment_ids.sudo():
                if (
                    attachment.res_model != self._name
                    or attachment.res_id != piece.id
                ):
                    attachment.sudo().write({
                        "res_model": self._name,
                        "res_id": piece.id,
                    })

    @api.model
    def _register_hook(self):
        super()._register_hook()
        self.sudo().search([])._normalize_attachment_metadata()

    def write(self, vals):
        vals = dict(vals)
        if (
            self.env.context.get("etat_civil_piece_procedure_token")
            is _PROCEDURE_TOKEN
        ):
            return super().write(vals)
        if {
            "recu_par_id",
            "date_reception",
            "verifie_par_id",
            "date_verification",
        } & vals.keys():
            raise AccessError(
                "Les informations de traçabilité des pièces sont gérées automatiquement."
            )
        self._ensure_owner_mutable(vals)
        if vals.get("etat") == "verifie":
            self._ensure_verificateur()
        if "obligatoire" in vals:
            raise AccessError(
                "Le caractère obligatoire d'une pièce est déterminé par la procédure."
            )

        old_states = {}
        changed = self.browse()
        if "etat" in vals:
            self.flush_recordset(["etat"])
            ids = tuple(sorted(self.ids))
            self.env.cr.execute(
                f'SELECT id, etat FROM "{self._table}" WHERE id IN %s ORDER BY id FOR UPDATE',
                [ids],
            )
            old_states = dict(self.env.cr.fetchall())
            self.invalidate_recordset(["etat"])
            self._ensure_owner_mutable(vals)
            if vals.get("etat") == "verifie":
                self._ensure_verificateur()
            changed = self.filtered(
                lambda piece: old_states.get(piece.id) != vals["etat"]
            )

        unchanged = self - changed
        if unchanged:
            unchanged_vals = dict(vals)
            if "etat" in unchanged_vals:
                unchanged_vals.pop("etat")
            if unchanged_vals:
                super(EtatCivilPieceJustificative, unchanged).write(unchanged_vals)

        if changed:
            transition_vals = dict(vals)
            transition_time = fields.Datetime.now()
            if vals["etat"] == "recu":
                transition_vals.update({
                    "recu_par_id": self.env.uid,
                    "date_reception": transition_time,
                })
            elif vals["etat"] == "verifie":
                transition_vals.update({
                    "verifie_par_id": self.env.uid,
                    "date_verification": transition_time,
                })
            super(EtatCivilPieceJustificative, changed).write(transition_vals)

        if "name" in vals or any(
            field_name in vals
            for field_name in (
                "acte_naissance_id",
                "acte_mariage_id",
                "acte_deces_id",
                "mention_id",
            )
        ):
            for record in self:
                owner = next(
                    (
                        record[field_name]
                        for field_name in (
                            "acte_naissance_id",
                            "acte_mariage_id",
                            "acte_deces_id",
                            "mention_id",
                        )
                        if record[field_name]
                    ),
                    False,
                )
                record._set_required_from_procedure(
                    bool(owner and record.name in owner._required_piece_codes())
                )
        if "attachment_ids" in vals:
            self._normalize_attachment_metadata()
        return True

    def _log_state_transition(self, old_state, new_state):
        labels = dict(self._fields["etat"].selection)
        if self.env.user._is_etat_civil_admin():
            role = "Administrateur d'état civil"
        elif self.env.user.has_group("etat_civil.group_etat_civil_officier"):
            role = "Officier compétent"
        elif self.env.user.has_group("etat_civil.group_etat_civil_agent"):
            role = "Agent"
        else:
            role = "Système"
        body = Markup(
            "<p>Pièce <strong>{}</strong> : état modifié de <strong>{}</strong> "
            "à <strong>{}</strong> par {} ({}, ID {}).</p>"
        ).format(
            escape(self.display_name),
            escape(labels.get(old_state, old_state)),
            escape(labels.get(new_state, new_state)),
            escape(self.env.user.display_name),
            escape(role),
            self.env.uid,
        )
        owner = (
            self.acte_naissance_id
            or self.acte_mariage_id
            or self.acte_deces_id
        )
        thread = owner if owner else self
        thread.message_post(
            body=body,
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )

    def action_mark_received(self):
        self.ensure_one()
        self._ensure_owner_mutable({"etat": "recu"})
        if self.etat == "recu":
            return True
        if self.etat != "a_fournir":
            raise UserError("Seule une pièce à fournir peut être marquée reçue.")
        return self.write({"etat": "recu"})

    def action_mark_verified(self):
        self.ensure_one()
        self._ensure_owner_mutable({"etat": "verifie"})
        self._ensure_verificateur()
        if self.etat == "verifie":
            return True
        if self.etat != "recu":
            raise UserError("Une pièce doit être reçue avant d'être vérifiée.")
        return self.write({"etat": "verifie"})

    def _ensure_verificateur(self):
        if not (
            self.env.user.has_group("etat_civil.group_etat_civil_officier")
            or self.env.user._is_etat_civil_admin()
            or self.env.user.has_group("base.group_system")
        ):
            raise AccessError(
                "Seul un officier ou un administrateur d'état civil peut vérifier une pièce justificative."
            )

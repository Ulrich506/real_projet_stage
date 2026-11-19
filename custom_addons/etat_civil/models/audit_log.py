import hashlib
import ipaddress
import json
import re
import uuid

import pytz

from odoo import api, fields, models, _
from odoo.exceptions import AccessError
from odoo.http import request


_AUDIT_CREATE_TOKEN = object()
_SAFE_VALUE_KEYS = {
    "statut",
    "state",
    "etat",
    "payment_state",
    "amount",
    "refund_amount",
    "currency_id",
    "format",
    "file_format",
    "language",
    "rows",
    "field_count",
    "role",
    "finance_event_type",
    "related_id",
}


class EtatCivilAuditLog(models.Model):
    _name = "etat.civil.audit.log"
    _description = "Journal central d'audit de l'état civil"
    _order = "event_datetime_utc desc, id desc"
    _sql_constraints = [
        (
            "event_uuid_unique",
            "unique(event_uuid)",
            "La référence d'un événement d'audit doit être unique.",
        ),
    ]

    event_uuid = fields.Char(
        string="Référence de l'événement", required=True, readonly=True, index=True
    )
    event_datetime_utc = fields.Datetime(
        string="Date et heure UTC",
        required=True,
        readonly=True,
        index=True,
        default=fields.Datetime.now,
    )
    event_datetime_local = fields.Char(
        string="Date et heure locale", required=True, readonly=True
    )
    event_timezone = fields.Char(string="Fuseau horaire", required=True, readonly=True)
    user_id = fields.Many2one(
        "res.users", string="Utilisateur", readonly=True, ondelete="set null", index=True
    )
    user_login = fields.Char(string="Identifiant de connexion", readonly=True, index=True)
    role = fields.Char(string="Rôle au moment de l'action", readonly=True, index=True)
    centre_id = fields.Many2one(
        "etat.civil.centre",
        string="Centre",
        readonly=True,
        ondelete="set null",
        index=True,
    )
    commune = fields.Char(string="Commune", readonly=True, index=True)
    action_type = fields.Selection(
        [
            ("login", "Connexion"),
            ("logout", "Déconnexion"),
            ("create", "Création"),
            ("update", "Modification"),
            ("delete", "Suppression"),
            ("sensitive_read", "Consultation sensible"),
            ("download", "Téléchargement"),
            ("print", "Impression"),
            ("export", "Exportation"),
            ("import", "Importation"),
            ("transmit", "Transmission"),
            ("validate", "Validation"),
            ("sign", "Signature"),
            ("return_correction", "Retour en correction"),
            ("reject", "Refus"),
            ("cancel", "Annulation"),
            ("rectify", "Rectification"),
            ("archive", "Archivage"),
            ("copy_request", "Demande de copie"),
            ("payment", "Paiement"),
            ("refund", "Remboursement"),
            ("delivery", "Délivrance"),
            ("user_created", "Création de compte utilisateur"),
            ("role_changed", "Changement de rôle utilisateur"),
            ("identity_locked", "Verrouillage de l'identité"),
            ("identity_unlocked", "Déverrouillage de l'identité"),
            ("other", "Autre opération"),
        ],
        string="Type d'action",
        required=True,
        readonly=True,
        index=True,
    )
    record_model = fields.Char(string="Modèle concerné", readonly=True, index=True)
    record_id = fields.Integer(string="Identifiant de l'enregistrement", readonly=True, index=True)
    changed_fields = fields.Text(string="Champs modifiés", readonly=True)
    old_values = fields.Text(string="Anciennes valeurs", readonly=True)
    new_values = fields.Text(string="Nouvelles valeurs", readonly=True)
    details = fields.Text(string="Détails complémentaires", readonly=True)
    ip_address = fields.Char(string="Adresse IP", readonly=True)
    session_hash = fields.Char(string="Empreinte de session", readonly=True)
    request_id = fields.Char(string="Identifiant de requête", readonly=True, index=True)
    result = fields.Selection(
        [
            ("success", "Réussi"),
            ("partial", "Partiel"),
            ("failed", "Échec"),
        ],
        string="Résultat",
        required=True,
        readonly=True,
        default="success",
    )

    @api.model
    def _record_event(
        self,
        action_type,
        record=None,
        record_model=None,
        record_id=None,
        centre_id=None,
        commune=None,
        changed_fields=None,
        old_values=None,
        new_values=None,
        details=None,
        result="success",
        user_id=None,
        event_datetime_utc=None,
        ip_address=None,
        session_hash=None,
        request_id=None,
    ):
        actor = self.env["res.users"].sudo().browse(user_id or self.env.uid).exists()
        if record:
            record.ensure_one()
            record_model = record._name
            record_id = record.id
            centre = self._find_centre(record)
            if centre:
                centre_id = centre.id
                commune = centre.commune

        if not centre_id:
            centres = actor.etat_civil_centre_ids
            if len(centres) == 1:
                centre_id = centres.id
                commune = centres.commune
        if centre_id and not commune:
            centre = self.env["etat.civil.centre"].sudo().browse(centre_id).exists()
            commune = centre.commune if centre else False

        event_datetime_utc = event_datetime_utc or fields.Datetime.now()
        timezone_name = actor.tz or "UTC"
        timezone = pytz.timezone(timezone_name)
        utc_datetime = fields.Datetime.to_datetime(event_datetime_utc).replace(
            tzinfo=pytz.UTC
        )
        local_datetime = utc_datetime.astimezone(timezone).strftime("%Y-%m-%d %H:%M:%S")
        role = self._role_for_user(actor)
        request_metadata = self._request_metadata()

        values = {
            "event_uuid": uuid.uuid4().hex,
            "event_datetime_utc": event_datetime_utc,
            "event_datetime_local": local_datetime,
            "event_timezone": timezone_name,
            "user_id": actor.id,
            "user_login": actor.login,
            "role": role,
            "centre_id": centre_id,
            "commune": commune,
            "action_type": action_type,
            "record_model": record_model,
            "record_id": record_id,
            "changed_fields": self._json_value(sorted(set(changed_fields or []))),
            "old_values": self._json_value(self._safe_values(old_values)),
            "new_values": self._json_value(self._safe_values(new_values)),
            "details": self._json_value(self._safe_values(details)),
            "ip_address": ip_address or request_metadata.get("ip_address"),
            "session_hash": session_hash or request_metadata.get("session_hash"),
            "request_id": request_id or request_metadata.get("request_id"),
            "result": result,
        }
        return self.sudo().with_context(
            etat_civil_audit_create_token=_AUDIT_CREATE_TOKEN
        ).create(values)

    @api.model
    def _find_centre(self, record, visited=None):
        if not record or len(record) != 1:
            return self.env["etat.civil.centre"]
        visited = visited or set()
        key = (record._name, record.id)
        if key in visited:
            return self.env["etat.civil.centre"]
        visited.add(key)
        if record._name == "etat.civil.centre":
            return record
        for field_name in (
            "centre_id",
            "center_id",
            "registre_id",
            "request_id",
            "acte_naissance_id",
            "acte_mariage_id",
            "acte_deces_id",
            "mention_id",
        ):
            if field_name in record._fields:
                related = record[field_name]
                if related:
                    centre = self._find_centre(related, visited)
                    if centre:
                        return centre
        return self.env["etat.civil.centre"]

    @api.model
    def _role_for_user(self, user):
        for xmlid, role_name in (
            ("etat_civil.group_etat_civil_admin", "Administrateur d'état civil"),
            ("etat_civil.group_etat_civil_officier", "Officier d'état civil"),
            ("etat_civil.group_etat_civil_agent", "Agent d'état civil"),
            ("etat_civil_account.group_etat_civil_regisseur", "Régisseur"),
            ("base.group_system", "Administrateur Odoo"),
        ):
            group = self.env.ref(xmlid, raise_if_not_found=False)
            if group and group in user.groups_id:
                return role_name
        return "Autre"

    @api.model
    def _request_metadata(self):
        try:
            http_request = request.httprequest
        except RuntimeError:
            return {}

        metadata = {}
        remote_addr = http_request.remote_addr
        if remote_addr:
            try:
                metadata["ip_address"] = str(ipaddress.ip_address(remote_addr))
            except ValueError:
                metadata["ip_address"] = False

        session_id = getattr(request.session, "sid", None)
        if session_id:
            metadata["session_hash"] = hashlib.sha256(
                session_id.encode("utf-8")
            ).hexdigest()

        correlation_id = http_request.environ.get("HTTP_X_REQUEST_ID", "")
        if re.fullmatch(r"[A-Za-z0-9._-]{1,128}", correlation_id):
            metadata["request_id"] = correlation_id
        return metadata

    @api.model
    def _safe_values(self, values):
        if not isinstance(values, dict):
            return {}
        safe = {}
        for key, value in values.items():
            if key not in _SAFE_VALUE_KEYS:
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                safe[key] = value[:128] if isinstance(value, str) else value
        return safe

    @api.model
    def _json_value(self, value):
        if not value:
            return False
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    @api.model_create_multi
    def create(self, vals_list):
        if (
            self.env.context.get("etat_civil_audit_create_token")
            is not _AUDIT_CREATE_TOKEN
        ):
            raise AccessError(_("Les événements d'audit ne peuvent être créés que par le système."))
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(_("Un événement d'audit est immuable et ne peut pas être modifié."))

    def unlink(self):
        raise AccessError(_("Un événement d'audit est immuable et ne peut pas être supprimé."))


class EtatCivilAuditMixin(models.AbstractModel):
    _name = "etat.civil.audit.mixin"
    _description = "Traçabilité des enregistrements d'état civil"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        audit_log = self.env["etat.civil.audit.log"]
        for record in records:
            audit_log._record_event("create", record=record)
        return records

    def write(self, vals):
        audit_log = self.env["etat.civil.audit.log"]
        before = {
            record.id: record._audit_state_values()
            for record in self
        }
        result = super().write(vals)
        for record in self:
            old_values = before.get(record.id, {})
            new_values = record._audit_state_values()
            audit_log._record_event(
                "update",
                record=record,
                changed_fields=list(vals),
                old_values=old_values,
                new_values=new_values,
            )
        return result

    def unlink(self):
        audit_log = self.env["etat.civil.audit.log"]
        event_values = [
            (
                record.id,
                audit_log._find_centre(record),
                record._audit_state_values(),
            )
            for record in self
        ]
        result = super().unlink()
        for record_id, centre, old_values in event_values:
            audit_log._record_event(
                "delete",
                record_model=self._name,
                record_id=record_id,
                centre_id=centre.id if centre else False,
                commune=centre.commune if centre else False,
                old_values=old_values,
            )
        return result

    def _audit_state_values(self):
        state_fields = ("statut", "state", "etat", "payment_state")
        return {
            field_name: self[field_name]
            for field_name in state_fields
            if field_name in self._fields and self[field_name]
        }

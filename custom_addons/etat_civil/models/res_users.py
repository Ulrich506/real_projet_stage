import logging

from odoo import SUPERUSER_ID, api, fields, models


_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        audit_log = self.env["etat.civil.audit.log"]
        for user, vals in zip(users, vals_list):
            if "groups_id" in vals:
                role = audit_log._role_for_user(user)
                if role != "Autre":
                    audit_log._record_event(
                        "create",
                        record_model="res.users",
                        record_id=user.id,
                        new_values={"role": role},
                    )
        return users

    def write(self, vals):
        audited_fields = {"groups_id", "etat_civil_centre_ids", "active", "login"}
        fields_changed = audited_fields.intersection(vals)
        previous_roles = {}
        if fields_changed:
            audit_log = self.env["etat.civil.audit.log"]
            previous_roles = {
                user.id: audit_log._role_for_user(user)
                for user in self
            }
        result = super().write(vals)
        if fields_changed:
            for user in self:
                audit_log._record_event(
                    "update",
                    record_model="res.users",
                    record_id=user.id,
                    changed_fields=sorted(fields_changed),
                    old_values={"role": previous_roles[user.id]},
                    new_values={"role": audit_log._role_for_user(user)},
                )
        return result

    @classmethod
    def _login(cls, db, login, password, user_agent_env):
        user_id = super()._login(db, login, password, user_agent_env)
        if user_id:
            try:
                with cls.pool.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    env["etat.civil.audit.log"]._record_event(
                        "login",
                        user_id=user_id,
                    )
                    cr.commit()
            except Exception:
                _logger.exception(
                    "Failed to record successful civil-registry login audit event "
                    "for user id %s",
                    user_id,
                )
        return user_id

    etat_civil_role = fields.Selection(
        [
            ("admin", "Administrateur d'état civil"),
            ("officier", "Officier d'état civil"),
            ("agent", "Agent d'état civil"),
            ("system", "Administrateur Odoo"),
            ("other", "Autre"),
        ],
        string="Rôle",
        compute="_compute_etat_civil_role",
        store=True,
        readonly=True,
    )

    etat_civil_centre_ids = fields.Many2many(
        "etat.civil.centre",
        "etat_civil_user_centre_rel",
        "user_id",
        "centre_id",
        string="Centres d'état civil autorisés",
        help=(
            "Centres auxquels cet utilisateur est affecté pour les opérations "
            "d'état civil. Les agents et officiers ne peuvent travailler que "
            "dans les centres de leur périmètre."
        ),
    )

    def _is_etat_civil_admin(self):
        return self.has_group("etat_civil.group_etat_civil_admin")

    @api.depends("groups_id", "share")
    def _compute_etat_civil_role(self):
        role_groups = {
            role: self.env.ref(xmlid, raise_if_not_found=False)
            for role, xmlid in (
                ("admin", "etat_civil.group_etat_civil_admin"),
                ("officier", "etat_civil.group_etat_civil_officier"),
                ("agent", "etat_civil.group_etat_civil_agent"),
                ("system", "base.group_system"),
            )
        }
        for user in self:
            user_groups = user.groups_id
            user.etat_civil_role = next(
                (
                    role
                    for role in ("admin", "officier", "agent", "system")
                    if role_groups[role] and role_groups[role] in user_groups
                ),
                "other",
            )

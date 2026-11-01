from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

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

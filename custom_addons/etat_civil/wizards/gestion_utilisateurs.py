from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


# Rôles métiers du module État Civil selon le workflow opérationnel :
# - Agent : crée et prépare les actes d'état civil.
# - Officier : valide et signe officiellement les actes créés.
# - Régisseur : gère le POS, encaisse et imprime les quittances.
# - Administrateur : accède aux actions Agent et Officier et gère le module.
_CIVIL_ROLE_REFS = (
    "etat_civil.group_etat_civil_agent",
    "etat_civil.group_etat_civil_officier",
    "etat_civil_account.group_etat_civil_regisseur",
    "etat_civil.group_etat_civil_admin",
)


class EtatCivilGestionUtilisateur(models.TransientModel):
    _name = "etat.civil.gestion.utilisateur"
    _description = "Gestion des comptes État Civil"

    mode = fields.Selection(
        [("create", "Créer un compte"), ("edit", "Gérer un compte")],
        required=True,
        default="create",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Compte interne",
        domain=[("share", "=", False)],
    )
    name = fields.Char(string="Nom complet")
    login = fields.Char(string="Identifiant")
    email = fields.Char(string="Adresse e-mail")
    role = fields.Selection(
        [
            ("agent", "Agent d'état civil"),
            ("officier", "Officier d'état civil"),
            ("regisseur", "Régisseur"),
            ("admin", "Administrateur d'état civil"),
        ],
        string="Rôle État Civil",
        help=(
            "Workflow métier proposé :\n"
            "- Agent : crée les actes et les dossiers ;\n"
            "- Officier : valide et signe les actes ;\n"
            "- Régisseur : gère le POS, encaisse et imprime les quittances ;\n"
            "- Administrateur : accède aux fonctions Agent et Officier, "
            "gère les référentiels et les comptes."
        ),
        required=True,
        default="agent",
    )
    new_user_role = fields.Selection(
        [
            ("agent", "Agent d'état civil"),
            ("officier", "Officier d'état civil"),
            ("regisseur", "Régisseur"),
            ("admin", "Administrateur d'état civil"),
        ],
        string="Rôle du nouveau compte",
        required=True,
        default="agent",
    )
    password = fields.Char(string="Mot de passe initial / nouveau mot de passe")
    active = fields.Boolean(string="Compte actif", default=True)
    centre_ids = fields.Many2many(
        "etat.civil.centre",
        string="Centres d'état civil autorisés",
        help="Périmètre territorial de l'agent ou de l'officier.",
    )

    def _ensure_admin(self):
        if not (
            self.env.user._is_etat_civil_admin()
            or self.env.user.has_group("base.group_system")
        ):
            raise AccessError(
                "Seul un administrateur d'état civil peut gérer les comptes."
            )

    def _role_group(self, role):
        role_ref = {
            "agent": _CIVIL_ROLE_REFS[0],
            "officier": _CIVIL_ROLE_REFS[1],
            "regisseur": _CIVIL_ROLE_REFS[2],
            "admin": _CIVIL_ROLE_REFS[3],
        }.get(role)
        if not role_ref:
            raise ValidationError("Sélectionnez un rôle État Civil valide.")
        return self.env.ref(role_ref)

    def _validate_target(self, user):
        if not user or user.share:
            raise ValidationError(
                "La gestion des rôles État Civil est réservée aux comptes internes."
            )
        if (
            user.id == self.env.ref("base.user_admin").id
            or self.env.ref("base.group_system") in user.groups_id
        ):
            raise AccessError(
                "Les administrateurs techniques Odoo ne peuvent pas être gérés ici."
            )

    def _ensure_admin_remains(self, user, target_role, target_active):
        admin_group = self.env.ref(_CIVIL_ROLE_REFS[3])
        if user and admin_group in user.groups_id:
            if target_role != "admin" or not target_active:
                other_admins = self.env["res.users"].sudo().search_count(
                    [
                        ("id", "!=", user.id),
                        ("active", "=", True),
                        ("groups_id", "in", admin_group.id),
                    ]
                )
                if not other_admins:
                    raise UserError(
                        "Impossible de retirer ou désactiver le dernier administrateur "
                        "d'état civil actif."
                    )

    @api.onchange("user_id")
    def _onchange_user_id(self):
        if not self.user_id:
            return
        user = self.user_id
        self.name = user.name
        self.login = user.login
        self.email = user.email
        self.active = user.active
        self.password = False
        self.centre_ids = user.etat_civil_centre_ids
        if self.env.ref(_CIVIL_ROLE_REFS[3]) in user.groups_id:
            self.role = "admin"
        elif self.env.ref(_CIVIL_ROLE_REFS[1]) in user.groups_id:
            self.role = "officier"
        elif self.env.ref(_CIVIL_ROLE_REFS[2]) in user.groups_id:
            self.role = "regisseur"
        elif self.env.ref(_CIVIL_ROLE_REFS[0]) in user.groups_id:
            self.role = "agent"
        else:
            self.role = "agent"

    def _get_pos_group(self):
        """Retourne le groupe utilisateur POS, s'il est disponible."""
        try:
            return self.env.ref("point_of_sale.group_pos_user")
        except ValueError:
            return self.env["res.groups"]

    def action_save(self):
        self.ensure_one()
        self._ensure_admin()
        target_role = self.new_user_role if self.mode == "create" else self.role
        if self.mode == "create" and target_role not in ("agent", "officier", "regisseur", "admin"):
            raise ValidationError(
                "Sélectionnez un rôle valide pour le nouveau compte."
            )
        role_group = self._role_group(target_role)

        if not (self.name or "").strip() or not (self.login or "").strip():
            raise ValidationError("Le nom et l'identifiant sont obligatoires.")

        users = self.env["res.users"].sudo().with_context(no_reset_password=True)
        pos_group = self._get_pos_group()

        if self.mode == "create":
            if not (self.password or "").strip():
                raise ValidationError("Saisissez un mot de passe initial.")
            groups = [role_group.id]
            if target_role == "regisseur" and pos_group:
                groups.append(pos_group.id)
            user = users.create(
                {
                    "name": self.name.strip(),
                    "login": self.login.strip(),
                    "email": (self.email or "").strip() or False,
                    "password": self.password,
                    "groups_id": [(6, 0, groups)],
                    "etat_civil_centre_ids": [(6, 0, self.centre_ids.ids)],
                }
            )
            # Journalisation audit : création d'un utilisateur
            self._log_audit_event(user, 'create', {
                'operation': 'user_created',
                'role': target_role,
                'centre_ids': self.centre_ids.ids,
            })
        else:
            user = self.user_id.sudo()
            old_role = self._detect_current_role(user)
            self._validate_target(user)
            self._ensure_admin_remains(user, target_role, self.active)

            role_groups = [self.env.ref(group_ref).id for group_ref in _CIVIL_ROLE_REFS]
            groups_update = [(3, group_id) for group_id in role_groups]
            groups_update.append((4, role_group.id))
            # Le régisseur doit avoir le groupe POS
            if target_role == "regisseur" and pos_group:
                groups_update.append((4, pos_group.id))
            elif pos_group:
                groups_update.append((3, pos_group.id))

            values = {
                "name": self.name.strip(),
                "login": self.login.strip(),
                "email": (self.email or "").strip() or False,
                "active": self.active,
                "groups_id": groups_update,
                "etat_civil_centre_ids": [(6, 0, self.centre_ids.ids)],
            }
            if self.password:
                values["password"] = self.password
            user.write(values)
            # Journalisation audit : changement de rôle
            if old_role != target_role:
                self._log_audit_event(user, 'update', {
                    'operation': 'role_changed',
                    'old_role': old_role,
                    'new_role': target_role,
                    'centre_ids': self.centre_ids.ids,
                })

        return {"type": "ir.actions.act_window_close"}

    def _detect_current_role(self, user):
        """Détermine le rôle métier actuel d'un utilisateur."""
        if self.env.ref(_CIVIL_ROLE_REFS[3]) in user.groups_id:
            return "admin"
        if self.env.ref(_CIVIL_ROLE_REFS[1]) in user.groups_id:
            return "officier"
        if self.env.ref(_CIVIL_ROLE_REFS[2]) in user.groups_id:
            return "regisseur"
        if self.env.ref(_CIVIL_ROLE_REFS[0]) in user.groups_id:
            return "agent"
        return None

    def _log_audit_event(self, user, event_type, details):
        """Journalise un événement dans le journal d'audit."""
        self.env['etat.civil.audit.log'].sudo()._record_event(
            event_type,
            record=user,
            details=details,
        )

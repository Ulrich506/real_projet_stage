"""Enforce e-mail logins at all ORM and authentication boundaries."""

from odoo import api, models
from odoo.exceptions import AccessDenied, ValidationError
from odoo.tools.mail import email_normalize


def normalize_email_login(value):
    """Trim whitespace and lowercase only the domain, preserving local-part."""
    if not isinstance(value, str):
        raise ValidationError("Veuillez saisir une adresse e-mail valide.")
    value = value.strip()
    if value.count("@") != 1:
        raise ValidationError("Veuillez saisir une adresse e-mail valide.")
    local_part, separator, supplied_domain = value.partition("@")
    if not separator or not local_part or not supplied_domain:
        raise ValidationError("Veuillez saisir une adresse e-mail valide.")
    normalized = email_normalize(value, strict=True)
    if not normalized or "@" not in normalized:
        raise ValidationError("Veuillez saisir une adresse e-mail valide.")
    domain = normalized.rsplit("@", 1)[1]
    return "%s@%s" % (local_part, domain.lower())


def inspect_existing_logins(cr):
    """Return aggregate preflight issues without putting identities in logs."""
    cr.execute("SELECT login, active FROM res_users ORDER BY id")
    invalid_active = 0
    invalid_inactive = 0
    for login, active in cr.fetchall():
        try:
            value = normalize_email_login(login)
        except ValidationError:
            if active:
                invalid_active += 1
            else:
                invalid_inactive += 1
            continue
    cr.execute(
        "SELECT count(*) FROM ("
        " SELECT lower(login) FROM res_users GROUP BY lower(login) HAVING count(*) > 1"
        ") AS duplicate_logins"
    )
    duplicate_groups = cr.fetchone()[0]
    return invalid_active, invalid_inactive, duplicate_groups


def require_compatible_existing_logins(cr):
    invalid_active, invalid_inactive, duplicate_groups = inspect_existing_logins(cr)
    if invalid_active or duplicate_groups:
        raise ValidationError(
            "Activation de la connexion par e-mail interrompue : "
            "%s identifiant(s) actif(s) ne sont pas compatibles; %s compte(s) "
            "inactif(s) incompatible(s) restent inchangés, "
            "%s collision(s) après normalisation. Aucun login n'a été modifié. "
            "Classifiez les comptes humains et techniques puis faites confirmer "
            "les adresses avant une transition contrôlée."
            % (invalid_active, invalid_inactive, duplicate_groups)
        )


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [dict(vals) for vals in vals_list]
        for vals in vals_list:
            if "login" not in vals:
                raise ValidationError("Veuillez saisir une adresse e-mail valide.")
            vals["login"] = normalize_email_login(vals["login"])
        self._check_login_collisions([vals["login"] for vals in vals_list])
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        if "login" in vals:
            if len(self) > 1:
                raise ValidationError(
                    "Modifiez l'identifiant d'un seul utilisateur à la fois."
                )
            vals["login"] = normalize_email_login(vals["login"])
            self._check_login_collisions([vals["login"]], exclude_ids=self.ids)
        elif vals.get("active") is True:
            for user in self:
                normalized = normalize_email_login(user.login)
                self._check_login_collisions([normalized], exclude_ids=self.ids)
                if normalized != user.login:
                    user.with_context(auth_email_normalizing=True).write({"login": normalized})
        return super().write(vals)

    @api.model
    def _check_login_collisions(self, logins, exclude_ids=None):
        """Serialize normalized-identity checks to close concurrent create races."""
        if not logins:
            return
        normalized = sorted({login.casefold() for login in logins})
        for key in normalized:
            self.env.cr.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [key])
            self.env.cr.execute(
                "SELECT id FROM res_users WHERE lower(login) = lower(%s) LIMIT 1",
                [key],
            )
            row = self.env.cr.fetchone()
            if row and row[0] not in (exclude_ids or []):
                raise ValidationError("Cette adresse e-mail est déjà utilisée comme identifiant.")
        if len(normalized) != len(logins):
            raise ValidationError("Cette adresse e-mail est déjà utilisée comme identifiant.")

    @classmethod
    def _login(cls, db, login, password, user_agent_env):
        try:
            normalized_login = normalize_email_login(login)
        except ValidationError:
            raise AccessDenied()
        return super()._login(db, normalized_login, password, user_agent_env)


def post_init_hook(env):
    """Enforce case-insensitive uniqueness after a safe preflight."""
    require_compatible_existing_logins(env.cr)
    env.cr.execute(
        """
        SELECT lower(login), count(*)
          FROM res_users
         GROUP BY lower(login)
        HAVING count(*) > 1
         LIMIT 1
        """
    )
    if env.cr.fetchone():
        raise ValidationError(
            "Des identifiants entrent en collision après normalisation. "
            "Résolvez ces doublons avant d'activer la connexion par e-mail."
        )
    env.cr.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS res_users_login_lower_uniq "
        "ON res_users (lower(login))"
    )


def pre_init_hook(env):
    """Fail before the strict login policy can lock out existing users."""
    require_compatible_existing_logins(env.cr)


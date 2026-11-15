"""Block an unsafe upgrade before the strict e-mail login policy is applied."""

from odoo.tools.mail import email_normalize


def migrate(cr, version):
    cr.execute("SELECT login, active FROM res_users ORDER BY id")
    invalid_active = 0
    invalid_inactive = 0
    for login, active in cr.fetchall():
        normalized = email_normalize((login or "").strip(), strict=True)
        if not normalized or "@" not in normalized:
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
    if invalid_active or duplicate_groups:
        raise RuntimeError(
            "Mise à jour de etat_civil_auth_email bloquée : "
            "%s login(s) actif(s) incompatible(s), %s inactif(s) conservé(s), "
            "%s groupe(s) de doublons. Aucun identifiant n'a été modifié."
            % (invalid_active, invalid_inactive, duplicate_groups)
        )

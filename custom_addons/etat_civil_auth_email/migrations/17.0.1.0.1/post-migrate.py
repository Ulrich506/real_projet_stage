"""Install the case-insensitive uniqueness guard after safe preflight."""


def migrate(cr, version):
    cr.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS res_users_login_lower_uniq "
        "ON res_users (lower(login))"
    )

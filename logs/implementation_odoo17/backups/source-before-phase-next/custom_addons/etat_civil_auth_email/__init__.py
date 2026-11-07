from . import models


def post_init_hook(env):
    from .models.res_users import post_init_hook as apply_hook

    return apply_hook(env)


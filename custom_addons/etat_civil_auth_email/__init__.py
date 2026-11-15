from . import models


def post_init_hook(env):
    from .models.res_users import post_init_hook as apply_hook

    return apply_hook(env)


def pre_init_hook(env):
    from .models.res_users import pre_init_hook as check_hook

    return check_hook(env)


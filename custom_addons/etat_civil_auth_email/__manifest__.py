{
    "name": "État civil — Connexion par e-mail",
    "version": "17.0.1.0.1",
    "category": "Administration",
    "summary": "Impose une adresse e-mail comme identifiant utilisateur",
    "depends": ["base", "web", "etat_civil"],
    "data": ["views/login_templates.xml"],
    "post_init_hook": "post_init_hook",
    "pre_init_hook": "pre_init_hook",
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}


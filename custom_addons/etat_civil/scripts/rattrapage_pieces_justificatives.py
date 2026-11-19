# -*- coding: utf-8 -*-
"""
Rattrapage des pièces justificatives auto sur les actes déjà enregistrés.

Ne s'exécute PAS à la mise à jour du module. À lancer uniquement sur une
copie de la base (pg_dump / pg_restore), jamais sur la base active.

Usage (clone isolé, venv odoo17-pdf-fix-py312) :

  python odoo/odoo-bin shell -c /chemin/clone.conf -d NOM_CLONE --no-http <<'PY'
exec(open('custom_addons/etat_civil/scripts/rattrapage_pieces_justificatives.py').read())
run(env, dry_run=True)
PY

Puis, après contrôle des totaux :

  run(env, dry_run=False)
"""


def run(env, dry_run=True):
    models = (
        "etat.civil.acte.naissance",
        "etat.civil.acte.mariage",
        "etat.civil.acte.deces",
    )
    total = 0
    for model_name in models:
        records = env[model_name].sudo().search([])
        created, details = records._rattrapage_pieces_justificatives(dry_run=dry_run)
        total += created
        mode = "dry-run" if dry_run else "applique"
        print("%s %s : %s ligne(s), %s acte(s) concernés" % (
            mode, model_name, created, len(details),
        ))
        for model, rec_id, missing in details[:50]:
            print("  %s,%s -> %s" % (model, rec_id, ",".join(missing)))
        if len(details) > 50:
            print("  ... %s acte(s) de plus" % (len(details) - 50))
    print("total lignes %s : %s" % ("à créer" if dry_run else "créées", total))
    return total

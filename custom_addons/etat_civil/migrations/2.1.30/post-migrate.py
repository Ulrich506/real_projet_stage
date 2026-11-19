"""Migration : changer le format du numéro de ticket.

Avant : G-2026-00114 (prefix G-%(year)s-, padding 5)
Après  : 1, 2, 3, … (prefix vide, padding 0, no_gap)

La séquence ir.sequence est mise à jour directement en base pour que
les nouvelles demandes reçoivent un entier incrémental à partir de 1.
Les anciens tickets gardent leur numéro existant.

NOTE : Avec implementation='no_gap', Odoo n'utilise pas de séquence
PostgreSQL sous-jacente. Le numéro est stocké dans number_next de
ir_sequence et incrémenté directement en base. Il suffit donc de
mettre à jour number_next sans toucher à aucune séquence SQL.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    seq = env["ir.sequence"].search(
        [("code", "=", "etat.civil.demande.guichet")], limit=1
    )
    if seq:
        # Si la séquence est déjà en no_gap, on n'a pas besoin de
        # changer l'implementation — on met juste à jour les autres champs.
        vals = {
            "prefix": "",
            "suffix": "",
            "padding": 0,
        }
        if seq.implementation != "no_gap":
            vals["implementation"] = "no_gap"
        seq.write(vals)
        # Réinitialiser le prochain numéro à 1.
        # Pour no_gap, number_next est la seule source de vérité :
        # Odoo lit et incrémente ce champ directement.
        cr.execute(
            """
            UPDATE ir_sequence
            SET number_next = 1, number_increment = 1
            WHERE id = %s
            """,
            (seq.id,),
        )

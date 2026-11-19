"""Migration : changer le format du numéro de ticket.

Avant : G-2026-00114 (prefix G-%(year)s-, padding 5)
Après  : 1, 2, 3, … (prefix vide, padding 0, no_gap)

La séquence ir.sequence est mise à jour directement en base pour que
les nouvelles demandes reçoivent un entier incrémental à partir de 1.
Les anciens tickets gardent leur numéro existant.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    seq = env["ir.sequence"].search(
        [("code", "=", "etat.civil.demande.guichet")], limit=1
    )
    if seq:
        # Mettre à jour les paramètres de la séquence existante
        seq.write({
            "prefix": "",
            "suffix": "",
            "padding": 0,
            "implementation": "no_gap",
        })
        # Réinitialiser le prochain numéro à 1
        # Pour no_gap, on met à jour la séquence SQL sous-jacente
        cr.execute(
            """
            UPDATE ir_sequence
            SET number_next = 1, number_increment = 1
            WHERE id = %s
            """,
            (seq.id,),
        )
        # Pour les séquences no_gap (basées sur PostgreSQL),
        # on doit aussi réinitialiser la séquence SQL associée
        cr.execute(
            """
            SELECT sequence_name
            FROM ir_sequence
            WHERE id = %s
            """,
            (seq.id,),
        )
        row = cr.fetchone()
        if row and row[0]:
            cr.execute(
                f"ALTER SEQUENCE {row[0]} RESTART WITH 1"
            )

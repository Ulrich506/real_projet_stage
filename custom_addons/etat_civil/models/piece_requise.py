# -*- coding: utf-8 -*-
"""
Modèle de configuration des pièces justificatives requises par type d'acte.
Administrable uniquement par l'Administrateur d'état civil.
Les règles ici pilotent la génération automatique des lignes dans l'onglet
« Pièces à vérifier » de chaque formulaire d'acte.
"""

from odoo import api, fields, models
from odoo.exceptions import AccessError

from .piece_justificative import PIECE_TYPES

TYPE_ACTE_SELECTION = [
    ("naissance", "Acte de naissance"),
    ("mariage", "Acte de mariage"),
    ("deces", "Acte de décès"),
    ("mention", "Mention marginale"),
]

CONDITION_SELECTION = [
    # ---- Naissance ----
    ("toujours", "Toujours (sans condition)"),
    ("naissance_hopital", "Naissance à l'hôpital"),
    ("naissance_maison_autre", "Naissance à domicile ou autre lieu"),
    ("filiation_legitime", "Filiation légitime"),
    ("filiation_illegitime", "Filiation illégitime"),
    # ---- Mariage ----
    ("conjoint_1_local", "Premier conjoint malgache"),
    ("conjoint_1_etranger", "Premier conjoint étranger"),
    ("conjoint_1_capacite", "Premier conjoint étranger — capacité requise"),
    ("conjoint_1_residence_etranger", "Premier conjoint étranger — résidence étrangère"),
    ("conjoint_2_local", "Second conjoint malgache"),
    ("conjoint_2_etranger", "Second conjoint étranger"),
    ("conjoint_2_capacite", "Second conjoint étranger — capacité requise"),
    ("conjoint_2_residence_etranger", "Second conjoint étranger — résidence étrangère"),
    ("temoin_1_present", "Premier témoin renseigné"),
    ("temoin_2_present", "Second témoin renseigné"),
    ("temoins_complets", "Dossier complet (témoins obligatoires)"),
    # ---- Décès ----
    ("deces_toujours", "Toujours pour un décès"),
    # ---- Mentions marginales ----
    ("reconnaissance_mineur", "Reconnaissance d'enfant mineur"),
    ("reconnaissance_majeur", "Reconnaissance d'enfant majeur"),
    ("adoption_accord_famille", "Adoption — accord de famille requis"),
    ("adoption_fokontany", "Adoption — lettre fokontany requise"),
    ("adoption_toujours", "Adoption"),
]


class EtatCivilPieceRequise(models.Model):
    """
    Table de configuration : quelles pièces faut-il pour quel type d'acte,
    sous quelle condition, dans quel ordre, et sont-elles obligatoires ?
    """

    _name = "etat.civil.piece.requise"
    _description = "Pièce justificative requise (configuration)"
    _order = "type_acte, sequence, id"

    type_acte = fields.Selection(
        TYPE_ACTE_SELECTION,
        string="Type d'acte",
        required=True,
        index=True,
    )
    code_piece = fields.Selection(
        PIECE_TYPES,
        string="Catégorie de pièce",
        required=True,
    )
    condition = fields.Selection(
        CONDITION_SELECTION,
        string="Condition d'application",
        required=True,
        default="toujours",
        help=(
            "La pièce est générée automatiquement uniquement si cette condition "
            "est remplie sur le dossier. « Toujours » = sans condition."
        ),
    )
    obligatoire = fields.Boolean(
        string="Obligatoire",
        default=True,
        help="Si coché, l'acte ne peut pas être imprimé tant que la pièce n'est pas reçue.",
    )
    sequence = fields.Integer(
        string="Ordre d'affichage",
        default=10,
    )
    description = fields.Char(
        string="Remarque",
        help="Commentaire libre pour l'administrateur (non affiché aux agents).",
    )

    _sql_constraints = [
        (
            "unique_piece_type_condition",
            "UNIQUE(type_acte, code_piece, condition)",
            "Une règle identique (même acte, même pièce, même condition) existe déjà.",
        )
    ]

    # ------------------------------------------------------------------
    # Sécurité — seul l'administrateur peut modifier la configuration
    # ------------------------------------------------------------------

    def _ensure_admin(self):
        if not (
            self.env.user._is_etat_civil_admin()
            or self.env.user.has_group("base.group_system")
        ):
            raise AccessError(
                "Seul l'administrateur d'état civil peut modifier "
                "la configuration des pièces requises."
            )

    @api.model_create_multi
    def create(self, vals_list):
        self._ensure_admin()
        return super().create(vals_list)

    def write(self, vals):
        self._ensure_admin()
        return super().write(vals)

    def unlink(self):
        self._ensure_admin()
        return super().unlink()


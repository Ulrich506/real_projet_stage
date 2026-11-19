"""Extensions des modèles d'acte pour le lien inverse vers les demandes de copie.

Placé dans etat_civil_account car ce module dépend de etat_civil, ce qui garantit
que le modèle etat.civil.copy.request existe déjà au moment de la création des
champs One2many.
"""
from odoo import api, fields, models


class EtatCivilActeNaissanceCopy(models.Model):
    _inherit = 'etat.civil.acte.naissance'

    copy_request_ids = fields.One2many(
        'etat.civil.copy.request',
        'acte_naissance_id',
        string='Demandes de copie',
    )
    copies_delivrees_count = fields.Integer(
        string='Copies délivrées',
        compute='_compute_copies_delivrees_count',
        help='Nombre total de copies physiques délivrées pour cet acte.',
    )

    @api.depends('copy_request_ids.state', 'copy_request_ids.copy_quantity')
    def _compute_copies_delivrees_count(self):
        for record in self:
            delivered = record.copy_request_ids.filtered(lambda r: r.state == 'delivered')
            record.copies_delivrees_count = sum(delivered.mapped('copy_quantity'))


class EtatCivilActeMariageCopy(models.Model):
    _inherit = 'etat.civil.acte.mariage'

    copy_request_ids = fields.One2many(
        'etat.civil.copy.request',
        'acte_mariage_id',
        string='Demandes de copie',
    )
    copies_delivrees_count = fields.Integer(
        string='Copies délivrées',
        compute='_compute_copies_delivrees_count',
        help='Nombre total de copies physiques délivrées pour cet acte.',
    )

    @api.depends('copy_request_ids.state', 'copy_request_ids.copy_quantity')
    def _compute_copies_delivrees_count(self):
        for record in self:
            delivered = record.copy_request_ids.filtered(lambda r: r.state == 'delivered')
            record.copies_delivrees_count = sum(delivered.mapped('copy_quantity'))


class EtatCivilActeDecesCopy(models.Model):
    _inherit = 'etat.civil.acte.deces'

    copy_request_ids = fields.One2many(
        'etat.civil.copy.request',
        'acte_deces_id',
        string='Demandes de copie',
    )
    copies_delivrees_count = fields.Integer(
        string='Copies délivrées',
        compute='_compute_copies_delivrees_count',
        help='Nombre total de copies physiques délivrées pour cet acte.',
    )

    @api.depends('copy_request_ids.state', 'copy_request_ids.copy_quantity')
    def _compute_copies_delivrees_count(self):
        for record in self:
            delivered = record.copy_request_ids.filtered(lambda r: r.state == 'delivered')
            record.copies_delivrees_count = sum(delivered.mapped('copy_quantity'))

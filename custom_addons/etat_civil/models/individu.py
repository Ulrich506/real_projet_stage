import re
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


_CIVIL_STATUS_WRITE_TOKEN = object()
_CIVIL_STATUS_FIELDS = {"statut_vital", "situation_matrimoniale"}

class EtatCivilIndividu(models.Model):
    _name = 'etat.civil.individu'
    _description = 'Individu / Citoyen'
    _rec_name = 'nom_complet'

    cin = fields.Char(
        string='Carte d\'Identité Nationale (CIN)',
        index=True,
        help="Numéro de la Carte d'Identité Nationale : exactement 12 chiffres.",
    )
    nom = fields.Char(string='Nom', required=True)
    prenoms = fields.Char(string='Prénoms')
    nom_complet = fields.Char(string='Nom Complet', compute='_compute_nom_complet', store=True)
    
    sexe = fields.Selection([
        ('M', 'Masculin'),
        ('F', 'Féminin')
    ], string='Sexe', required=True)
    
    date_naissance = fields.Date(string='Date de naissance', required=False)
    categorie_age = fields.Selection(
        [
            ('nourrisson', 'Nourrisson'),
            ('enfant', 'Enfant'),
            ('adolescent', 'Adolescent'),
            ('adulte', 'Adulte'),
            ('senior', 'Senior'),
            ('indetermine', 'Non déterminé'),
        ],
        string="Catégorie d'âge",
        compute='_compute_categorie_age',
        store=True,
        readonly=True,
        help="Classification administrative d'affichage, sans valeur juridique.",
    )
    eligible_conjoint = fields.Boolean(
        string="Éligible comme conjoint",
        compute='_compute_eligible_conjoint',
        search='_search_eligible_conjoint',
        store=False,
        readonly=True,
        help="Contrôle administratif d'affichage: date de naissance vérifiée et âge d'au moins 18 ans.",
    )
    cin_non_requise = fields.Boolean(
        string='CIN non requise',
        compute='_compute_cin_non_requise',
    )
    date_naissance_estimee = fields.Boolean(string='Date estimée', default=False)
    lieu_naissance_commune = fields.Char(
        string='Commune de naissance',
        default='Fianarantsoa',
    )
    lieu_naissance_pays = fields.Char(string='Pays de naissance', default='Madagascar')
    
    profession_actuelle = fields.Char(string='Profession')
    domicile_actuel = fields.Text(string='Domicile')
    nationalite_actuelle = fields.Char(string='Nationalité', default='Malagasy')
    
    statut_vital = fields.Selection([
        ('vivant', 'Vivant'),
        ('decede', 'Décédé'),
        ('disparu', 'Présumé Disparu')
    ], string='Statut vital', default='vivant', required=True)
    
    situation_matrimoniale = fields.Selection([
        ('celibataire', 'Célibataire'),
        ('marie', 'Marié(e)'),
        ('divorce', 'Divorcé(e)'),
        ('veuf', 'Veuf/Veuve')
    ], string='Situation matrimoniale', default='celibataire', required=True)

    _sql_constraints = [
        ('cin_unique', 'unique(cin)', 'Le numéro de CIN doit être unique.'),
        (
            'cin_format',
            "CHECK(cin IS NULL OR cin = '' OR cin ~ '^[0-9]{12}$')",
            'Le numéro de CIN doit contenir exactement 12 chiffres.',
        ),
    ]

    @api.constrains('date_naissance')
    def _check_date_naissance(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.date_naissance and record.date_naissance > today:
                raise ValidationError("La date de naissance ne peut pas être dans le futur.")

    def _get_age_years(self, reference_date=None):
        self.ensure_one()
        if not self.date_naissance:
            return False
        if reference_date is None:
            reference_date = fields.Date.context_today(self)
        elif isinstance(reference_date, str):
            reference_date = fields.Date.from_string(reference_date)
        birth_date = self.date_naissance
        if reference_date < birth_date:
            return 0
        age = reference_date.year - birth_date.year
        # A 29 February birthday is reached on 1 March in non-leap years.
        anniversary_month = birth_date.month
        anniversary_day = birth_date.day
        if birth_date.month == 2 and birth_date.day == 29 and not (
            reference_date.year % 4 == 0
            and (reference_date.year % 100 != 0 or reference_date.year % 400 == 0)
        ):
            anniversary_month = 3
            anniversary_day = 1
        if (reference_date.month, reference_date.day) < (anniversary_month, anniversary_day):
            age -= 1
        return age

    def _validate_marriage_eligibility(self, reference_date=None, label=None):
        self.ensure_one()
        label = label or 'cet individu'
        if not self.date_naissance:
            raise ValidationError(
                f"Impossible de sélectionner cet individu comme {label} conjoint : "
                "sa date de naissance n'est pas renseignée."
            )
        age = self._get_age_years(reference_date=reference_date)
        if age < 18:
            raise ValidationError(
                f"Impossible de sélectionner cet individu comme {label} conjoint : "
                "son âge est inférieur à 18 ans (moins de 18 ans)."
            )
        return True

    @api.depends('date_naissance')
    def _compute_categorie_age(self):
        today = fields.Date.context_today(self)
        for record in self:
            if not record.date_naissance:
                record.categorie_age = 'indetermine'
                continue
            age = record._get_age_years(today)
            if age < 2:
                record.categorie_age = 'nourrisson'
            elif age < 12:
                record.categorie_age = 'enfant'
            elif age < 18:
                record.categorie_age = 'adolescent'
            elif age < 60:
                record.categorie_age = 'adulte'
            else:
                record.categorie_age = 'senior'

    @api.model
    def refresh_age_categories(self):
        records = self.search([])
        records.invalidate_recordset(['categorie_age', 'eligible_conjoint'])
        return True

    @api.depends('date_naissance')
    def _compute_eligible_conjoint(self):
        today = fields.Date.context_today(self)
        for record in self:
            age = record._get_age_years(today)
            record.eligible_conjoint = bool(record.date_naissance and age >= 18)

    @api.model
    def _search_eligible_conjoint(self, operator, value):
        eligible_ids = []
        today = fields.Date.context_today(self)
        for record in self.search([('date_naissance', '!=', False)]):
            if record._get_age_years(today) >= 18:
                eligible_ids.append(record.id)
        wanted = bool(value)
        matches = bool(operator in ('=', '==', 'is') and wanted)
        if matches:
            return [('id', 'in', eligible_ids)]
        if operator in ('!=', '<>', 'is not'):
            return [('id', 'not in', eligible_ids)]
        if not wanted and operator in ('=', '=='):
            return [('id', 'not in', eligible_ids)]
        return [('id', 'in', [])]

    @api.depends('date_naissance')
    def _compute_cin_non_requise(self):
        for record in self:
            today = fields.Date.context_today(record)
            record.cin_non_requise = bool(
                record.date_naissance
                and record.date_naissance > today - relativedelta(years=18)
            )

    @api.constrains('cin')
    def _check_cin_format(self):
        for record in self:
            if record.cin and not re.fullmatch(r'[0-9]{12}', record.cin):
                raise ValidationError('Le numéro de CIN doit contenir exactement 12 chiffres.')

    @api.constrains('cin')
    def _check_cin_unique(self):
        for record in self:
            if record.cin:
                duplicate = self.search([
                    ('id', '!=', record.id),
                    ('cin', '=', record.cin),
                ], limit=1)
                if duplicate:
                    raise ValidationError("Le numéro de CIN doit être unique.")

    @api.model
    def _default_cin_for_newborn(self):
        return False

    @staticmethod
    def _normalize_cin(value):
        if not isinstance(value, str):
            return value
        value = value.strip() or False
        if value and not re.fullmatch(r'[0-9]{12}', value):
            raise ValidationError('Le numéro de CIN doit contenir exactement 12 chiffres.')
        return value

    @api.model_create_multi
    def create(self, vals_list):
        if (
            self.env.context.get("etat_civil_status_write_token")
            is not _CIVIL_STATUS_WRITE_TOKEN
            and any(
                any(
                    key in vals and vals[key] != default
                    for key, default in (
                        ("statut_vital", "vivant"),
                        ("situation_matrimoniale", "celibataire"),
                    )
                )
                for vals in vals_list
            )
        ):
            raise UserError(
                "Le statut vital et la situation matrimoniale doivent être "
                "initialisés par un import autorisé ou modifiés par le workflow d'état civil."
            )
        for vals in vals_list:
            legacy_cin = vals.pop('nin', None)
            if legacy_cin is not None:
                if vals.get('cin') not in (None, legacy_cin):
                    raise ValidationError("Les valeurs CIN reçues ne correspondent pas.")
                vals['cin'] = legacy_cin
            if 'cin' in vals and vals['cin'] not in (None, ''):
                vals['cin'] = self._normalize_cin(vals['cin'])
                if vals['cin'] and self.search_count([('cin', '=', vals['cin'])]) > 0:
                    raise ValidationError("Le numéro de CIN doit être unique.")
        return super().create(vals_list)

    @api.model_create_multi
    def _create_from_import(self, vals_list):
        return self.with_context(
            etat_civil_status_write_token=_CIVIL_STATUS_WRITE_TOKEN
        ).create(vals_list)

    def _write_civil_status(self, vals):
        if not vals or not set(vals).issubset(_CIVIL_STATUS_FIELDS):
            raise ValidationError("Seuls les statuts d'état civil peuvent être modifiés par cette méthode.")
        return self.with_context(
            etat_civil_status_write_token=_CIVIL_STATUS_WRITE_TOKEN
        ).write(vals)

    def _write_from_import(self, vals):
        if _CIVIL_STATUS_FIELDS.intersection(vals):
            profile_vals = {
                key: value for key, value in vals.items()
                if key not in _CIVIL_STATUS_FIELDS
            }
            if profile_vals:
                self.write(profile_vals)
            status_vals = {
                key: value for key, value in vals.items()
                if key in _CIVIL_STATUS_FIELDS
            }
            return self._write_civil_status(status_vals)
        return self.write(vals)

    def write(self, vals):
        vals = dict(vals)
        if (
            _CIVIL_STATUS_FIELDS.intersection(vals)
            and self.env.context.get("etat_civil_status_write_token")
            is not _CIVIL_STATUS_WRITE_TOKEN
        ):
            raise UserError(
                "Le statut vital et la situation matrimoniale doivent être "
                "modifiés par le workflow d'état civil."
            )
        legacy_cin = vals.pop('nin', None)
        if legacy_cin is not None:
            if vals.get('cin') not in (None, legacy_cin):
                raise ValidationError("Les valeurs CIN reçues ne correspondent pas.")
            vals['cin'] = legacy_cin
        if 'cin' in vals and vals['cin'] not in (None, ''):
            vals['cin'] = self._normalize_cin(vals['cin'])
            if vals['cin'] and self.search_count([('id', 'not in', self.ids), ('cin', '=', vals['cin'])]) > 0:
                raise ValidationError("Le numéro de CIN doit être unique.")
        birth_date_changed = 'date_naissance' in vals
        result = super().write(vals)
        if birth_date_changed:
            marriage_model = self.env['etat.civil.acte.mariage']
            marriages = marriage_model.search([
                '|',
                ('conjoint_1_id', 'in', self.ids),
                ('conjoint_2_id', 'in', self.ids),
            ])
            reference_ids = set(self.ids)
            for marriage in marriages:
                reference_date = marriage.date_mariage or fields.Date.context_today(marriage)
                for label, spouse in (
                    ('premier', marriage.conjoint_1_id),
                    ('second', marriage.conjoint_2_id),
                ):
                    if spouse.id in reference_ids:
                        spouse._validate_marriage_eligibility(reference_date, label)
        return result

    @api.depends('nom', 'prenoms')
    def _compute_nom_complet(self):
        for rec in self:
            rec.nom_complet = f"{rec.nom or ''} {rec.prenoms or ''}".strip()
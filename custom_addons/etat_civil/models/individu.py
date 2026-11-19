import re
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


_CIVIL_STATUS_WRITE_TOKEN = object()
_CIVIL_STATUS_FIELDS = {"statut_vital", "situation_matrimoniale"}

class EtatCivilIndividu(models.Model):
    _name = 'etat.civil.individu'
    _inherit = ['etat.civil.audit.mixin']
    _description = 'Individu / Citoyen'
    _rec_name = 'nom_complet'

    acte_naissance_enfant_ids = fields.One2many(
        "etat.civil.acte.naissance", "enfant_id", string="Actes de naissance comme enfant"
    )
    acte_naissance_pere_ids = fields.One2many(
        "etat.civil.acte.naissance", "pere_id", string="Actes de naissance comme père"
    )
    acte_naissance_mere_ids = fields.One2many(
        "etat.civil.acte.naissance", "mere_id", string="Actes de naissance comme mère"
    )
    acte_naissance_declarant_ids = fields.One2many(
        "etat.civil.acte.naissance", "declarant_id", string="Actes de naissance comme déclarant"
    )
    acte_mariage_conjoint_1_ids = fields.One2many(
        "etat.civil.acte.mariage", "conjoint_1_id", string="Actes de mariage comme conjoint"
    )
    acte_mariage_conjoint_2_ids = fields.One2many(
        "etat.civil.acte.mariage", "conjoint_2_id", string="Actes de mariage comme 2ème conjoint"
    )
    acte_mariage_temoin_1_ids = fields.One2many(
        "etat.civil.acte.mariage", "temoin_1_id", string="Actes de mariage comme témoin"
    )
    acte_mariage_temoin_2_ids = fields.One2many(
        "etat.civil.acte.mariage", "temoin_2_id", string="Actes de mariage comme 2ème témoin"
    )
    acte_deces_defunt_ids = fields.One2many(
        "etat.civil.acte.deces", "defunt_id", string="Actes de décès comme défunt"
    )
    acte_deces_declarant_ids = fields.One2many(
        "etat.civil.acte.deces", "declarant_id", string="Actes de décès comme déclarant"
    )

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
    def _default_lieu_naissance_commune(self):
        user = self.env.user
        if hasattr(user, 'etat_civil_centre_ids') and user.etat_civil_centre_ids:
            primary_centre = user.etat_civil_centre_ids[0]
            if primary_centre.commune:
                return primary_centre.commune
        return False

    date_naissance_estimee = fields.Boolean(string='Date estimée', default=False)
    lieu_naissance_commune = fields.Char(
        string='Commune de naissance',
        default=_default_lieu_naissance_commune,
    )
    lieu_naissance_pays = fields.Char(string='Pays de naissance', default='Madagascar')
    
    profession_actuelle = fields.Char(string='Profession')
    domicile_actuel = fields.Text(string='Domicile')
    nationalite_actuelle = fields.Char(string='Nationalité', default='Malagasy')
    
    statut_vital = fields.Selection([
        ('vivant', 'Vivant'),
        ('decede', 'Décédé'),
        ('presume_disparu', 'Présumé disparu'),
        ('presume_mort', 'Présumé mort'),
        ('autre', 'Autre'),
    ], string='Statut vital', default='vivant', required=True)
    statut_vital_precision = fields.Char(
        string='Précision du statut vital',
        help='Champ visible uniquement quand le statut vital est « Autre ».',
    )
    
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
        today = fields.Date.context_today(self)
        eighteen_years_ago = today - relativedelta(years=18)
        # Use a SQL date comparison instead of iterating row-by-row in Python.
        eligible_ids = self.search([
            ('date_naissance', '!=', False),
            ('date_naissance', '<=', eighteen_years_ago),
        ]).ids
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
        return self.sudo().with_context(
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

    @api.model
    def citoyens_demo_init(self):
        """Initialiser les citoyens de démonstration (appelé depuis data XML)."""
        citoyens = [
            {"nom": "Rakoto", "prenoms": "Jean Michel", "cin": "100198500001", "sexe": "M",
             "date_naissance": "1985-03-15", "lieu_naissance_commune": "Fianarantsoa",
             "lieu_naissance_pays": "Madagascar", "nationalite_actuelle": "Malagasy",
             "domicile_actuel": "Lot II N°45, Analakely, Fianarantsoa 401",
             "profession_actuelle": "Enseignant", "statut_vital": "vivant", "situation_matrimoniale": "marie"},
            {"nom": "Rasoa", "prenoms": "Marie Claire", "cin": "100199000002", "sexe": "F",
             "date_naissance": "1990-07-22", "lieu_naissance_commune": "Fianarantsoa",
             "lieu_naissance_pays": "Madagascar", "nationalite_actuelle": "Malagasy",
             "domicile_actuel": "Tsiafahiny, Fianarantsoa 401",
             "profession_actuelle": "Infirmière", "statut_vital": "vivant", "situation_matrimoniale": "celibataire"},
            {"nom": "Andria", "prenoms": "François", "cin": "100197800003", "sexe": "M",
             "date_naissance": "1978-11-05", "lieu_naissance_commune": "Fianarantsoa",
             "lieu_naissance_pays": "Madagascar", "nationalite_actuelle": "Malagasy",
             "domicile_actuel": "Ambodivona, Fianarantsoa 401",
             "profession_actuelle": "Commerçant", "statut_vital": "vivant", "situation_matrimoniale": "marie"},
            {"nom": "Be", "prenoms": "Sophie Raharimanana", "cin": "100199500004", "sexe": "F",
             "date_naissance": "1995-01-30", "lieu_naissance_commune": "Fianarantsoa",
             "lieu_naissance_pays": "Madagascar", "nationalite_actuelle": "Malagasy",
             "domicile_actuel": "Lot I N°12, Ambodivona, Fianarantsoa 401",
             "profession_actuelle": "Avocate", "statut_vital": "vivant", "situation_matrimoniale": "celibataire"},
            {"nom": "Rajaonarivelo", "prenoms": "Hery", "cin": "100196000005", "sexe": "M",
             "date_naissance": "1960-06-18", "lieu_naissance_commune": "Fianarantsoa",
             "lieu_naissance_pays": "Madagascar", "nationalite_actuelle": "Malagasy",
             "domicile_actuel": "Ambohimanga, Fianarantsoa 401",
             "profession_actuelle": "Retraité", "statut_vital": "vivant", "situation_matrimoniale": "veuf"},
            {"nom": "Voahirana", "prenoms": "Nirina", "cin": "100198800006", "sexe": "F",
             "date_naissance": "1988-09-12", "lieu_naissance_commune": "Fianarantsoa",
             "lieu_naissance_pays": "Madagascar", "nationalite_actuelle": "Malagasy",
             "domicile_actuel": "Ambodirano, Fianarantsoa 401",
             "profession_actuelle": "Médecin", "statut_vital": "vivant", "situation_matrimoniale": "marie"},
            {"nom": "Randria", "prenoms": "Tiana", "cin": "100197200007", "sexe": "F",
             "date_naissance": "1972-04-25", "lieu_naissance_commune": "Fianarantsoa",
             "lieu_naissance_pays": "Madagascar", "nationalite_actuelle": "Malagasy",
             "domicile_actuel": "Lot IV N°78, Isotry, Fianarantsoa 401",
             "profession_actuelle": "Pharmacien", "statut_vital": "vivant", "situation_matrimoniale": "divorce"},
            {"nom": "Njara", "prenoms": "Andry", "cin": "100200000008", "sexe": "M",
             "date_naissance": "2000-12-03", "lieu_naissance_commune": "Fianarantsoa",
             "lieu_naissance_pays": "Madagascar", "nationalite_actuelle": "Malagasy",
             "domicile_actuel": "Lot I N°5, Fianarantsoa 401",
             "profession_actuelle": "Étudiant", "statut_vital": "vivant", "situation_matrimoniale": "celibataire"},
            {"nom": "Rakotonirina", "prenoms": "Voahirana", "cin": "100195500009", "sexe": "F",
             "date_naissance": "1955-08-14", "lieu_naissance_commune": "Fianarantsoa",
             "lieu_naissance_pays": "Madagascar", "nationalite_actuelle": "Malagasy",
             "domicile_actuel": "Ambalabe, Fianarantsoa 401",
             "profession_actuelle": "Retraité", "statut_vital": "decede", "situation_matrimoniale": "veuve"},
            {"nom": "Haja", "prenoms": "Fidovolonirina", "cin": "100199200010", "sexe": "F",
             "date_naissance": "1992-02-28", "lieu_naissance_commune": "Fianarantsoa",
             "lieu_naissance_pays": "Madagascar", "nationalite_actuelle": "Malagasy",
             "domicile_actuel": "Lot III N°33, Alasora, Fianarantsoa 401",
             "profession_actuelle": "Comptable", "statut_vital": "vivant", "situation_matrimoniale": "marie"},
            {"nom": "Ravelo", "prenoms": "M-bah", "cin": "100198300011", "sexe": "M",
             "date_naissance": "1983-05-09", "lieu_naissance_commune": "Fianarantsoa",
             "lieu_naissance_pays": "Madagascar", "nationalite_actuelle": "Malagasy",
             "domicile_actuel": "Amborovy, Fianarantsoa 401",
             "profession_actuelle": "Ingénieur", "statut_vital": "vivant", "situation_matrimoniale": "marie"},
            {"nom": "Rajaona", "prenoms": "Hanta", "cin": "100199800012", "sexe": "F",
             "date_naissance": "1998-10-17", "lieu_naissance_commune": "Fianarantsoa",
             "lieu_naissance_pays": "Madagascar", "nationalite_actuelle": "Malagasy",
             "domicile_actuel": "Lot II N°21, Ambatobevy, Fianarantsoa 401",
             "profession_actuelle": "Journaliste", "statut_vital": "vivant", "situation_matrimoniale": "celibataire"},
            {"nom": "Andriamampandry", "prenoms": "Solomon", "cin": "100196500013", "sexe": "M",
             "date_naissance": "1965-07-01", "lieu_naissance_commune": "Fianarantsoa",
             "lieu_naissance_pays": "Madagascar", "nationalite_actuelle": "Malagasy",
             "domicile_actuel": "Lot I N°9, Fianarantsoa 401",
             "profession_actuelle": "Professeur", "statut_vital": "vivant", "situation_matrimoniale": "marie"},
            {"nom": "Rakotoharisoa", "prenoms": "Voahary", "cin": "100200300014", "sexe": "F",
             "date_naissance": "2003-03-20", "lieu_naissance_commune": "Fianarantsoa",
             "lieu_naissance_pays": "Madagascar", "nationalite_actuelle": "Malagasy",
             "domicile_actuel": "Ambodivona, Fianarantsoa 401",
             "profession_actuelle": "Étudiante", "statut_vital": "vivant", "situation_matrimoniale": "celibataire"},
            {"nom": "Razafindrabe", "prenoms": "Tobiana", "cin": "100197500015", "sexe": "M",
             "date_naissance": "1975-12-11", "lieu_naissance_commune": "Fianarantsoa",
             "lieu_naissance_pays": "Madagascar", "nationalite_actuelle": "Malagasy",
             "domicile_actuel": "Lot II N°56, Ambalavojy, Fianarantsoa 401",
             "profession_actuelle": "Agriculteur", "statut_vital": "vivant", "situation_matrimoniale": "marie"},
            {"nom": "Nirina", "prenoms": "Rakotonirina", "cin": "100194000016", "sexe": "F",
             "date_naissance": "1940-01-05", "lieu_naissance_commune": "Fianarantsoa",
             "lieu_naissance_pays": "Madagascar", "nationalite_actuelle": "Malagasy",
             "domicile_actuel": "Lot IV N°2, Analakely, Fianarantsoa 401",
             "profession_actuelle": "Retraité", "statut_vital": "decede", "situation_matrimoniale": "veuve"},
            {"nom": "Rakotondrazaka", "prenoms": "Haja", "cin": "100199900017", "sexe": "F",
             "date_naissance": "1999-06-23", "lieu_naissance_commune": "Fianarantsoa",
             "lieu_naissance_pays": "Madagascar", "nationalite_actuelle": "Malagasy",
             "domicile_actuel": "Lot I N°44, Fianarantsoa 401",
             "profession_actuelle": "Vétérinaire", "statut_vital": "vivant", "situation_matrimoniale": "celibataire"},
            {"nom": "Rajaonarison", "prenoms": "David", "cin": "100198700018", "sexe": "M",
             "date_naissance": "1987-04-08", "lieu_naissance_commune": "Fianarantsoa",
             "lieu_naissance_pays": "Madagascar", "nationalite_actuelle": "Malagasy",
             "domicile_actuel": "Ambodirano, Fianarantsoa 401",
             "profession_actuelle": "Architecte", "statut_vital": "vivant", "situation_matrimoniale": "marie"},
            {"nom": "Be", "prenoms": "Fara", "cin": "100200100019", "sexe": "F",
             "date_naissance": "2001-09-15", "lieu_naissance_commune": "Fianarantsoa",
             "lieu_naissance_pays": "Madagascar", "nationalite_actuelle": "Malagasy",
             "domicile_actuel": "Lot III N°67, Isotry, Fianarantsoa 401",
             "profession_actuelle": "Étudiante", "statut_vital": "vivant", "situation_matrimoniale": "celibataire"},
            {"nom": "Andriamanjato", "prenoms": "Rakoto", "cin": "100197000020", "sexe": "M",
             "date_naissance": "1970-11-30", "lieu_naissance_commune": "Fianarantsoa",
             "lieu_naissance_pays": "Madagascar", "nationalite_actuelle": "Malagasy",
             "domicile_actuel": "Ambalabe, Fianarantsoa 401",
             "profession_actuelle": "Pêcheur", "statut_vital": "vivant", "situation_matrimoniale": "divorce"},
        ]
        created = 0
        for vals in citoyens:
            if self.search_count([('cin', '=', vals['cin'])]):
                continue
            try:
                self._create_from_import([vals])
                created += 1
            except Exception:
                pass
        return created

    @api.depends('nom', 'prenoms')
    def _compute_nom_complet(self):
        for rec in self:
            rec.nom_complet = f"{rec.nom or ''} {rec.prenoms or ''}".strip()
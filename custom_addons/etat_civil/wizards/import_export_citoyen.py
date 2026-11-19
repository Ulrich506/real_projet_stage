import base64
import csv
import io
import json
import logging
import os
import re
import zipfile
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

# Maximum file sizes
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_ZIP_TOTAL = 200 * 1024 * 1024  # 200 MB decompressed
def _ensure_civil_admin(env):
    if not env.su and not env.user.has_group("etat_civil.group_etat_civil_admin"):
        raise AccessError(_("Seul l'administrateur d'état civil peut importer ou exporter des citoyens."))


# Auto-mapping: common external column names → Odoo field names
AUTO_MAPPING = {
    'nom': 'nom',
    'name': 'nom',
    'last_name': 'nom',
    'lastname': 'nom',
    'family_name': 'nom',
    'nom_famille': 'nom',
    'prenom': 'prenoms',
    'prenoms': 'prenoms',
    'first_name': 'prenoms',
    'firstname': 'prenoms',
    'given_name': 'prenoms',
    'cin': 'cin',
    'nin': 'cin',
    'id_number': 'cin',
    'carte_identite': 'cin',
    'sexe': 'sexe',
    'sex': 'sexe',
    'gender': 'sexe',
    'genre': 'sexe',
    'date_naissance': 'date_naissance',
    'birth_date': 'date_naissance',
    'date_of_birth': 'date_naissance',
    'dob': 'date_naissance',
    'nationalite': 'nationalite_actuelle',
    'nationality': 'nationalite_actuelle',
    'nationalite_actuelle': 'nationalite_actuelle',
    'domicile': 'domicile_actuel',
    'address': 'domicile_actuel',
    'adresse': 'domicile_actuel',
    'domicile_actuel': 'domicile_actuel',
    'profession': 'profession_actuelle',
    'profession_actuelle': 'profession_actuelle',
    'job': 'profession_actuelle',
    'commune_naissance': 'lieu_naissance_commune',
    'lieu_naissance_commune': 'lieu_naissance_commune',
    'birthplace': 'lieu_naissance_commune',
    'lieu_naissance': 'lieu_naissance_commune',
    'pays_naissance': 'lieu_naissance_pays',
    'lieu_naissance_pays': 'lieu_naissance_pays',
    'birth_country': 'lieu_naissance_pays',
    'country': 'lieu_naissance_pays',
    'statut_vital': 'statut_vital',
    'vital_status': 'statut_vital',
    'situation_matrimoniale': 'situation_matrimoniale',
    'marital_status': 'situation_matrimoniale',
}
IMPORTABLE_FIELD_ORDER = [
    "nom", "prenoms", "cin", "sexe", "date_naissance",
    "date_naissance_estimee", "lieu_naissance_commune",
    "lieu_naissance_pays", "nationalite_actuelle", "domicile_actuel",
    "profession_actuelle", "statut_vital", "situation_matrimoniale",
]

# Fields allowed for import on etat.civil.individu
IMPORTABLE_FIELDS = {
    'nom', 'prenoms', 'cin', 'sexe', 'date_naissance',
    'date_naissance_estimee', 'lieu_naissance_commune', 'lieu_naissance_pays',
    'nationalite_actuelle', 'domicile_actuel', 'profession_actuelle',
    'statut_vital', 'situation_matrimoniale',
}

EXPORTABLE_FIELDS = [
    "cin",
    "nom",
    "prenoms",
    "nom_complet",
    "sexe",
    "date_naissance",
    "date_naissance_estimee",
    "categorie_age",
    "lieu_naissance_commune",
    "lieu_naissance_pays",
    "nationalite_actuelle",
    "domicile_actuel",
    "profession_actuelle",
    "statut_vital",
    "situation_matrimoniale",
]


def _create_exchange_log(
    env,
    operation,
    state,
    file_name,
    file_format,
    total_rows=0,
    imported_rows=0,
    updated_rows=0,
    skipped_rows=0,
    duplicate_rows=0,
    error_rows=0,
    criteria=None,
    exported_fields=None,
    language=None,
):
    operation_label = _("Importation") if operation == "import" else _("Exportation")
    exchange_log = env["etat.civil.exchange.log"].sudo().create({
        "name": "%s — %s" % (operation_label, file_name or _("sans nom")),
        "operation": operation,
        "state": state,
        "user_id": env.uid,
        "file_name": file_name,
        "file_format": file_format,
        "total_rows": total_rows,
        "imported_rows": imported_rows,
        "updated_rows": updated_rows,
        "skipped_rows": skipped_rows,
        "duplicate_rows": duplicate_rows,
        "error_rows": error_rows,
        "criteria": json.dumps(criteria or {}, ensure_ascii=False, sort_keys=True),
        "exported_fields": json.dumps(exported_fields or [], ensure_ascii=False),
        "language": language or env.context.get("lang"),
    })
    env["etat.civil.audit.log"]._record_event(
        "import" if operation == "import" else "export",
        record=exchange_log,
        result=state if state in ("success", "partial", "failed") else "success",
        details={
            "file_format": file_format,
            "rows": total_rows,
            "field_count": len(exported_fields or []),
            "language": language or env.context.get("lang"),
        },
    )


def _escape_spreadsheet_formula(value):
    if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')):
        return "'" + value
    return value


class EtatCivilImportLine(models.TransientModel):
    _name = "etat.civil.import.line"
    _description = "Ligne de prévisualisation de l'import citoyen"
    _order = "line_number, id"

    wizard_id = fields.Many2one(
        "etat.civil.import.wizard", required=True, ondelete="cascade"
    )
    line_number = fields.Integer(string="Ligne", readonly=True)
    nom = fields.Char(string="Nom")
    prenoms = fields.Char(string="Prénoms")
    cin = fields.Char(string="CIN")
    sexe = fields.Char(string="Sexe")
    date_naissance = fields.Char(string="Date de naissance")
    date_naissance_estimee = fields.Char(string="Date estimée")
    lieu_naissance_commune = fields.Char(string="Commune de naissance")
    lieu_naissance_pays = fields.Char(string="Pays de naissance")
    nationalite_actuelle = fields.Char(string="Nationalité")
    domicile_actuel = fields.Char(string="Domicile")
    profession_actuelle = fields.Char(string="Profession")
    statut_vital = fields.Char(string="Statut vital")
    situation_matrimoniale = fields.Char(string="Situation matrimoniale")
    error_message = fields.Text(string="Erreurs de validation", readonly=True)
    duplicate_record_id = fields.Many2one(
        "etat.civil.individu", string="Doublon existant", readonly=True
    )


class EtatCivilImportWizard(models.TransientModel):
    _name = 'etat.civil.import.wizard'
    _description = "Assistant d'importation des citoyens"

    file_data = fields.Binary(string='Fichier à importer')
    file_name = fields.Char(string='Nom du fichier')
    file_format = fields.Selection([
        ('csv', 'CSV'),
        ('xlsx', 'Excel (.xlsx)'),
        ('xls', 'Excel ancien (.xls)'),
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('ods', 'ODS (LibreOffice)'),
        ('zip', 'ZIP (archive)'),
    ], string='Format', compute='_compute_file_format', store=True)

    duplicate_strategy = fields.Selection([
        ('skip', 'Ignorer les doublons'),
        ('update', 'Mettre à jour les doublons'),
        ('report', 'Signaler les doublons (ne pas importer)'),
    ], string='Stratégie de doublons', default='skip', required=True)

    state = fields.Selection([
        ('upload', 'Téléverser'),
        ('mapping', 'Correspondance des colonnes'),
        ('preview', 'Aperçu'),
        ('done', 'Terminé'),
    ], default='upload', string='Étape')

    # Mapping fields (stored as JSON)
    detected_columns = fields.Text(string='Colonnes détectées (JSON)', readonly=True)
    column_mapping = fields.Text(
        string='Correspondance des colonnes (JSON)',
        help='JSON dict: {"external_col": "odoo_field_or_empty", ...}',
    )
    preview_data = fields.Text(string='Aperçu (JSON)', readonly=True)
    line_ids = fields.One2many(
        "etat.civil.import.line", "wizard_id", string="Lignes à importer"
    )
    template_file = fields.Binary(string="Modèle d'importation", readonly=True)
    template_file_name = fields.Char(readonly=True)

    # Results
    result_total = fields.Integer(string='Lignes analysées', readonly=True)
    result_imported = fields.Integer(string='Citoyens importés', readonly=True)
    result_updated = fields.Integer(string='Citoyens mis à jour', readonly=True)
    result_duplicates = fields.Integer(string='Doublons détectés', readonly=True)
    result_skipped = fields.Integer(string='Lignes ignorées', readonly=True)
    result_errors = fields.Integer(string='Erreurs', readonly=True)
    result_details = fields.Text(string='Détails / erreurs', readonly=True)
    result_error_file = fields.Binary(string='Rapport des erreurs', readonly=True)
    result_error_file_name = fields.Char(string='Nom du rapport', readonly=True)

    @api.depends('file_name')
    def _compute_file_format(self):
        ext_map = {
            '.csv': 'csv',
            '.xlsx': 'xlsx',
            '.xls': 'xls',
            '.json': 'json',
            '.xml': 'xml',
            '.ods': 'ods',
            '.zip': 'zip',
        }
        for rec in self:
            ext = ''
            if rec.file_name:
                ext = os.path.splitext(rec.file_name)[1].lower()
            rec.file_format = ext_map.get(ext, False)

    def _decode_file(self):
        """Decode binary field and validate file size."""
        self.ensure_one()
        if not self.file_data:
            raise UserError(_("Aucun fichier fourni."))
        raw = base64.b64decode(self.file_data)
        if len(raw) > MAX_FILE_SIZE:
            raise UserError(
                _("Le fichier dépasse la taille maximale autorisée (%d Mo).")
                % (MAX_FILE_SIZE // (1024 * 1024))
            )
        return raw

    def _parse_file(self, raw=None):
        """Parse the uploaded file and return a list of dicts (rows)."""
        self.ensure_one()
        if raw is None:
            raw = self._decode_file()
        fmt = self.file_format
        if not fmt:
            raise UserError(_("Format de fichier non reconnu. Extensions acceptées : .csv, .xlsx, .xls, .json, .xml, .ods, .zip"))
        if fmt == 'csv':
            return self._parse_csv(raw)
        elif fmt == 'xlsx':
            return self._parse_xlsx(raw)
        elif fmt == 'xls':
            return self._parse_xls(raw)
        elif fmt == 'json':
            return self._parse_json(raw)
        elif fmt == 'xml':
            return self._parse_xml(raw)
        elif fmt == 'ods':
            return self._parse_ods(raw)
        elif fmt == 'zip':
            return self._parse_zip(raw)
        raise UserError(_("Format '%s' non pris en charge.") % fmt)

    def _parse_csv(self, raw):
        try:
            text = raw.decode('utf-8-sig')
        except UnicodeDecodeError as exc:
            raise UserError(_("Le fichier CSV n'est pas encodé en UTF-8.")) from exc
        reader = csv.DictReader(io.StringIO(text))
        return [dict(row) for row in reader]

    def _parse_xlsx(self, raw):
        try:
            import openpyxl
        except ImportError:
            raise UserError(_("La bibliothèque 'openpyxl' est nécessaire pour importer des fichiers Excel (.xlsx). Installez-la avec : pip install openpyxl"))
        wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        headers = [str(h or '').strip() for h in rows[0]]
        result = []
        for row in rows[1:]:
            d = {}
            for i, val in enumerate(row):
                if i < len(headers) and headers[i]:
                    d[headers[i]] = str(val) if val is not None else ''
            result.append(d)
        wb.close()
        return result

    def _parse_xls(self, raw):
        try:
            import xlrd
        except ImportError:
            raise UserError(_("La bibliothèque 'xlrd' est nécessaire pour les fichiers .xls. Installez-la avec : pip install xlrd"))
        wb = xlrd.open_workbook(file_contents=raw)
        ws = wb.sheet_by_index(0)
        headers = [str(ws.cell_value(0, c)).strip() for c in range(ws.ncols)]
        result = []
        for r in range(1, ws.nrows):
            d = {}
            for c in range(ws.ncols):
                if headers[c]:
                    d[headers[c]] = str(ws.cell_value(r, c)).strip()
            result.append(d)
        return result

    def _parse_json(self, raw):
        text = raw.decode('utf-8-sig', errors='replace')
        data = json.loads(text)
        if isinstance(data, dict):
            data = data.get('data', data.get('citoyens', data.get('records', [])))
        if not isinstance(data, list):
            raise UserError(_("Le fichier JSON doit contenir une liste de citoyens."))
        return [{str(k): str(v) if v is not None else '' for k, v in row.items()} for row in data if isinstance(row, dict)]

    def _parse_xml(self, raw):
        import xml.etree.ElementTree as ET
        if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
            raise UserError(_("Les déclarations DTD et entités XML ne sont pas autorisées."))
        root = ET.fromstring(raw)
        result = []
        # Support both <citoyens><citoyen>...</citoyen></citoyens>
        # and <records><record>...</record></records>
        for child in root:
            d = {}
            for elem in child:
                d[elem.tag] = (elem.text or '').strip()
            if d:
                result.append(d)
        return result

    def _parse_ods(self, raw):
        try:
            from odf.opendocument import load as odf_load
            from odf.table import Table, TableRow, TableCell
            from odf.text import P
        except ImportError:
            raise UserError(_("La bibliothèque 'odfpy' est nécessaire pour les fichiers .ods. Installez-la avec : pip install odfpy"))
        doc = odf_load(io.BytesIO(raw))
        result = []
        for table in doc.getElementsByType(Table):
            rows = table.getElementsByType(TableRow)
            if not rows:
                continue
            headers = []
            for cell in rows[0].getElementsByType(TableCell):
                text_parts = []
                for p in cell.getElementsByType(P):
                    text_content = ''
                    for child_node in p.childNodes:
                        text_content += str(child_node)
                    text_parts.append(text_content.strip())
                headers.append(' '.join(text_parts).strip())
            for row in rows[1:]:
                d = {}
                cells = row.getElementsByType(TableCell)
                for i, cell in enumerate(cells):
                    if i < len(headers) and headers[i]:
                        text_parts = []
                        for p in cell.getElementsByType(P):
                            text_content = ''
                            for child_node in p.childNodes:
                                text_content += str(child_node)
                            text_parts.append(text_content.strip())
                        d[headers[i]] = ' '.join(text_parts).strip()
                if any(v for v in d.values()):
                    result.append(d)
            break  # Only first table
        return result

    def _parse_zip(self, raw):
        """Parse supported files in an archive without extracting them."""
        total_decompressed = 0
        all_rows = []
        with zipfile.ZipFile(io.BytesIO(raw), 'r') as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                normalized_name = info.filename.replace('\\', '/')
                if (
                    normalized_name.startswith('/')
                    or any(part == '..' for part in normalized_name.split('/'))
                ):
                    raise UserError(
                        _("Le fichier ZIP contient un chemin non autorisé : %s")
                        % info.filename
                    )
                total_decompressed += info.file_size
                if total_decompressed > MAX_ZIP_TOTAL:
                    raise UserError(
                        _("La taille totale décompressée dépasse la limite (%d Mo).")
                        % (MAX_ZIP_TOTAL // (1024 * 1024))
                    )
                ext = os.path.splitext(info.filename)[1].lower()
                if ext not in ('.csv', '.xlsx', '.xls', '.json', '.xml', '.ods'):
                    continue
                inner_raw = zf.read(info.filename)
                # Create a temporary sub-wizard to parse each file
                sub = self.new({
                    'file_name': info.filename,
                    'file_format': {
                        '.csv': 'csv', '.xlsx': 'xlsx', '.xls': 'xls',
                        '.json': 'json', '.xml': 'xml', '.ods': 'ods',
                    }.get(ext),
                })
                try:
                    all_rows.extend(sub._parse_file(inner_raw))
                except Exception as e:
                    _logger.warning("Could not parse %s from uploaded ZIP: %s", info.filename, e)
                    raise UserError(
                        _("Impossible de lire le fichier « %s » contenu dans l'archive : %s")
                        % (info.filename, str(e))
                    ) from e
        return all_rows

    def action_detect_columns(self):
        """Step 1 → Step 2: Parse file and detect columns."""
        self.ensure_one()
        _ensure_civil_admin(self.env)
        rows = self._parse_file()
        if not rows:
            raise UserError(_("Le fichier ne contient aucune donnée."))

        # Collect all column names
        columns = list(dict.fromkeys(
            col for row in rows for col in row.keys() if col.strip()
        ))

        # Auto-map columns
        translated_fields = self.env["etat.civil.individu"].fields_get(
            IMPORTABLE_FIELD_ORDER, ["string"]
        )
        translated_mapping = {
            re.sub(r"[\s-]+", "_", info["string"].strip().lower()): field_name
            for field_name, info in translated_fields.items()
        }
        mapping = {}
        for col in columns:
            normalized = col.strip().lower().replace(' ', '_').replace('-', '_')
            odoo_field = translated_mapping.get(
                normalized, AUTO_MAPPING.get(normalized, "")
            )
            mapping[col] = odoo_field

        self.write({
            'detected_columns': json.dumps(columns, ensure_ascii=False),
            'column_mapping': json.dumps(mapping, ensure_ascii=False),
            'state': 'mapping',
        })
        return self._reopen_wizard()

    def action_preview(self):
        """Step 2 → Step 3: Show preview of mapped data."""
        self.ensure_one()
        _ensure_civil_admin(self.env)
        rows = self._parse_file()
        mapping = json.loads(self.column_mapping or '{}')

        active_mapping = {
            ext_col: odoo_field
            for ext_col, odoo_field in mapping.items()
            if odoo_field and odoo_field in IMPORTABLE_FIELDS
        }
        if not active_mapping:
            raise UserError(_("Aucune correspondance de colonne valide n'a été définie."))

        self.line_ids.unlink()
        line_values = []
        for index, row in enumerate(rows, start=2):
            mapped = {}
            for ext_col, odoo_field in active_mapping.items():
                raw_value = row.get(ext_col, "")
                if raw_value is None:
                    continue
                try:
                    mapped.update(
                        self._map_row({ext_col: str(raw_value)}, {ext_col: odoo_field}, index)
                    )
                except ValidationError:
                    mapped[odoo_field] = str(raw_value).strip()
            line_values.append({
                "wizard_id": self.id,
                "line_number": index,
                **{
                    field_name: str(mapped.get(field_name, "") or "")
                    for field_name in IMPORTABLE_FIELD_ORDER
                },
            })
        if line_values:
            self.env["etat.civil.import.line"].create(line_values)

        self.write({
            'preview_data': json.dumps(
                [
                    {
                        field_name: getattr(line, field_name)
                        for field_name in IMPORTABLE_FIELD_ORDER
                    }
                    for line in self.line_ids[:20]
                ],
                ensure_ascii=False,
                indent=2,
            ),
            'state': 'preview',
        })
        self.action_validate_preview()
        return self._reopen_wizard()

    def action_download_template(self):
        self.ensure_one()
        _ensure_civil_admin(self.env)
        fields_get = self.env["etat.civil.individu"].fields_get(
            IMPORTABLE_FIELDS, ["string"]
        )
        headers = [fields_get[name]["string"] for name in IMPORTABLE_FIELD_ORDER]
        output = io.StringIO()
        csv.writer(output).writerow(headers)
        self.write({
            "template_file": base64.b64encode(output.getvalue().encode("utf-8-sig")),
            "template_file_name": "modele_import_citoyens.csv",
        })
        return {
            "type": "ir.actions.act_url",
            "url": (
                "/web/content?model=%s&id=%s&field=template_file"
                "&filename_field=template_file_name&download=true"
                % (self._name, self.id)
            ),
            "target": "self",
        }

    def action_validate_preview(self):
        self.ensure_one()
        _ensure_civil_admin(self.env)
        error_details = []
        duplicate_count = 0
        Individu = self.env["etat.civil.individu"]
        for line in self.line_ids:
            try:
                vals = self._line_to_vals(line)
                existing = self._find_duplicate(vals, Individu)
                line.write({
                    "error_message": False,
                    "duplicate_record_id": existing.id if existing else False,
                })
                if existing:
                    duplicate_count += 1
            except ValidationError as error:
                message = str(error)
                line.error_message = message
                line.duplicate_record_id = False
                error_details.append(
                    _("Ligne %d : %s") % (line.line_number, message)
                )
        self.write({
            "result_total": len(self.line_ids),
            "result_errors": len(error_details),
            "result_duplicates": duplicate_count,
            "result_details": "\n".join(error_details[:100]),
            "result_error_file": False if not error_details else self.result_error_file,
            "result_error_file_name": (
                False if not error_details else self.result_error_file_name
            ),
        })
        return self._reopen_wizard()

    def _line_to_vals(self, line):
        active_mapping = {
            field_name: field_name
            for field_name in IMPORTABLE_FIELDS
            if getattr(line, field_name)
        }
        vals = self._map_row(
            {
                field_name: getattr(line, field_name) or ""
                for field_name in active_mapping
            },
            active_mapping,
            line.line_number,
        )
        if not vals.get("nom"):
            raise ValidationError(_("Le nom est obligatoire."))
        if vals.get("sexe") not in ("M", "F"):
            raise ValidationError(_("Le sexe doit être Masculin ou Féminin."))
        if not vals.get("date_naissance"):
            raise ValidationError(_("La date de naissance est obligatoire."))
        if vals.get("cin") and not re.fullmatch(r"[0-9]{12}", vals["cin"]):
            raise ValidationError(_("Le numéro de CIN doit contenir exactement 12 chiffres."))
        birth_date = fields.Date.to_date(vals["date_naissance"])
        if birth_date > fields.Date.context_today(self):
            raise ValidationError(_("La date de naissance ne peut pas être dans le futur."))
        if vals.get("statut_vital") and vals["statut_vital"] not in (
            "vivant", "decede", "presume_disparu", "presume_mort", "autre"
        ):
            raise ValidationError(_("Le statut vital n'est pas reconnu."))
        if vals.get("situation_matrimoniale") and vals[
            "situation_matrimoniale"
        ] not in ("celibataire", "marie", "divorce", "veuf"):
            raise ValidationError(_("La situation matrimoniale n'est pas reconnue."))
        return vals

    def action_import(self):
        self.ensure_one()
        _ensure_civil_admin(self.env)
        try:
            if not self.line_ids:
                self.action_preview()
            self.action_validate_preview()
            invalid_lines = self.line_ids.filtered("error_message")
            if invalid_lines:
                details = [
                    _("Ligne %d : %s") % (line.line_number, line.error_message)
                    for line in invalid_lines
                ]
                self.write({
                    "result_details": "\n".join(details[:100]),
                    "result_errors": len(invalid_lines),
                    "result_error_file": base64.b64encode(
                        "\n".join(details).encode("utf-8")
                    ),
                    "result_error_file_name": "rapport_erreurs_import.txt",
                    "state": "preview",
                })
                return self._reopen_wizard()
            with self.env.cr.savepoint():
                return self._action_import()
        except Exception:
            _create_exchange_log(
                self.env,
                "import",
                "failed",
                self.file_name,
                self.file_format,
                error_rows=1,
            )
            raise

    def _action_import(self):
        """Import only rows that have been reviewed and validated."""
        self.ensure_one()
        _ensure_civil_admin(self.env)
        if not self.line_ids:
            raise UserError(_("Aucune ligne à importer n'est disponible dans l'aperçu."))

        Individu = self.env['etat.civil.individu']
        total = len(self.line_ids)
        imported = 0
        updated = 0
        duplicates = 0
        skipped = 0
        errors = 0
        error_details = []

        for line in self.line_ids:
            vals = self._line_to_vals(line)
            existing = self._find_duplicate(vals, Individu)
            if existing:
                duplicates += 1
                if self.duplicate_strategy == "skip":
                    skipped += 1
                    continue
                if self.duplicate_strategy == "update":
                    update_vals = {
                        key: value for key, value in vals.items()
                        if value and key != "cin"
                    }
                    if update_vals:
                        existing._write_from_import(update_vals)
                        updated += 1
                    else:
                        skipped += 1
                    continue
                error_details.append(
                    _("Ligne %d : doublon détecté, aucune création effectuée.")
                    % line.line_number
                )
                skipped += 1
                continue
            try:
                with self.env.cr.savepoint():
                    Individu._create_from_import([vals])
                    imported += 1
            except (ValidationError, UserError) as error:
                errors += 1
                error_details.append(
                    _("Ligne %d : %s") % (line.line_number, str(error))
                )
            except Exception:
                errors += 1
                error_details.append(
                    _("Ligne %d : erreur inattendue lors de l'enregistrement.")
                    % line.line_number
                )
                _logger.exception("Import error at line %d", line.line_number)

        # Generate error report file
        error_file = False
        error_file_name = False
        if error_details:
            report_text = '\n'.join(error_details)
            error_file = base64.b64encode(report_text.encode('utf-8'))
            error_file_name = 'rapport_erreurs_import.txt'

        _create_exchange_log(
            self.env,
            "import",
            "partial" if errors or (duplicates and self.duplicate_strategy == "report") else "success",
            self.file_name,
            self.file_format,
            total_rows=total,
            imported_rows=imported,
            updated_rows=updated,
            skipped_rows=skipped,
            duplicate_rows=duplicates,
            error_rows=errors,
        )
        self.write({
            'state': 'done',
            'result_total': total,
            'result_imported': imported,
            'result_updated': updated,
            'result_duplicates': duplicates,
            'result_skipped': skipped,
            'result_errors': errors,
            'result_details': '\n'.join(error_details[:100]) if error_details else _("Importation terminée sans erreur."),
            'result_error_file': error_file,
            'result_error_file_name': error_file_name,
        })
        return self._reopen_wizard()


    def _map_row(self, row, active_mapping, line_num):
        """Map a single row from external columns to Odoo fields."""
        vals = {}
        for ext_col, odoo_field in active_mapping.items():
            raw_val = (row.get(ext_col) or '').strip()
            if not raw_val:
                continue
            if odoo_field == 'sexe':
                raw_lower = raw_val.lower()
                if raw_lower in ('m', 'masculin', 'male', 'homme', 'h', 'lahy'):
                    vals['sexe'] = 'M'
                elif raw_lower in ('f', 'féminin', 'feminin', 'female', 'femme', 'vavy'):
                    vals['sexe'] = 'F'
                else:
                    vals['sexe'] = raw_val
            elif odoo_field == 'date_naissance':
                vals['date_naissance'] = self._parse_date(raw_val, line_num)
            elif odoo_field == 'statut_vital':
                raw_lower = raw_val.lower()
                if raw_lower in ('vivant', 'alive', 'living', 'v', 'velona'):
                    vals['statut_vital'] = 'vivant'
                elif raw_lower in ('décédé', 'decede', 'dead', 'deceased', 'd', 'maty'):
                    vals['statut_vital'] = 'decede'
                elif raw_lower in (
                    'disparu', 'missing', 'presumed_missing', 'heverina fa tsy hita'
                ):
                    vals['statut_vital'] = 'presume_disparu'
                else:
                    vals['statut_vital'] = raw_val
            elif odoo_field == 'situation_matrimoniale':
                raw_lower = raw_val.lower()
                sm_map = {
                    'célibataire': 'celibataire', 'celibataire': 'celibataire',
                    'single': 'celibataire', 'tsy manambady': 'celibataire',
                    'marié': 'marie', 'mariée': 'marie', 'marie': 'marie',
                    'married': 'marie', 'manambady': 'marie',
                    'divorcé': 'divorce', 'divorcée': 'divorce', 'divorce': 'divorce',
                    'divorced': 'divorce',
                    'veuf': 'veuf', 'veuve': 'veuf', 'widowed': 'veuf',
                    'mpitondratena': 'veuf', 'maty vady': 'veuf',
                }
                vals['situation_matrimoniale'] = sm_map.get(raw_lower, raw_val)
            elif odoo_field == 'date_naissance_estimee':
                raw_lower = raw_val.lower()
                vals['date_naissance_estimee'] = raw_lower in (
                    'true', 'oui', '1', 'yes', 'vrai', 'eny'
                )
            else:
                vals[odoo_field] = raw_val
        return vals

    def _parse_date(self, raw_val, line_num):
        """Parse a date string to YYYY-MM-DD format."""
        import re
        from datetime import datetime
        patterns = [
            ('%Y-%m-%d', None),
            ('%d/%m/%Y', None),
            ('%d-%m-%Y', None),
            ('%m/%d/%Y', None),
            ('%Y/%m/%d', None),
            ('%d.%m.%Y', None),
        ]
        for fmt, _ in patterns:
            try:
                dt = datetime.strptime(raw_val.strip(), fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        # Try ISO format
        try:
            dt = datetime.fromisoformat(raw_val.strip()[:10])
            return dt.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            pass
        raise ValidationError(
            _("Ligne %d : date de naissance invalide '%s'. Formats acceptés : YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY.")
            % (line_num, raw_val)
        )

    def _find_duplicate(self, vals, Individu):
        """Check if a citizen already exists based on CIN or reliable composite criteria.

        Never match on name alone, as multiple people can share identical names.
        """
        cin = (vals.get('cin') or '').strip()
        if cin:
            existing = Individu.search([('cin', '=', cin)], limit=1)
            if existing:
                return existing

        nom = (vals.get('nom') or '').strip()
        prenoms = (vals.get('prenoms') or '').strip()
        date_naissance = vals.get('date_naissance')
        commune = (vals.get('lieu_naissance_commune') or '').strip()

        # Reliable composite check: match on nom + date_naissance + (prenoms or commune)
        if nom and date_naissance and (prenoms or commune):
            domain = [
                ('nom', '=ilike', nom),
                ('date_naissance', '=', date_naissance),
            ]
            if prenoms:
                domain.append(('prenoms', '=ilike', prenoms))
            if commune:
                domain.append(('lieu_naissance_commune', '=ilike', commune))
            existing = Individu.search(domain, limit=1)
            if existing:
                return existing

        return False

    def _reopen_wizard(self):
        """Return action to re-open this wizard at its current state."""
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_back_to_mapping(self):
        """Go back from preview to mapping step."""
        self.ensure_one()
        _ensure_civil_admin(self.env)
        self.state = 'mapping'
        return self._reopen_wizard()

    def action_back_to_upload(self):
        """Go back from mapping to upload step."""
        self.ensure_one()
        _ensure_civil_admin(self.env)
        self.state = 'upload'
        return self._reopen_wizard()


class EtatCivilExportWizard(models.TransientModel):
    _name = "etat.civil.export.wizard"
    _description = "Assistant d'exportation des citoyens"

    export_format = fields.Selection(
        [
            ("xlsx", "Excel (.xlsx)"),
            ("csv", "CSV"),
            ("ods", "ODS"),
            ("pdf", "PDF"),
            ("json", "JSON"),
            ("xml", "XML"),
        ],
        string="Format",
        default="xlsx",
        required=True,
    )
    export_filter = fields.Selection(
        [("all", "Tous les statuts vitaux"), ("vivant", "Vivants uniquement"),
         ("decede", "Décédés uniquement"), ("presume_disparu", "Présumés disparus"),
         ("presume_mort", "Présumés morts")],
        string="Statut vital",
        default="all",
        required=True,
    )
    marital_filter = fields.Selection(
        [
            ("all", "Toutes les situations matrimoniales"),
            ("celibataire", "Célibataires"),
            ("marie", "Mariés"),
            ("divorce", "Divorcés"),
            ("veuf", "Veufs ou veuves"),
        ],
        string="Situation matrimoniale",
        default="all",
        required=True,
    )
    sex_filter = fields.Selection(
        [("all", "Tous"), ("M", "Masculin"), ("F", "Féminin")],
        string="Sexe",
        default="all",
        required=True,
    )
    age_min = fields.Integer(string="Âge minimum")
    age_max = fields.Integer(string="Âge maximum")
    filter_age_min = fields.Boolean(string="Activer l'âge minimum")
    filter_age_max = fields.Boolean(string="Activer l'âge maximum")
    selection_mode = fields.Selection(
        [("filtered", "Toutes les personnes correspondant aux filtres"),
         ("selected", "Sélection manuelle")],
        string="Personnes à exporter",
        default="filtered",
        required=True,
    )
    selected_individu_ids = fields.Many2many(
        "etat.civil.individu",
        "etat_civil_export_individu_rel",
        "wizard_id",
        "individu_id",
        string="Personnes sélectionnées",
    )
    include_all_fields = fields.Boolean(string="Tous les champs exportables", default=True)
    export_field_ids = fields.Many2many(
        "ir.model.fields",
        "etat_civil_export_field_rel",
        "wizard_id",
        "field_id",
        string="Champs à exporter",
        domain=[
            ("model", "=", "etat.civil.individu"),
            ("name", "in", EXPORTABLE_FIELDS),
        ],
    )
    language = fields.Selection(
        [("fr_FR", "Français"), ("mg_MG", "Malagasy")],
        string="Langue du fichier",
        default="fr_FR",
        required=True,
    )
    pdf_layout = fields.Selection(
        [("table", "Liste tabulaire"), ("individual", "Fiche par personne")],
        string="Présentation du PDF",
        default="table",
    )
    result_file = fields.Binary(string="Fichier exporté", readonly=True)
    result_file_name = fields.Char(string="Nom du fichier", readonly=True)
    state = fields.Selection(
        [("config", "Configuration"), ("done", "Terminé")],
        default="config",
        string="Étape",
    )
    result_count = fields.Integer(string="Citoyens exportés", readonly=True)

    @api.constrains("age_min", "age_max")
    def _check_age_range(self):
        for wizard in self:
            if wizard.age_min < 0 or wizard.age_max < 0:
                raise ValidationError(_("Les âges ne peuvent pas être négatifs."))
            if wizard.age_min and wizard.age_max and wizard.age_min > wizard.age_max:
                raise ValidationError(
                    _("L'âge minimum ne peut pas dépasser l'âge maximum.")
                )

    def action_select_all_fields(self):
        self.ensure_one()
        _ensure_civil_admin(self.env)
        all_fields = self.env["ir.model.fields"].search([
            ("model", "=", "etat.civil.individu"),
            ("name", "in", EXPORTABLE_FIELDS),
        ])
        self.write({
            "include_all_fields": False,
            "export_field_ids": [(6, 0, all_fields.ids)],
        })
        return True

    def _get_domain(self):
        self.ensure_one()
        domain = []
        if self.export_filter != "all":
            domain.append(("statut_vital", "=", self.export_filter))
        if self.marital_filter != "all":
            domain.append(("situation_matrimoniale", "=", self.marital_filter))
        if self.sex_filter != "all":
            domain.append(("sexe", "=", self.sex_filter))
        today = fields.Date.context_today(self)
        if self.filter_age_min:
            domain.append((
                "date_naissance", "<=",
                today - relativedelta(years=self.age_min),
            ))
        if self.filter_age_max:
            earliest_date = today - relativedelta(years=self.age_max + 1)
            domain.append(("date_naissance", ">=", earliest_date + relativedelta(days=1)))
        if self.selection_mode == "selected":
            if not self.selected_individu_ids:
                raise UserError(_("Sélectionnez au moins une personne à exporter."))
            domain.append(("id", "in", self.selected_individu_ids.ids))
        return domain

    def _get_fields(self):
        self.ensure_one()
        if self.include_all_fields:
            return list(EXPORTABLE_FIELDS)
        selected = set(self.export_field_ids.mapped("name"))
        field_list = [name for name in EXPORTABLE_FIELDS if name in selected]
        if not field_list:
            raise UserError(_("Sélectionnez au moins un champ à exporter."))
        return field_list

    def _get_records(self):
        self.ensure_one()
        return self.env["etat.civil.individu"].search(
            self._get_domain(), order="nom, prenoms, id"
        )

    def _get_field_labels(self, field_list):
        fields_info = self.env["etat.civil.individu"].with_context(
            lang=self.language
        ).fields_get(field_list, ["string", "selection"])
        return {
            name: fields_info[name]["string"]
            for name in field_list
        }, fields_info

    def _records_to_dicts(self, records, field_list, fields_info=None):
        self.ensure_one()
        if fields_info is None:
            _, fields_info = self._get_field_labels(field_list)
        localized_yes = "Eny" if self.language == "mg_MG" else "Oui"
        localized_no = "Tsia" if self.language == "mg_MG" else "Non"
        result = []
        for record in records:
            values = {}
            for field_name in field_list:
                value = record[field_name]
                field_info = fields_info[field_name]
                if field_info.get("selection") and value:
                    value = dict(field_info["selection"]).get(value, value)
                elif isinstance(value, datetime):
                    value = value.strftime("%d/%m/%Y %H:%M")
                elif hasattr(value, "strftime"):
                    value = value.strftime("%d/%m/%Y")
                elif isinstance(value, bool):
                    value = localized_yes if value else localized_no
                elif value is False or value is None:
                    value = ""
                else:
                    value = str(value)
                values[field_name] = value
            result.append(values)
        return result

    def _get_export_data(self):
        self.ensure_one()
        wizard = self.with_context(lang=self.language)
        field_list = wizard._get_fields()
        records = wizard._get_records()
        labels, fields_info = wizard._get_field_labels(field_list)
        rows = wizard._records_to_dicts(records, field_list, fields_info)
        return records, field_list, labels, fields_info, rows

    def _get_export_criteria(self):
        self.ensure_one()
        return {
            "age_min": self.age_min if self.filter_age_min else None,
            "age_max": self.age_max if self.filter_age_max else None,
            "sex": self.sex_filter,
            "vital_status": self.export_filter,
            "marital_status": self.marital_filter,
            "selection_mode": self.selection_mode,
            "selected_ids": (
                self.selected_individu_ids.ids
                if self.selection_mode == "selected" else []
            ),
            "pdf_layout": self.pdf_layout if self.export_format == "pdf" else None,
        }

    def action_export(self):
        self.ensure_one()
        _ensure_civil_admin(self.env)
        try:
            with self.env.cr.savepoint():
                return self._action_export()
        except Exception:
            _create_exchange_log(
                self.env,
                "export",
                "failed",
                False,
                self.export_format,
                criteria=self._get_export_criteria(),
                exported_fields=(
                    EXPORTABLE_FIELDS if self.include_all_fields
                    else self.export_field_ids.mapped("name")
                ),
                language=self.language,
            )
            raise

    def _action_export(self):
        self.ensure_one()
        _ensure_civil_admin(self.env)
        records, field_list, labels, fields_info, data = self._get_export_data()
        file_format = self.export_format
        if file_format == "csv":
            content, file_name = self._export_csv(data, field_list, labels)
        elif file_format == "xlsx":
            content, file_name = self._export_xlsx(data, field_list, labels)
        elif file_format == "json":
            content, file_name = self._export_json(data, field_list, labels)
        elif file_format == "xml":
            content, file_name = self._export_xml(data, field_list, labels)
        elif file_format == "ods":
            content, file_name = self._export_ods(data, field_list, labels)
        elif file_format == "pdf":
            report_data = {
                "language": self.language,
                "pdf_layout": self.pdf_layout,
            }
            content, _ = self.env["ir.actions.report"].with_context(
                lang=self.language,
                force_report_rendering=True,
                landscape=self.pdf_layout == "table",
            )._render_qweb_pdf(
                "etat_civil.action_report_citizen_export",
                res_ids=self.ids,
                data=report_data,
            )
            file_name = "citoyens_export.pdf"
        else:
            raise UserError(_("Format d'exportation non pris en charge."))

        self.write({
            "result_file": base64.b64encode(content),
            "result_file_name": file_name,
            "result_count": len(records),
            "state": "done",
        })
        _create_exchange_log(
            self.env,
            "export",
            "success",
            file_name,
            file_format,
            total_rows=len(records),
            criteria=self._get_export_criteria(),
            exported_fields=field_list,
            language=self.language,
        )
        return self._reopen_wizard()

    def _export_csv(self, data, field_list, labels=None):
        labels = labels or {name: name for name in field_list}
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([labels[name] for name in field_list])
        for row in data:
            writer.writerow([
                _escape_spreadsheet_formula(row.get(name, ""))
                for name in field_list
            ])
        return output.getvalue().encode("utf-8-sig"), "citoyens_export.csv"

    def _export_xlsx(self, data, field_list, labels=None):
        try:
            import openpyxl
        except ImportError as error:
            raise UserError(
                _("La bibliothèque 'openpyxl' est nécessaire pour exporter en Excel.")
            ) from error
        labels = labels or {name: name for name in field_list}
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = (
            "Olom-pirenena" if self.language == "mg_MG" else "Citoyens"
        )
        worksheet.append([labels[name] for name in field_list])
        for row in data:
            worksheet.append([
                row.get(name, "")
                for name in field_list
            ])
            for cell in worksheet[worksheet.max_row]:
                cell.data_type = "s"
        buffer = io.BytesIO()
        workbook.save(buffer)
        return buffer.getvalue(), "citoyens_export.xlsx"

    def _export_json(self, data, field_list=None, labels=None):
        labels = labels or {name: name for name in (field_list or [])}
        if field_list:
            data = [
                {labels[name]: row.get(name, "") for name in field_list}
                for row in data
            ]
        collection_label = (
            "Olom-pirenena" if self.language == "mg_MG" else "Citoyens"
        )
        return (
            json.dumps(
                {"label": collection_label, "citoyens": data},
                ensure_ascii=False,
                indent=2,
            ).encode("utf-8"),
            "citoyens_export.json",
        )

    def _export_xml(self, data, field_list, labels=None):
        import xml.etree.ElementTree as ET

        labels = labels or {name: name for name in field_list}
        root = ET.Element("citoyens")
        root.set(
            "label",
            "Olom-pirenena" if self.language == "mg_MG" else "Citoyens",
        )
        for row in data:
            person = ET.SubElement(root, "citoyen")
            for name in field_list:
                element = ET.SubElement(person, name)
                element.set("label", labels[name])
                element.text = row.get(name, "")
        buffer = io.BytesIO()
        ET.ElementTree(root).write(buffer, encoding="utf-8", xml_declaration=True)
        return buffer.getvalue(), "citoyens_export.xml"

    def _export_ods(self, data, field_list, labels=None):
        try:
            from odf.opendocument import OpenDocumentSpreadsheet
            from odf.table import Table, TableRow, TableCell
            from odf.text import P
        except ImportError as error:
            raise UserError(
                _("La bibliothèque 'odfpy' est nécessaire pour exporter en ODS.")
            ) from error
        labels = labels or {name: name for name in field_list}
        document = OpenDocumentSpreadsheet()
        table = Table(
            name="Olom-pirenena" if self.language == "mg_MG" else "Citoyens"
        )
        header = TableRow()
        for name in field_list:
            cell = TableCell()
            cell.addElement(P(text=labels[name]))
            header.addElement(cell)
        table.addElement(header)
        for row in data:
            table_row = TableRow()
            for name in field_list:
                cell = TableCell()
                cell.addElement(P(text=row.get(name, "")))
                table_row.addElement(cell)
            table.addElement(table_row)
        document.spreadsheet.addElement(table)
        buffer = io.BytesIO()
        document.save(buffer)
        return buffer.getvalue(), "citoyens_export.ods"

    def _reopen_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }


class ReportEtatCivilCitizenExport(models.AbstractModel):
    _name = "report.etat_civil.report_citizen_export"
    _description = "Rapport d'exportation des citoyens"

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        language = data.get("language", "fr_FR")
        wizard = self.env["etat.civil.export.wizard"].browse(docids).with_context(
            lang=language
        )
        _ensure_civil_admin(wizard.env)
        records, field_list, labels, _fields_info, values = wizard._get_export_data()
        rows = [
            {
                "values": [
                    {"label": labels[name], "value": row.get(name, "")}
                    for name in field_list
                ]
            }
            for row in values
        ]
        return {
            "doc_ids": wizard.ids,
            "doc_model": wizard._name,
            "docs": wizard,
            "headers": [labels[name] for name in field_list],
            "rows": rows,
            "pdf_layout": data.get("pdf_layout", "table"),
            "result_count": len(records),
        }

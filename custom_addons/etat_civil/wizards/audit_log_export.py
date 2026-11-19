import csv
import io
import json

from odoo import api, fields, models, _
from odoo.exceptions import AccessError


class AuditLogExportWizard(models.TransientModel):
    _name = "etat.civil.audit.log.export.wizard"
    _description = "Wizard d'export du journal d'audit"

    export_format = fields.Selection(
        [
            ("csv", "CSV"),
            ("xlsx", "Excel (.xlsx)"),
        ],
        string="Format d'export",
        required=True,
        default="csv",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Utilisateur",
        help="Laisser vide pour exporter tous les utilisateurs.",
    )
    action_type = fields.Selection(
        selection="_get_action_types",
        string="Type d'action",
        help="Laisser vide pour exporter tous les types.",
    )
    date_from = fields.Date(
        string="Date de début",
        help="Laisser vide pour ne pas filtrer par date de début.",
    )
    date_to = fields.Date(
        string="Date de fin",
        help="Laisser vide pour ne pas filtrer par date de fin.",
    )
    data_file = fields.Binary(
        string="Fichier à télécharger",
        readonly=True,
        copy=False,
    )
    filename = fields.Char(
        string="Nom du fichier",
        readonly=True,
        copy=False,
    )

    @api.model
    def _get_action_types(self):
        return self.env["etat.civil.audit.log"]._fields["action_type"].selection

    def action_export(self):
        self.ensure_one()
        user = self.env.user

        # Vérification des droits : seul l'admin peut exporter
        if not (
            user.has_group("etat_civil.group_etat_civil_admin")
            or user.has_group("base.group_system")
        ):
            raise AccessError(
                _("Seul un administrateur peut exporter le journal d'audit.")
            )

        # Récupération des enregistrements filtrés
        domain = []
        if self.user_id:
            domain.append(("user_id", "=", self.user_id.id))
        if self.action_type:
            domain.append(("action_type", "=", self.action_type))
        if self.date_from:
            domain.append(("event_datetime_utc", ">=", fields.Datetime.to_datetime(self.date_from)))
        if self.date_to:
            domain.append(
                ("event_datetime_utc", "<=", fields.Datetime.to_datetime(self.date_to) + __import__("datetime").timedelta(days=1) - __import__("datetime").timedelta(seconds=1))
            )

        logs = self.env["etat.civil.audit.log"].search(domain, order="event_datetime_utc desc")

        if not logs:
            raise AccessError(_("Aucun événement d'audit ne correspond aux filtres sélectionnés."))

        # Génération du fichier
        if self.export_format == "csv":
            return self._generate_csv(logs)
        else:
            return self._generate_xlsx(logs)

    def _generate_csv(self, logs):
        output = io.StringIO()
        writer = csv.writer(output)

        # En-têtes
        writer.writerow([
            "Date/Heure (UTC)",
            "Date/Heure (locale)",
            "Utilisateur",
            "Identifiant de connexion",
            "Rôle",
            "Commune",
            "Type d'action",
            "Modèle concerné",
            "ID enregistrement",
            "Résultat",
            "Détails",
        ])

        # Lignes
        for log in logs:
            details = log.details or ""
            try:
                details = json.loads(details) if isinstance(details, str) else details
                details = str(details)
            except (json.JSONDecodeError, ValueError):
                pass

            writer.writerow([
                log.event_datetime_utc or "",
                log.event_datetime_local or "",
                log.user_id.name if log.user_id else "",
                log.user_login or "",
                log.role or "",
                log.commune or "",
                log.action_type or "",
                log.record_model or "",
                log.record_id or "",
                log.result or "",
                details,
            ])

        csv_data = output.getvalue().encode("utf-8-sig")
        self.data_file = csv_data
        self.filename = f"journal_audit_{fields.Date.today().strftime('%Y%m%d')}.csv"

        return {
            "type": "ir.actions.act_window",
            "res_model": "etat.civil.audit.log.export.wizard",
            "view_mode": "form",
            "target": "new",
            "res_id": self.id,
        }

    def _generate_xlsx(self, logs):
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill
        except ImportError:
            raise AccessError(
                _("La bibliothèque openpyxl est requise pour l'export Excel. "
                  "Installez-la avec : pip install openpyxl")
            )

        wb = Workbook()
        ws = wb.active
        ws.title = "Journal d'audit"

        # Styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # En-têtes
        headers = [
            "Date/Heure (UTC)",
            "Date/Heure (locale)",
            "Utilisateur",
            "Identifiant de connexion",
            "Rôle",
            "Commune",
            "Type d'action",
            "Modèle concerné",
            "ID enregistrement",
            "Résultat",
            "Détails",
        ]
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment

        # Lignes
        for row_idx, log in enumerate(logs, start=2):
            details = log.details or ""
            try:
                details = json.loads(details) if isinstance(details, str) else details
                details = str(details)
            except (json.JSONDecodeError, ValueError):
                pass

            ws.cell(row=row_idx, column=1, value=log.event_datetime_utc).number_format = "YYYY-MM-DD HH:MM:SS"
            ws.cell(row=row_idx, column=2, value=log.event_datetime_local)
            ws.cell(row=row_idx, column=3, value=log.user_id.name if log.user_id else "")
            ws.cell(row=row_idx, column=4, value=log.user_login or "")
            ws.cell(row=row_idx, column=5, value=log.role or "")
            ws.cell(row=row_idx, column=6, value=log.commune or "")
            ws.cell(row=row_idx, column=7, value=log.action_type or "")
            ws.cell(row=row_idx, column=8, value=log.record_model or "")
            ws.cell(row=row_idx, column=9, value=log.record_id or 0)
            ws.cell(row=row_idx, column=10, value=log.result or "")
            ws.cell(row=row_idx, column=11, value=details)

        # Ajustement des largeurs de colonnes
        for col in ws.columns:
            max_length = 0
            column_letter = col[0].column_letter
            for cell in col:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            ws.column_dimensions[column_letter].width = min(max_length + 2, 50)

        # Génération du fichier
        output = io.BytesIO()
        wb.save(output)
        xlsx_data = output.getvalue()

        self.data_file = xlsx_data
        self.filename = f"journal_audit_{fields.Date.today().strftime('%Y%m%d')}.xlsx"

        return {
            "type": "ir.actions.act_window",
            "res_model": "etat.civil.audit.log.export.wizard",
            "view_mode": "form",
            "target": "new",
            "res_id": self.id,
        }

    def action_download(self):
        self.ensure_one()
        if not self.data_file:
            raise AccessError(_("Aucun fichier à télécharger. Générez d'abord l'export."))

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/etat.civil.audit.log.export.wizard/{self.id}/data_file?download=true{f'&filename={self.filename}' if self.filename else ''}",
            "target": "self",
        }

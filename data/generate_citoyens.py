import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Citoyens"

# En-têtes
headers = [
    "nom", "prenoms", "cin", "sexe", "date_naissance",
    "date_naissance_estimee", "lieu_naissance_commune",
    "lieu_naissance_pays", "nationalite_actuelle", "domicile_actuel",
    "profession_actuelle", "statut_vital", "situation_matrimoniale"
]

# Styles
header_font = Font(bold=True, color="FFFFFF")
header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
thin_border = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

# Écrire les en-têtes
for col, header in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=header)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = header_alignment
    cell.border = thin_border

# Données fictives de citoyens malagasy (tous nés à Fianarantsoa)
data = [
    ("Rakoto", "Jean Michel", "100198500001", "M", "1985-03-15", False,
     "Fianarantsoa", "Madagascar", "Malagasy",
     "Lot II N°45, Analakely, Fianarantsoa 401", "Enseignant", "vivant", "marie"),

    ("Rasoa", "Marie Claire", "100199000002", "F", "1990-07-22", False,
     "Fianarantsoa", "Madagascar", "Malagasy",
     "Tsiafahiny, Fianarantsoa 401", "Infirmière", "vivant", "celibataire"),

    ("Andria", "François", "100197800003", "M", "1978-11-05", False,
     "Fianarantsoa", "Madagascar", "Malagasy",
     "Ambodivona, Fianarantsoa 401", "Commerçant", "vivant", "marie"),

    ("Be", "Sophie Raharimanana", "100199500004", "F", "1995-01-30", False,
     "Fianarantsoa", "Madagascar", "Malagasy",
     "Lot I N°12, Ambodivona, Fianarantsoa 401", "Avocate", "vivant", "celibataire"),

    ("Rajaonarivelo", "Hery", "100196000005", "M", "1960-06-18", False,
     "Fianarantsoa", "Madagascar", "Malagasy",
     "Ambohimanga, Fianarantsoa 401", "Retraité", "vivant", "veuf"),

    ("Voahirana", "Nirina", "100198800006", "F", "1988-09-12", False,
     "Fianarantsoa", "Madagascar", "Malagasy",
     "Ambodirano, Fianarantsoa 401", "Médecin", "vivant", "marie"),

    ("Randria", "Tiana", "100197200007", "F", "1972-04-25", False,
     "Fianarantsoa", "Madagascar", "Malagasy",
     "Lot IV N°78, Isotry, Fianarantsoa 401", "Pharmacien", "vivant", "divorce"),

    ("Njara", "Andry", "100200000008", "M", "2000-12-03", False,
     "Fianarantsoa", "Madagascar", "Malagasy",
     "Lot I N°5, Fianarantsoa 401", "Étudiant", "vivant", "celibataire"),

    ("Rakotonirina", "Voahirana", "100195500009", "F", "1955-08-14", False,
     "Fianarantsoa", "Madagascar", "Malagasy",
     "Ambalabe, Fianarantsoa 401", "Retraité", "decede", "veuve"),

    ("Haja", "Fidovolonirina", "100199200010", "F", "1992-02-28", False,
     "Fianarantsoa", "Madagascar", "Malagasy",
     "Lot III N°33, Alasora, Fianarantsoa 401", "Comptable", "vivant", "marie"),

    ("Ravelo", "M-bah", "100198300011", "M", "1983-05-09", False,
     "Fianarantsoa", "Madagascar", "Malagasy",
     "Amborovy, Fianarantsoa 401", "Ingénieur", "vivant", "marie"),

    ("Rajaona", "Hanta", "100199800012", "F", "1998-10-17", False,
     "Fianarantsoa", "Madagascar", "Malagasy",
     "Lot II N°21, Ambatobevy, Fianarantsoa 401", "Journaliste", "vivant", "celibataire"),

    ("Andriamampandry", "Solomon", "100196500013", "M", "1965-07-01", False,
     "Fianarantsoa", "Madagascar", "Malagasy",
     "Lot I N°9, Fianarantsoa 401", "Professeur", "vivant", "marie"),

    ("Rakotoharisoa", "Voahary", "100200300014", "F", "2003-03-20", False,
     "Fianarantsoa", "Madagascar", "Malagasy",
     "Ambodivona, Fianarantsoa 401", "Étudiante", "vivant", "celibataire"),

    ("Razafindrabe", "Tobiana", "100197500015", "M", "1975-12-11", False,
     "Fianarantsoa", "Madagascar", "Malagasy",
     "Lot II N°56, Ambalavojy, Fianarantsoa 401", "Agriculteur", "vivant", "marie"),

    ("Nirina", "Rakotonirina", "100194000016", "F", "1940-01-05", False,
     "Fianarantsoa", "Madagascar", "Malagasy",
     "Lot IV N°2, Analakely, Fianarantsoa 401", "Retraité", "decede", "veuve"),

    ("Rakotondrazaka", "Haja", "100199900017", "F", "1999-06-23", False,
     "Fianarantsoa", "Madagascar", "Malagasy",
     "Lot I N°44, Fianarantsoa 401", "Vétérinaire", "vivant", "celibataire"),

    ("Rajaonarison", "David", "100198700018", "M", "1987-04-08", False,
     "Fianarantsoa", "Madagascar", "Malagasy",
     "Ambodirano, Fianarantsoa 401", "Architecte", "vivant", "marie"),

    ("Be", "Fara", "100200100019", "F", "2001-09-15", False,
     "Fianarantsoa", "Madagascar", "Malagasy",
     "Lot III N°67, Isotry, Fianarantsoa 401", "Étudiante", "vivant", "celibataire"),

    ("Andriamanjato", "Rakoto", "100197000020", "M", "1970-11-30", False,
     "Fianarantsoa", "Madagascar", "Malagasy",
     "Ambalabe, Fianarantsoa 401", "Pêcheur", "vivant", "divorce"),
]

for row_idx, row_data in enumerate(data, 2):
    for col_idx, value in enumerate(row_data, 1):
        cell = ws.cell(row=row_idx, column=col_idx, value=value)
        cell.border = thin_border
        if col_idx == 5:  # date_naissance
            cell.number_format = 'YYYY-MM-DD'

# Ajuster la largeur des colonnes
column_widths = {
    "nom": 20,
    "prenoms": 25,
    "cin": 18,
    "sexe": 8,
    "date_naissance": 16,
    "date_naissance_estimee": 22,
    "lieu_naissance_commune": 22,
    "lieu_naissance_pays": 18,
    "nationalite_actuelle": 20,
    "domicile_actuel": 40,
    "profession_actuelle": 20,
    "statut_vital": 18,
    "situation_matrimoniale": 24,
}

for col, header in enumerate(headers, 1):
    ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = column_widths.get(header, 20)

# Sauvegarder
output_path = "/home/ulrich/tous_les_projet/stage_l3_odoo/data/import_citoyens_fictifs.xlsx"
wb.save(output_path)
print(f"Fichier créé avec succès : {output_path}")
print(f"Nombre de citoyens : {len(data)}")

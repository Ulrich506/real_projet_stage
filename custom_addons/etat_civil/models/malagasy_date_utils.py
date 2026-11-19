# -*- coding: utf-8 -*-
"""
Utilitaires de conversion des dates et heures en lettres malgache.

Utilisé par les templates d'impression des actes d'état civil pour écrire
les dates et heures en toutes lettres, conformément au format officiel
de la commune de Fianarantsoa.

Exemple :
    2026-01-02 → "roa janoary taona enina amby roapolo sy roa arivo"
    14:30 → "folo efatra ora, efapolo dimy isaky ny fetra"
"""

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

MOIS_MALGACHE = [
    None,  # index 0 inexistant
    "Janoary", "Febaoary", "Martsa", "Aprily", "Mey", "Jona",
    "Jolay", "Aogositra", "Septambra", "Oktobra", "Novambra", "Desambra",
]

# Nombres 1–16 en malgache (forme de base)
NOMBRES_1_16 = [
    None,  # 0
    "iray", "roa", "telo", "efatra", "dimy", "enina", "fito",
    "valo", "sivy", "folo", "ira ambin'ny folo", "lapy ambin'ny folo",
    "latsiny ambin'ny folo", "folo efatra", "folo dimy",
    "folo enina",
]

# Dizaines
DIZAINES = {
    2: "roapolo",
    3: "telopolo",
    4: "efatopolo",
    5: "dimy amby ny folo",
    6: "enina amby ny folo",
    7: "fito amby ny folo",
    8: "valo amby ny folo",
    9: "sivy amby ny folo",
}

# ---------------------------------------------------------------------------
# Conversion des nombres entiers (1–9999) en malgache
# ---------------------------------------------------------------------------


def nombre_to_malagasy_words(n: int) -> str:
    """
    Convertit un entier positif (1–99999) en lettres malgache.

    Exemples :
        1 → "iray"
        14 → "folo efatra"
        25 → "roapolo dimy"
        100 → "iray amby ny zato"
        50000 → "dimy arivo folo"
    """
    if n < 1 or n > 99999:
        return str(n)

    if n <= 16:
        return NOMBRES_1_16[n]

    if n < 100:
        return _nombre_10_99(n)

    if n < 1000:
        return _nombre_100_999(n)

    if n < 10000:
        return _nombre_1000_9999(n)

    return _nombre_10000_99999(n)


def _nombre_10_99(n: int) -> str:
    """Convertit 17–99 en malgache."""
    dizaine = n // 10
    unite = n % 10

    if unite == 0:
        return DIZAINES[dizaine]

    # Pour 20–39 : "roapolo iray", "telopolo dimy"
    # Pour 40–99 : "efatopolo iray", "dimy amby ny folo efatra"
    if dizaine <= 3:
        return f"{DIZAINES[dizaine]} {NOMBRES_1_16[unite]}"
    elif dizaine == 4:
        return f"efatopolo {NOMBRES_1_16[unite]}"
    else:
        # 50–99 : "dimy amby ny folo X"
        diz = DIZAINES[dizaine]
        return f"{diz} {NOMBRES_1_16[unite]}"


def _nombre_100_999(n: int) -> str:
    """Convertit 100–999 en malgache."""
    centaine = n // 100
    reste = n % 100

    if reste == 0:
        if centaine == 1:
            return "iray amby ny zato"
        return f"{nombre_to_malagasy_words(centaine)} amby ny zato"

    if centaine == 1:
        base = "iray amby ny zato"
    else:
        base = f"{nombre_to_malagasy_words(centaine)} amby ny zato"

    return f"{base} {nombre_to_malagasy_words(reste)}"


def _nombre_1000_9999(n: int) -> str:
    """Convertit 1000–9999 en malgache."""
    millier = n // 1000
    reste = n % 1000

    if reste == 0:
        if millier == 1:
            return "iray arivo"
        return f"{nombre_to_malagasy_words(millier)} arivo"

    if millier == 1:
        base = "iray arivo"
    else:
        base = f"{nombre_to_malagasy_words(millier)} arivo"

    return f"{base} {nombre_to_malagasy_words(reste)}"


def _nombre_10000_99999(n: int) -> str:
    """
    Convertit 10000–99999 en malgache.

    Format : "dimy arivo zato" pour 50000,
             "dimy arivo zato iray" pour 50001,
             "folo arivo" pour 10000.
    """
    # On décompose en dizaines de mille + reste
    dizaine_mille = n // 10000
    reste = n % 10000

    if reste == 0:
        if dizaine_mille == 1:
            return "folo arivo"
        return f"{nombre_to_malagasy_words(dizaine_mille)} arivo folo"

    if dizaine_mille == 1:
        base = "folo arivo"
    else:
        base = f"{nombre_to_malagasy_words(dizaine_mille)} arivo folo"

    return f"{base} {nombre_to_malagasy_words(reste)}"


# ---------------------------------------------------------------------------
# Conversion des années (format spécial malgache)
# ---------------------------------------------------------------------------


def year_to_malagasy_words(year: int) -> str:
    """
    Convertit une année en lettres malgache, avec le format spécial utilisé
    dans les actes d'état civil.

    Le format malgache pour les années 2000+ utilise une structure particulière :
        2026 → "enina amby roapolo sy roa arivo"
        2000 → "roa arivo"
        1961 → "iray arivo sivy amby ny zato enina amby ny folo iray"

    Pour les années 2000–2099, le format est :
        "{reste_formaté} sy roa arivo"
        où le reste (01–99) utilise le format "X amby Y" pour 20–49.
    """
    if year < 1000 or year > 3000:
        return str(year)

    millier = year // 1000
    reste = year % 1000

    if reste == 0:
        if millier == 1:
            return "iray arivo"
        return f"{nombre_to_malagasy_words(millier)} arivo"

    # Pour les années 2000–2099
    if millier == 2:
        if reste < 10:
            return f"{nombre_to_malagasy_words(reste)} sy roa arivo"
        if reste < 100:
            reste_texte = _annee_2000_reste(reste)
            return f"{reste_texte} sy roa arivo"
        return f"{nombre_to_malagasy_words(reste)} sy roa arivo"

    # Pour les années 1000–1999, format standard
    return f"{nombre_to_malagasy_words(year)}"


def _annee_2000_reste(n: int) -> str:
    """
    Convertit le reste d'une année 2000+ (10–99) en format spécial.

    Le format attendu pour 2026 est "enina amby roapolo" pour le reste 26.
    Cela signifie : unite + " amby " + dizaine.

    26 → "enina amby roapolo" (6 + 20)
    14 → "folo efatra" (format normal pour 10-16)
    35 → "dimy amby telopolo" (5 + 30)
    50 → "dimy amby ny folo"
    """
    if n < 17:
        return nombre_to_malagasy_words(n)

    dizaine = n // 10
    unite = n % 10

    if unite == 0:
        return DIZAINES[dizaine]

    # Pour 20–49 : format "X amby Y" (unite avant dizaine)
    if dizaine == 2:
        return f"{NOMBRES_1_16[unite]} amby roapolo"
    elif dizaine == 3:
        return f"{NOMBRES_1_16[unite]} amby telopolo"
    elif dizaine == 4:
        return f"{NOMBRES_1_16[unite]} amby efatopolo"
    else:
        # 50–99 : format normal "dizaine unite"
        return _nombre_10_99(n)


# ---------------------------------------------------------------------------
# Conversion des dates complètes
# ---------------------------------------------------------------------------


def date_to_malagasy_words(date_obj) -> str:
    """
    Convertit une date (datetime.date ou datetime.datetime) en lettres malgache.

    Retourne une chaîne comme :
        "roa janoary taona enina amby roapolo sy roa arivo"

    Pour 2026-01-02.
    """
    jour = date_obj.day
    mois = MOIS_MALGACHE[date_obj.month].lower()
    annee = year_to_malagasy_words(date_obj.year)

    jour_texte = nombre_to_malagasy_words(jour)

    return f"{jour_texte} {mois} taona {annee}"


# ---------------------------------------------------------------------------
# Conversion des heures
# ---------------------------------------------------------------------------


def time_to_malagasy_words(time_value) -> str:
    """
    Convertit une heure en lettres malgache.

    Accepte :
        - float (ex: 14.5 pour 14:30, format Odoo float_time)
        - datetime.time
        - datetime.datetime

    Retourne une chaîne comme :
        "folo efatra ora dimy amby ny folo minitra"
    """
    if isinstance(time_value, float):
        # Format Odoo : 14.5 = 14h30
        heure = int(time_value)
        minute = int(round((time_value - heure) * 60))
    elif hasattr(time_value, 'hour'):
        # datetime.time ou datetime.datetime
        heure = time_value.hour
        minute = time_value.minute
    else:
        return str(time_value)

    heure_texte = nombre_to_malagasy_words(heure)

    if minute == 0:
        return f"{heure_texte} ora"

    minute_texte = nombre_to_malagasy_words(minute)
    return f"{heure_texte} ora {minute_texte} minitra"


# ---------------------------------------------------------------------------
# Format court pour la sidebar (dates en chiffres avec mois malgache)
# ---------------------------------------------------------------------------


def date_to_malagasy_short(date_obj) -> str:
    """
    Convertit une date au format court avec mois en malgache.

    Retourne : "02 Janoary 2026"
    """
    jour = f"{date_obj.day:02d}"
    mois = MOIS_MALGACHE[date_obj.month]
    annee = date_obj.year
    return f"{jour} {mois} {annee}"


# ---------------------------------------------------------------------------
# Conversion des montants en lettres malgache (pour quittance)
# ---------------------------------------------------------------------------


def montant_to_malagasy_words(montant: float) -> str:
    """
    Convertit un montant numérique en lettres malgache suivi de "Ariary".

    Exemple :
        2000 → "roa arivo Ariary"
        1500 → "dimy amby ny zato sy iray arivo Ariary"
    """
    if montant <= 0:
        return "zero Ariary"

    partie_entiere = int(montant)
    partie_decimale = round((montant - partie_entiere) * 100)

    texte = nombre_to_malagasy_words(partie_entiere)

    if partie_decimale > 0:
        texte += f" sy {nombre_to_malagasy_words(partie_decimale)} iray"

    return f"{texte} Ariary"

# Inventaire — Environnement

## Système d'exploitation

| Élément | Valeur |
|---------|--------|
| OS | Ubuntu 26.04 (Linux 7.0.0-38-generic x86_64) |
| Utilisateur | ulrich |
| Date d'audit | 2026-11-19 |

## Interpréteurs et outils

| Outil | Version | Chemin |
|-------|---------|--------|
| Python | 3.12.16 | /home/ulrich/tous_les_projet/stage_l3_odoo/venv/bin/python3 |
| Odoo | 17.0.0 final | /home/ulrich/tous_les_projet/stage_l3_odoo/odoo/ |
| PostgreSQL (psql) | 18.6 | système (Ubuntu 18.6-0ubuntu0.26.04.1) |
| wkhtmltopdf | installé | /usr/local/bin/wkhtmltopdf |
| Node.js | v22.22.1 | système |
| npm | 9.2.0 | système |
| Git | 2.55.0 | système |

## Configuration Odoo

| Paramètre | Valeur |
|-----------|--------|
| Fichier de config | config/odoo17.conf |
| Port HTTP | 8071 |
| Port Gevent | 8072 |
| Interface | 127.0.0.1 |
| Base de données | etat_civil_odoo17_test |
| PostgreSQL host | 127.0.0.1:5432 |
| PostgreSQL user | odoo17 |
| addons_path | odoo/addons, custom_addons |
| data_dir | data/ |
| logfile | logs/odoo17.log |
| log_level | info |
| max_cron_threads | 0 |
| list_db | True |

> ⚠️ **Risque sécurité** : Les mots de passe (admin_passwd, db_password) sont stockés en clair dans config/odoo17.conf. Voir rapport qualité P0.

## Dépendances Python externes

| Package | Usage |
|---------|-------|
| odfpy | Export ODF (OpenDocument) |
| openpyxl | Export Excel (.xlsx) |
| qrcode | Génération QR code sur les actes |
| pytz | Gestion fuseaux horaires (audit log) |
| python-dateutil | Calculs relatifs d'âge |
| markupsafe | Échappement HTML (pièces justificatives) |

## Dépendances Odoo par module

| Module | Dépendances Odoo |
|--------|-----------------|
| etat_civil | base, mail, web |
| etat_civil_account | etat_civil, account |
| etat_civil_pos | etat_civil_account, point_of_sale |
| etat_civil_auth_email | base, web, etat_civil |

# Inventaire — Git, CI/CD et Procédure d'Installation

## Git

| Élément | Valeur |
|---------|--------|
| Dépôt distant | https://github.com/Ulrich506/real_projet_stage.git |
| Branche active | clean-main |
| Branches locales | chore/professionalisation-projet, clean-main, fix/etat-civil-account-billing, main, main-professional |
| Tags | Aucun |
| Nombre de commits | 18 |
| Dernier commit | 55b6008e feat(etat_civil): supprimer 'Suivi de la copie' + numéro de ticket incrémental |
| Premier commit | 07ab40a0 feat: Gestion d'État Civil — Odoo 17 |
| Fichier modifié (non commité) | custom_addons/etat_civil/migrations/2.1.30/post-migrate.py |

## CI/CD

| Élément | Statut |
|---------|--------|
| GitHub Actions | Non détecté (.github/workflows/ absent) |
| Pipeline CI | Non configuré |
| Tests automatisés CI | Non intégrés |

> ⚠️ Aucun workflow CI/CD détecté. Les tests ne s'exécutent pas automatiquement.

## Branches et différences

| Branche | Description |
|---------|-------------|
| clean-main | Branche active, version de travail principale |
| main | Branche originale |
| main-professional | Version professionnelle (à vérifier les différences) |
| chore/professionalisation-projet | Tâches de professionnalisation |
| fix/etat-civil-account-billing | Correction facturation |

## Procédure d'installation reconstituée

### Prérequis

1. Ubuntu 24.04+ (ou 26.04)
2. Python 3.12+
3. PostgreSQL 16+
4. wkhtmltopdf
5. Node.js + npm (pour le bundler LESS/JS d'Odoo)

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/Ulrich506/real_projet_stage.git
cd real_projet_stage

# 2. Créer l'environnement virtuel Python
python3 -m venv venv
source venv/bin/activate

# 3. Installer les dépendances Python
pip install -r odoo/requirements.txt
pip install odfpy openpyxl qrcode pytz python-dateutil markupsafe

# 4. Créer l'utilisateur et la base PostgreSQL
sudo -u postgres psql -c "CREATE USER odoo17 WITH PASSWORD '********' CREATEDB;"
createdb -E utf-8 -O odoo17 etat_civil_odoo17_test

# 5. Configurer Odoo
# Copier config/odoo17.conf.example → config/odoo17.conf
# Adapter les chemins et mots de passe

# 6. Initialiser la base avec les modules
./odoo/odoo-bin -c config/odoo17.conf -d etat_civil_odoo17_test \
  -i etat_civil,etat_civil_account,etat_civil_pos,etat_civil_auth_email \
  --stop-after-init

# 7. Lancer le serveur
./odoo/odoo-bin -c config/odoo17.conf
```

### Ce qui manque pour une installation reproductible

- ❌ Aucun fichier `requirements.txt` au niveau du projet (seul odoo/requirements.txt existe)
- ❌ Aucun script d'installation automatique
- ❌ Aucun Dockerfile / docker-compose.yml
- ❌ Les mots de passe sont codés en dur dans la config
- ❌ Aucune documentation sur la configuration PostgreSQL
- ❌ La dépendance `qrcode` n'est pas listée dans __manifest__.py external_dependencies
- ⚠️ `max_cron_threads = 0` désactive les tâches planifiées en production

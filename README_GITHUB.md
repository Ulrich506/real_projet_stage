# Gestion d'État Civil — Odoo 17

Logiciel de gestion des actes d'état civil (naissances, mariages, décès) basé sur **Odoo 17 Community**, développé dans le cadre d'un stage de Licence 3.

## Modules inclus

| Module | Description | Version |
|--------|-------------|---------|
| `etat_civil` | Gestion des citoyens, actes, registres et demandes de guichet | 17.0.2.1.12 |
| `etat_civil_account` | Passerelle comptable — facturation des demandes de copies | 17.0.1.1.2 |
| `etat_civil_pos` | Encaissement au point de vente (POS) | 17.0.1.0.1 |

## Prérequis

- **Python** 3.12
- **PostgreSQL** 16+ (testé avec 18.6)
- **Odoo 17 Community** — commit `1a68f7671bd0bf7594eb07d809763f147ee92c5a`

## Installation rapide

```bash
# 1. Cloner le projet
git clone https://github.com/Ulrich506/gestion-etat-civil-odoo17.git
cd gestion-etat-civil-odoo17

# 2. Cloner Odoo 17 Community
git clone --depth 1 -b 17.0 https://github.com/odoo/odoo.git odoo
cd odoo && git checkout 1a68f7671bd0bf7594eb07d809763f147ee92c5a && cd ..

# 3. Créer l'environnement virtuel
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements/base.txt -r requirements/custom-addons.txt

# 4. Configurer PostgreSQL
sudo -u postgres createuser --superuser odoo17
# Ou ajuster selon votre configuration

# 5. Configurer Odoo
cp config/odoo17.conf.example config/odoo17.conf
# Éditer config/odoo17.conf : changer les mots de passe et les chemins

# 6. Démarrer
./odoo17.sh start
```

Le serveur est accessible à `http://127.0.0.1:8071`.

## Documentation

- [Installation détaillée](documentation/INSTALL.md)
- [Configuration](documentation/CONFIGURATION.md)
- [Sauvegarde et restauration](documentation/BACKUP_RESTORE.md)

## Licence

LGPL-3

## Auteurs

Équipe État Civil — Stage L3

## Contribuer

Voir [CONTRIBUTING.md](CONTRIBUTING.md).

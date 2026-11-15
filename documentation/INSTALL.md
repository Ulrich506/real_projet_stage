# Guide d'installation

## Prérequis système

- **OS** : Ubuntu 24.04 LTS (ou dérivé)
- **Python** : 3.12
- **PostgreSQL** : 16+ (testé avec 18.6)
- **Espace disque** : minimum 5 Go libres

## 1. Cloner le projet

```bash
git clone https://github.com/Ulrich506/gestion-etat-civil-odoo17.git
cd gestion-etat-civil-odoo17
```

## 2. Installer Odoo 17 Community

```bash
git clone --depth 1 -b 17.0 https://github.com/odoo/odoo.git odoo
cd odoo
git checkout 1a68f7671bd0bf7594eb07d809763f147ee92c5a
cd ..
```

## 3. Configurer PostgreSQL

```bash
# Créer l'utilisateur odoo17
sudo -u postgres createuser --superuser odoo17

# Créer la base de données
sudo -u postgres createdb -O odoo17 etat_civil_odoo17_test
```

## 4. Créer l'environnement virtuel Python

```bash
python3.12 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements/base.txt
pip install -r requirements/custom-addons.txt
```

## 5. Configurer Odoo

```bash
cp config/odoo17.conf.example config/odoo17.conf
```

Éditez `config/odoo17.conf` :
- Changez `admin_passwd` et `db_password`
- Ajustez les chemins `addons_path`, `data_dir`, `logfile`

## 6. Démarrer le service

```bash
./odoo17.sh start
```

Le serveur est accessible à `http://127.0.0.1:8071`.

## 7. Installer les modules

1. Connectez-vous à Odoo
2. Activez le mode développeur
3. Allez dans Applications
4. Installez :
   - **Gestion d'État Civil** (`etat_civil`)
   - **État civil — Passerelle comptable** (`etat_civil_account`)
   - **État civil — Encaissement au point de vente** (`etat_civil_pos`)

## Commandes du script

```bash
./odoo17.sh start       # Démarrer
./odoo17.sh stop        # Arrêter
./odoo17.sh restart     # Redémarrer
./odoo17.sh status      # Vérifier l'état
./odoo17.sh logs        # Voir les logs en temps réel
./odoo17.sh update all  # Mettre à jour tous les modules
```

## Dépannage

- **Erreur de connexion PostgreSQL** : Vérifiez que le service PostgreSQL est actif et que les credentials dans `config/odoo17.conf` sont corrects.
- **Erreur de module manquant** : Vérifiez que `addons_path` dans la configuration inclut bien `odoo/addons` et `custom_addons`.
- **Erreur Python** : Vérifiez que le venv est activé et que les dépendances sont installées.

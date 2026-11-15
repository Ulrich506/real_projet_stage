# Guide de configuration

## Fichier de configuration

Le fichier `config/odoo17.conf` contrôle le comportement d'Odoo.

### Paramètres essentiels

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `admin_passwd` | Mot de passe maître pour la gestion des bases | `CHANGE_ME` |
| `db_host` | Adresse du serveur PostgreSQL | `127.0.0.1` |
| `db_port` | Port PostgreSQL | `5432` |
| `db_user` | Utilisateur PostgreSQL | `odoo17` |
| `db_password` | Mot de passe PostgreSQL | `CHANGE_ME` |
| `http_port` | Port HTTP du serveur Odoo | `8071` |
| `addons_path` | Chemins des modules (séparés par des virgules) | `/path/odoo/addons,/path/custom_addons` |
| `data_dir` | Répertoire de données (filestore, sessions) | `/path/data` |
| `logfile` | Chemin du fichier de log | `/path/logs/odoo17.log` |
| `db_name` | Base de données par défaut | `etat_civil_odoo17_test` |

### Sécurité

- **Ne commettez jamais** `config/odoo17.conf` dans Git — il est dans `.gitignore`.
- Utilisez `config/odoo17.conf.example` comme modèle.
- Changez toujours les mots de passe par défaut avant la première utilisation.
- Configurez `~/.pgpass` pour éviter de stocker les mots de passe dans les commandes.

### addons_path

L'ordre est important :
1. `odoo/addons` — modules standards Odoo
2. `custom_addons` — modules personnalisés du projet

Exemple :
```ini
addons_path = /home/user/projet/odoo/addons,/home/user/projet/custom_addons
```

### Logs

Niveaux de log disponibles :
- `info` — niveau par défaut, recommandé
- `debug` — pour le débogage
- `warning` — avertissements uniquement
- `error` — erreurs uniquement

## Script odoo17.sh

Le script gère le cycle de vie du service :

```bash
./odoo17.sh start       # Démarrer en arrière-plan
./odoo17.sh stop        # Arrêter proprement
./odoo17.sh restart     # Redémarrer
./odoo17.sh status      # Vérifier l'état
./odoo17.sh logs        # Suivre les logs en temps réel
./odoo17.sh update all  # Mettre à jour tous les modules
./odoo17.sh update etat_civil  # Mettre à jour un module spécifique
```

### Mise à jour de modules

Le script refuse de mettre à jour la base de production (`etat_civil_odoo17_test`). Pour mettre à jour un module :

1. Créez une copie de la base
2. Modifiez `db_name` dans la configuration
3. Exécutez `./odoo17.sh update nom_du_module`

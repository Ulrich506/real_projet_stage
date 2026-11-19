# Déploiement par Commune — État Civil Odoo 17

## Principe fondamental

**Une base PostgreSQL = Une commune = Une installation Odoo**

Chaque commune dispose de sa propre base de données PostgreSQL isolée. Aucune commune ne peut consulter, modifier ou découvrir les données d'une autre commune.

## Prérequis

- Serveur Linux (Ubuntu 22.04+ recommandé)
- PostgreSQL 14+
- Python 3.10+
- Odoo 17
- Accès administrateur au serveur

## 1. Création de la base PostgreSQL

```bash
# Se connecter à PostgreSQL
sudo -u postgres psql

# Créer la base de données
CREATE DATABASE etat_civil_<CODE_COMMUNE>
    ENCODING 'UTF8'
    LC_COLLATE='fr_FR.UTF-8'
    LC_CTYPE='fr_FR.UTF-8'
    TEMPLATE template0;

# Créer un utilisateur dédié (optionnel, pour plus de sécurité)
CREATE USER etat_civil_<CODE_COMMUNE> WITH PASSWORD '<mot_de_passe_fort>';
GRANT ALL PRIVILEGES ON DATABASE etat_civil_<CODE_COMMUNE> TO etat_civil_<CODE_COMMUNE>;
```

Remplacer `<CODE_COMMUNE>` par le code court de la commune (ex: `ants`, `fia`, `amb`).

## 2. Configuration Odoo

Créer un fichier de configuration dédié par commune :

```ini
# config/odoo_<CODE_COMMUNE>.conf
[options]
db_name = etat_civil_<CODE_COMMUNE>
db_host = localhost
db_port = 5432
db_user = odoo
db_password = odoo

# CRITIQUE : filtrer pour ne voir que cette base
dbfilter = ^etat_civil_<CODE_COMMUNE>$

# CRITIQUE : ne pas exposer la liste des bases
list_db = False

# Mot de passe maître fort et unique par installation
admin_passwd = <generer_mot_de_passe_fort_32_caracteres>

# Filestore isolé par installation
data_dir = /opt/odoo/data/<CODE_COMMUNE>

# Logs isolés
logfile = /opt/odoo/logs/<CODE_COMMUNE>.log

# Sécurité
limit_time_real = 1200
limit_time_cpu = 600
workers = 4
max_cron_threads = 1
```

### Génération d'un mot de passe maître fort

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 3. Structure des répertoires

```
/opt/odoo/
├── config/
│   ├── odoo_ants.conf      # Commune d'Antsohihy
│   ├── odoo_fia.conf       # Commune de Fianarantsoa
│   └── odoo_amb.conf       # Commune d'Ambanja
├── data/
│   ├── ants/               # Filestore d'Antsohihy
│   │   ├── filestore/
│   │   └── sessions/
│   ├── fia/                # Filestore de Fianarantsoa
│   └── amb/                # Filestore d'Ambanja
├── logs/
│   ├── ants.log
│   ├── fia.log
│   └── amb.log
└── custom_addons/          # Modules partagés (même version)
    ├── etat_civil/
    ├── etat_civil_account/
    └── etat_civil_pos/
```

## 4. Lancement du serveur

```bash
# Lancer Odoo pour une commune spécifique
python3 /opt/odoo/odoo/odoo-bin \
    -c /opt/odoo/config/odoo_<CODE_COMMUNE>.conf \
    --addons-path=/opt/odoo/custom_addons,/opt/odoo/odoo/addons
```

### Service systemd (recommandé)

```ini
# /etc/systemd/system/odoo-<CODE_COMMUNE>.service
[Unit]
Description=Odoo 17 - État Civil <NOM_COMMUNE>
After=network.target postgresql.service

[Service]
Type=simple
User=odoo
Group=odoo
ExecStart=/usr/bin/python3 /opt/odoo/odoo/odoo-bin \
    -c /opt/odoo/config/odoo_<CODE_COMMUNE>.conf \
    --addons-path=/opt/odoo/custom_addons,/opt/odoo/odoo/addons
Restart=always
RestartSec=5
StandardOutput=append:/opt/odoo/logs/<CODE_COMMUNE>.log
StandardError=append:/opt/odoo/logs/<CODE_COMMUNE>.log

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable odoo-<CODE_COMMUNE>
sudo systemctl start odoo-<CODE_COMMUNE>
```

## 5. Installation des modules

```bash
# Créer et installer les modules
python3 /opt/odoo/odoo/odoo-bin \
    -c /opt/odoo/config/odoo_<CODE_COMMUNE>.conf \
    --addons-path=/opt/odoo/custom_addons,/opt/odoo/odoo/addons \
    -i etat_civil,etat_civil_account,etat_civil_pos \
    --stop-after-init
```

## 6. Configuration initiale

Après l'installation, l'administrateur local accède au menu **Administration > Identité de la commune** pour configurer :

1. Nom officiel de la commune
2. Type (urbaine/rurale)
3. Code de la commune
4. Région et district
5. Adresse et contact
6. Logo officiel
7. Mentions légales

L'identité est automatiquement verrouillée après le premier acte enregistré.

## 7. Sauvegarde

### Sauvegarde PostgreSQL

```bash
# Sauvegarde complète de la base
pg_dump -U postgres -Fc -f /backup/etat_civil_<CODE_COMMUNE>_%Y%m%d.dump \
    etat_civil_<CODE_COMMUNE>

# Chiffrement de la sauvegarde
gpg --symmetric --cipher-algo AES256 \
    /backup/etat_civil_<CODE_COMMUNE>_%Y%m%d.dump
```

### Sauvegarde du filestore

```bash
tar -czf /backup/filestore_<CODE_COMMUNE>_%Y%m%d.tar.gz \
    /opt/odoo/data/<CODE_COMMUNE>/filestore
```

### Cron de sauvegarde automatique

```bash
# /etc/cron.d/odoo-backup-<CODE_COMMUNE>
0 2 * * * odoo pg_dump -U postgres -Fc -f /backup/etat_civil_<CODE_COMMUNE>_%Y%m%d.dump etat_civil_<CODE_COMMUNE> && gpg --symmetric --cipher-algo AES256 /backup/etat_civil_<CODE_COMMUNE>_%Y%m%d.dump
0 3 * * * odoo tar -czf /backup/filestore_<CODE_COMMUNE>_%Y%m%d.tar.gz /opt/odoo/data/<CODE_COMMUNE>/filestore
```

### Rétention des sauvegardes

```bash
# Garder uniquement les 30 derniers jours
find /backup -name "etat_civil_<CODE_COMMUNE>_*.dump*" -mtime +30 -delete
find /backup -name "filestore_<CODE_COMMUNE>_*.tar.gz" -mtime +30 -delete
```

## 8. Restauration

```bash
# Déchiffrer la sauvegarde
gpg --decrypt /backup/etat_civil_<CODE_COMMUNE>_%Y%m%d.dump.gpg \
    | pg_restore -U postgres -d etat_civil_<CODE_COMMUNE> --clean --if-exists

# Restaurer le filestore
tar -xzf /backup/filestore_<CODE_COMMUNE>_%Y%m%d.tar.gz \
    -C /opt/odoo/data/<CODE_COMMUNE>/
```

## 9. Mise à jour des modules

```bash
# Mettre à jour les modules custom
python3 /opt/odoo/odoo/odoo-bin \
    -c /opt/odoo/config/odoo_<CODE_COMMUNE>.conf \
    --addons-path=/opt/odoo/custom_addons,/opt/odoo/odoo/addons \
    -u etat_civil,etat_civil_account,etat_civil_pos \
    --stop-after-init
```

## 10. Sécurité

### Règles de pare-feu

```bash
# Autoriser uniquement le port Odoo (8069) et PostgreSQL local
sudo ufw allow 8069/tcp
sudo ufw deny 5432/tcp  # PostgreSQL ne doit pas être accessible depuis l'extérieur
sudo ufw enable
```

### Certificat SSL

```bash
# Utiliser Let's Encrypt avec Nginx comme reverse proxy
sudo certbot --nginx -d etat-civil.<commune>.mg
```

### Nginx reverse proxy

```nginx
server {
    listen 80;
    server_name etat-civil.<commune>.mg;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name etat-civil.<commune>.mg;

    ssl_certificate /etc/letsencrypt/live/etat-civil.<commune>.mg/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/etat-civil.<commune>.mg/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8069;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # WebSocket pour Chat
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 11. Monitoring

### Vérification de l'état du service

```bash
sudo systemctl status odoo-<CODE_COMMUNE>
```

### Logs

```bash
# Voir les logs en temps réel
sudo tail -f /opt/odoo/logs/<CODE_COMMUNE>.log
```

## 12. Checklist de déploiement

- [ ] Base PostgreSQL créée avec le bon nom
- [ ] Fichier de configuration avec `dbfilter` et `list_db = False`
- [ ] Mot de passe maître fort et unique
- [ ] Filestore isolé dans `data/<CODE_COMMUNE>/`
- [ ] Logs isolés dans `logs/<CODE_COMMUNE>.log`
- [ ] Service systemd configuré
- [ ] Modules installés
- [ ] Identité de la commune configurée
- [ ] Sauvegarde automatique configurée
- [ ] Certificat SSL installé
- [ ] Pare-feu configuré
- [ ] Accès administrateur local vérifié

## 13. Dépannage

### Le module ne se charge pas

```bash
# Vérifier les logs
sudo tail -50 /opt/odoo/logs/<CODE_COMMUNE>.log

# Vérifier les permissions
sudo chown -R odoo:odoo /opt/odoo/data/<CODE_COMMUNE>
sudo chown -R odoo:odoo /opt/odoo/custom_addons
```

### La base n'est pas accessible

```bash
# Vérifier que dbfilter est correct
grep dbfilter /opt/odoo/config/odoo_<CODE_COMMUNE>.conf

# Vérifier que la base existe
sudo -u postgres psql -l | grep etat_civil_<CODE_COMMUNE>
```

### L'identité ne se verrouille pas

```bash
# Vérifier qu'il y a au moins un acte
sudo -u postgres psql -d etat_civil_<CODE_COMMUNE> -c \
    "SELECT count(*) FROM etat_civil_acte_naissance;"
```

## Annexes

### Codes de communes recommandés

| Commune | Code | Base PostgreSQL |
|---------|------|-----------------|
| Antsohihy | ANTS | etat_civil_ants |
| Fianarantsoa | FIA | etat_civil_fia |
| Ambanja | AMB | etat_civil_amb |
| Toamasina | TMM | etat_civil_tmm |
| Antsirabe | ANI | etat_civil_ani |

### Variables d'environnement sensibles

Ne jamais committer les fichiers de configuration contenant les mots de passe. Utiliser `.gitignore` :

```gitignore
# .gitignore
config/odoo_*.conf
*.dump
*.gpg
```

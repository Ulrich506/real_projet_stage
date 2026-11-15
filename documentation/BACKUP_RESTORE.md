# Sauvegarde et restauration

## Sauvegarde

### Base de données

```bash
# Sauvegarde complète au format custom
pg_dump -Fc -U odoo17 -h 127.0.0.1 -d etat_civil_odoo17_test -f backup.dump
```

### Filestore

```bash
# Sauvegarde du filestore (fichiers joints, pièces jointes)
tar -czf filestore.tar.gz -C data/filestore etat_civil_odoo17_test/
```

### Code et configuration

```bash
# Sauvegarde des modules custom
tar -czf code.tar.gz -C /path/to/project custom_addons/ odoo17.sh config/ requirements/
```

### Vérification

```bash
# Vérifier la structure du dump
pg_restore --list backup.dump

# Vérifier les sommes SHA-256
sha256sum -c sha256sums.txt
```

## Restauration

### Base de données

```bash
# Créer une nouvelle base
createdb -U odoo17 -h 127.0.0.1 etat_civil_restored

# Restaurer le dump
pg_restore -U odoo17 -h 127.0.0.1 -d etat_civil_restored --no-owner --no-privileges backup.dump
```

### Filestore

```bash
# Arrêter Odoo avant de restaurer le filestore
./odoo17.sh stop

# Restaurer le filestore
tar -xzf filestore.tar.gz -C data/filestore/

# Redémarrer Odoo
./odoo17.sh start
```

## Sauvegarde automatique

Il est recommandé de planifier des sauvegardes régulières avec `cron` :

```bash
# Éditer le crontab
crontab -e

# Exemple : sauvegarde quotidienne à 2h du matin
0 2 * * * pg_dump -Fc -U odoo17 -h 127.0.0.1 -d etat_civil_odoo17_test -f /home/ulrich/backups/odoo17/$(date +\%Y\%m\%d).dump
```

## Stockage des sauvegardes

- Les sauvegardes contiennent des **données personnelles** — ne les partagez pas.
- Stockez les sauvegardes sur un support externe ou un serveur distant sécurisé.
- Vérifiez régulièrement que les sauvegardes sont restaurables.

## Procédure de restauration d'urgence

1. Arrêter le service Odoo : `./odoo17.sh stop`
2. Restaurer la base de données depuis le dernier backup
3. Restaurer le filestore
4. Vérifier la configuration (`config/odoo17.conf`)
5. Redémarrer le service : `./odoo17.sh start`
6. Vérifier les logs : `tail -f logs/odoo17.log`
7. Tester l'accès : `curl http://127.0.0.1:8071/web/login`

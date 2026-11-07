# Préparation technique — préproduction État Civil

**État : préparation seulement.** Aucun backup, création, restauration ou migration n’a été effectué. Il faut une autorisation explicite distincte avant ces opérations et une source précise désignée par le responsable.

## Cible et chemins

- Base préproduction proposée : `etat_civil_preproduction_20261105` — vérifiée absente le 5 novembre 2026.
- Base source : **à désigner**. Ne pas prendre par défaut une base active ou la base de revue.
- `data_dir` du projet : `/home/ulrich/tous_les_projet/stage_l3_odoo/data`.
- Filestore source courant vérifié : `/home/ulrich/tous_les_projet/stage_l3_odoo/data/filestore/etat_civil_final_review_20261105_1304` (ce chemin ne désigne pas la source de préproduction).
- Filestore cible proposé : `/home/ulrich/tous_les_projet/stage_l3_odoo/data/filestore/etat_civil_preproduction_20261105`.
- Racine de backup proposée, disponibilité et capacité non vérifiées : `/var/backups/odoo/etat_civil_preproduction_20261105/<UTC_TIMESTAMP>/`.
- Fichiers proposés dans cette racine : `<SOURCE_DB>.dump`, `<SOURCE_DB>-filestore.tar`, `SHA256SUMS`, `pg_restore-list.txt`, `backup-manifest.txt`.

Les chemins de backup sont une proposition; leur existence, permissions, espace libre, chiffrement et politique de rétention restent à confirmer avant usage.

## Prérequis

1. Autorisation explicite portant sur la base source, la cible, l’emplacement des backups et la fenêtre d’intervention.
2. Vérifier que la source est une base de test/validation autorisée, jamais la base active sans permission distincte.
3. Capturer l’inventaire des modules installés, versions, dépendances, propriétaires/extensions PostgreSQL et taille de la base.
4. Vérifier migrations de schéma et données présentes dans `custom_addons/etat_civil/migrations/` entre la version de la source et celle du module livré.
5. Vérifier la cible absente avant toute création. Refuser si elle existe déjà.
6. Coordonner une pause des écritures sur la source, ou une méthode de snapshot cohérente, afin que dump et filestore correspondent au même état.
7. Confirmer que le stockage de backup est protégé et exclu des dépôts Git.

## Sauvegarde PostgreSQL proposée — non exécutée

Après autorisation et choix de `SOURCE_DB` :

```sh
set -euo pipefail
SOURCE_DB='<base_source_autorisee>'
TARGET_DB='etat_civil_preproduction_20261105'
STAMP='<UTC_TIMESTAMP>'
BACKUP_DIR="/var/backups/odoo/etat_civil_preproduction_20261105/$STAMP"
install -d -m 0700 "$BACKUP_DIR"
test "$SOURCE_DB" != "$TARGET_DB"
pg_dump --format=custom --no-owner --no-privileges \
  --dbname="$SOURCE_DB" --file="$BACKUP_DIR/$SOURCE_DB.dump"
pg_restore --list "$BACKUP_DIR/$SOURCE_DB.dump" \
  > "$BACKUP_DIR/pg_restore-list.txt"
```

Les secrets d’accès PostgreSQL doivent provenir du mécanisme approuvé de l’environnement, sans argument visible, rapport ou journal contenant un mot de passe.

## Sauvegarde filestore correspondante — non exécutée

```sh
SOURCE_FS='/home/ulrich/tous_les_projet/stage_l3_odoo/data/filestore/'"$SOURCE_DB"
test -d "$SOURCE_FS"
tar --numeric-owner --xattrs --acls -cpf \
  "$BACKUP_DIR/$SOURCE_DB-filestore.tar" -C "$SOURCE_FS" .
tar -tf "$BACKUP_DIR/$SOURCE_DB-filestore.tar" >/dev/null
sha256sum "$BACKUP_DIR/$SOURCE_DB.dump" \
  "$BACKUP_DIR/$SOURCE_DB-filestore.tar" > "$BACKUP_DIR/SHA256SUMS"
(cd "$BACKUP_DIR" && sha256sum --check SHA256SUMS)
```

Le filestore doit toujours être celui de `SOURCE_DB`; ne jamais substituer celui d’une autre base. Enregistrer dans `backup-manifest.txt` les identifiants source/cible, timestamps UTC, chemins absolus, versions, nombres de fichiers et empreintes, sans données personnelles ni secrets.

## Restauration isolée proposée — non exécutée

Avant restauration : cible absente, serveur de préproduction isolé, cron désactivés, port HTTP/gevent dédiés, `dbfilter` limité à la cible, `PYTHONPATH` contrôlé, service actif non utilisé.

```sh
createdb --template=template0 --encoding=UTF8 "$TARGET_DB"
pg_restore --exit-on-error --no-owner --dbname="$TARGET_DB" \
  "$BACKUP_DIR/$SOURCE_DB.dump"
```

La restauration du filestore doit viser uniquement le répertoire cible absent. Si celui-ci existe, arrêter et demander une décision; ne pas fusionner ou écraser des fichiers.

```sh
TARGET_FS='/home/ulrich/tous_les_projet/stage_l3_odoo/data/filestore/'"$TARGET_DB"
test ! -e "$TARGET_FS"
install -d -m 0750 "$TARGET_FS"
tar --same-owner --same-permissions --xattrs --acls -xpf \
  "$BACKUP_DIR/$SOURCE_DB-filestore.tar" -C "$TARGET_FS"
```

## Contrôles avant migration

- Comparer inventaire et versions des modules installés à la source.
- Vérifier les versions du module `etat_civil` et chemins de migration applicables.
- Préparer captures avant migration : nombres par type d’acte, centres, registres, pièces jointes et mentions; contrôles de séquences; contraintes et clés étrangères; index; pièces `ir_attachment` et résolution de chaque `store_fname` dans le filestore.
- Valider la sauvegarde par `sha256sum --check`, `pg_restore --list` et inventaire du tar; réaliser une restauration d’essai isolée avant d’accepter la sauvegarde.
- Ne lancer `-u etat_civil` qu’après approbation explicite de la migration sur cette cible isolée, avec sauvegarde vérifiée et log dédié. Aucune mise à jour de base active.
- Après migration, contrôler séquences, relations, contraintes, échantillons métier, pièces jointes, accès par rôle/centre et rapports PDF avant ouverture de la préproduction.

## Critères d’acceptation

- Backup PostgreSQL et archive du filestore correspondent à la même base et au même instant; empreintes vérifiées.
- Restauration d’essai terminée sans erreur dans un environnement isolé.
- Modules/migrations attendus identifiés, contraintes et séquences cohérentes.
- Aucune pièce jointe référencée manquante; aucune pièce du filestore d’une autre base.
- Tests de rôles, centres, URL/API/RPC, actes, pièces, PDF et navigation réussis; anomalies restantes acceptées par le responsable.
- Pas de référence à des identifiants, secrets, signatures fictives, logos ou cachets inventés.

## Retour arrière proposé

1. Bloquer l’accès à la préproduction et arrêter uniquement ses processus isolés.
2. Conserver l’état échoué sous un nom daté par renommage PostgreSQL; ne supprimer aucune base.
3. Préserver son filestore sous un nom de rétention daté par renommage; ne supprimer aucun fichier.
4. Restaurer le dump vérifié et le filestore de la même source vers les chemins cibles libérés, sans fusion.
5. Refaire les contrôles de cohérence et documenter l’incident, les chemins et empreintes.

Aucune étape de ce document n’a été exécutée. Toute création, restauration, migration ou renommage attend une autorisation explicite.

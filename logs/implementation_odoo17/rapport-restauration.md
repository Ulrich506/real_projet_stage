# Rapport de sauvegarde et restauration d’essai

## Archive source

- Archive : `backups/etat_civil_dev_regression_20261105_pre_finance_retest.zip`.
- Contenu inspecté : `dump.sql`, `manifest.json` et objets sous `filestore/`.
- `unzip -tq` : aucune erreur; la SHA-256 enregistrée dans `SHA256SUMS.txt` est vérifiée.
- La sauvegarde est issue d’une base synthétique. Elle n’est ni une sauvegarde de production, ni une copie de la base de revue.

## Restauration isolée

- Destination neuve : `etat_civil_restore_validation_20261105_01` (confirmée absente avant restauration).
- Filestore exact : `/home/ulrich/tous_les_projet/stage_l3_odoo/data/implementation_odoo17_dev/filestore/etat_civil_restore_validation_20261105_01`.
- Processus Odoo démarré sur `127.0.0.1:18183` et gevent `18184`, configuration privée `/tmp/etat_civil_restore_validation_20261105_01.conf`, journal `odoo-restore-check-final.log (snapshot)`.
- Le registre Odoo 17 a chargé 45 modules sans mise à jour; `/api/v1/health` répond 200 avec la base de destination.
- Audit ORM en lecture seule : 43 pièces jointes avec `store_fname`; **0 objet de filestore manquant**.
- Le test a donc vérifié archive, restauration de base, filestore correspondant et démarrage. Aucun document métier payant n’était présent pour vérifier une pièce d’acte générée.

## Après restauration

Quatre utilisateurs synthétiques ont été créés uniquement dans cette destination pour une connexion HTTP par rôle. Aucune donnée personnelle réelle, aucun mot de passe réel et aucun service protégé n’ont été touchés. Cette base restaurée est maintenant une base de validation synthétique enrichie; l’archive source reste inchangée.

## Limites

Aucune restauration de production ou de revue n’a eu lieu. Le backup à restaurer en exploitation doit être créé à partir de la base autorisée et du filestore de même nom au même instant logique; ce rapport ne constitue pas une procédure de reprise de production.

Un premier appel de sauvegarde a échoué avant accès DB (gestionnaire de DB désactivé) et a laissé un fichier vide, renommé `backups/etat_civil_final_audit_tests_20261105_pre_update.empty-invalid`; il n’est pas une sauvegarde et ne doit pas être utilisé. L’archive `_pre_update_verified.zip` créée ensuite est celle qui a été vérifiée.

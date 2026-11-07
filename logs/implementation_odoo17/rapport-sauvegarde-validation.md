# Rapport — sauvegarde et restauration de validation

**Relevé :** 2026-11-06 09:20 EAT (+03:00).  
**Odoo / Python / PostgreSQL :** 17.0 / 3.14.4 / 18.6.  
**Instance source :** HTTP/gevent 18391/18392, loopback; aucun serveur HTTP n'a été démarré pour la restauration.  
**Modules concernés :** `etat_civil`, `etat_civil_auth_email`, `etat_civil_account`, `account`, `base`, `web`, `mail`.  
**Statut :** TERMINÉ ET TESTÉ pour la sauvegarde, l'intégrité de l'archive et la restauration dans une base neuve.

## Sauvegarde source

- Base synthétique : `etat_civil_validation_20261106_0100`.
- Dump : `logs/implementation_odoo17/backups/etat_civil_validation_20261106_0100.dump` — format PostgreSQL custom, 3 705 938 octets.
- Archive filestore : `logs/implementation_odoo17/backups/etat_civil_validation_20261106_0100-filestore.tar.gz` — 2 304 899 octets, 786 fichiers et 7 906 601 octets décompressés.
- Manifeste : `logs/implementation_odoo17/backups/etat_civil_validation_20261106_0100.sha256`.
- Les trois fichiers sont en mode 600. `pg_restore --list` a lu 7 452 entrées. Les empreintes SHA-256 du dump et de l'archive ont été recalculées et correspondent au manifeste.

| Fichier | SHA-256 |
|---|---|
| `etat_civil_validation_20261106_0100.dump` | `0b1dc3e68b13104910bf4af0a39a4f3560c268478687bf778bd80c718e7c233d` |
| `etat_civil_validation_20261106_0100-filestore.tar.gz` | `3cac0a10c19f82f55d9ec8a01914034a9db21061c3858155f4f9af70459207f3` |

## Restauration isolée

- Nom de destination contrôlé absent avant création : `etat_civil_validation_restore_20261106_0100`.
- Configuration privée distincte, mode 600 : `logs/implementation_odoo17/etat_civil_validation_restore_20261106_0100.conf`.
- Data dir neuf : `data/validation_restore_20261106_0100`.
- Filestore : `data/validation_restore_20261106_0100/filestore/etat_civil_validation_restore_20261106_0100`.
- La base a été créée avec `createdb --template=template0 --owner=odoo17`, puis restaurée avec `pg_restore --exit-on-error --no-owner --no-acl`. Aucun `--clean`, aucune suppression et aucune restauration sur une base préexistante.
- Le registre Odoo a été chargé sans HTTP. Il voit 3 demandes, 0 facture et 0 paiement; les sept modules attendus sont installés.

Les deux arbres de filestore ont exactement 786 fichiers, sans fichier manquant ni supplémentaire; les SHA-256 individuels des 786 paires source/restauration correspondent. La base contient 474 lignes `ir_attachment`; 473 ont une référence `store_fname` non vide (389 chemins distincts). Toutes les références vérifiées existent dans le filestore restauré. Aucune pièce jointe référencée n'est manquante.

## Commandes / limites

Contrôles et actions : `pg_dump --format=custom --no-owner --no-acl`; création d'une archive tar du seul filestore source; `pg_restore --list`; validation SHA-256; `createdb` sur le nouveau nom; `pg_restore --exit-on-error`; vérification de chaque fichier et de chaque référence de filestore; chargement du registre par `Registry(...)` Odoo et requêtes ORM en lecture seule. Les identifiants PostgreSQL ont été lus en mémoire depuis la configuration privée; aucun secret n'est passé en argument de commande ou écrit dans le rapport.

La restauration n'a pas été exposée en HTTP et n'a pas fait l'objet d'un test navigateur; le chargement du registre et l'intégrité base/filestore sont vérifiés. Aucun contenu PDF métier n'existe dans les fixtures à contrôler. Les archives portent uniquement sur la base et les données synthétiques de ce banc.

**Fichiers créés :** dump, archive et manifeste ci-dessus; configuration et journal dédiés à la restauration; filestore de destination. Aucune source préexistante n'a été écrasée. La base et le service source restent actifs.

**Preuves et erreurs :** contrôles PostgreSQL des noms de base, taille, propriétaire/privilège; `pg_restore --list`; empreintes des archives; comparaison SHA-256 de chaque fichier; vérification des chemins `store_fname`; chargement du registre Odoo. Toutes les assertions ont réussi; aucune erreur de restauration n'a été observée. La commande initiale `psql -w` sans secret fourni avait échoué au contrôle d'accès; la sauvegarde/restauration a utilisé les paramètres de la configuration autorisée sans les afficher.

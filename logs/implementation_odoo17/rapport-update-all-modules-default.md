# Rapport — mise à jour par défaut de tous les modules

Date: 2026-11-06

## Objectif

Finaliser `odoo17 update` pour que, sans base ni mot-clé `all`, la commande utilise une base unique explicitement définie par `db_name` dans `config/odoo17.conf` et transmette `-u all` à Odoo. Les mises à jour ciblées restent supportées.

## Configuration examinée

`config/odoo17.conf` contient actuellement:

- `list_db = True`
- aucun `db_name`
- aucun `dbfilter`

La configuration ne permet donc pas de choisir automatiquement une base. Par sécurité, `odoo17 update` refuse l'opération avec le code 2 et demande l'ajout explicite de `db_name = NOM_BASE`.

## Sauvegarde et modifications préexistantes

Les sauvegardes existantes avant les travaux sont:

- `logs/implementation_odoo17/odoo17.sh.before-update-all.20261106091646`
- `logs/implementation_odoo17/odoo17.sh.before-default-update.20261106092329`

Le dépôt contenait déjà de nombreuses modifications préexistantes. Elles ont été préservées. Seul `odoo17.sh` a été modifié pour cette mission; la configuration Odoo, les bases et les filestores n'ont pas été modifiés.

## Comportement final

- `odoo17 update` utilise `module=all` par défaut.
- `odoo17 update etat_civil` conserve une mise à jour ciblée.
- Les listes comme `etat_civil,etat_civil_account` restent acceptées.
- Le nom du module est limité aux lettres, chiffres et underscores, avec des éléments séparés par des virgules.
- La base est lue uniquement depuis `db_name` dans `config/odoo17.conf`.
- `db_name` doit apparaître exactement une fois et contenir un seul nom valide.
- `dbfilter` n'est pas utilisé comme sélection arbitraire de base.
- Le processus conserve `--stop-after-init --no-http` et son journal en `logs/update_NOMBASE_MODULE.log`.
- Un serveur Odoo actif est détecté et provoque un refus; le script ne l'arrête jamais.

## Tests réalisés

Toutes les mises à jour ont été simulées avec un exécuteur Odoo factice. Aucun Odoo réel ni aucune base réelle n'a été lancé ou modifié.

| Cas | Résultat observé | Code |
|---|---|---:|
| Syntaxe `bash -n` | Réussie | 0 |
| `git diff --check -- odoo17.sh` | Réussie | 0 |
| Configuration réelle sans `db_name`, `update` | Refus explicite | 2 |
| Configuration simulée unique, `update` | `-d demo_isolee -u all` transmis | 0 |
| Configuration simulée unique, `update etat_civil` | `-d demo_isolee -u etat_civil` transmis | 0 |
| `db_name` absent en simulation | Refus explicite | 2 |
| Deux occurrences `db_name` | Refus explicite | 2 |
| Instance Odoo active simulée | Refus, aucun arrêt effectué | 1 |
| Erreur Odoo simulée avec code 7 | Code 7 remonté | 7 |
| Module invalide `etat civil` | Refus de validation | 2 |

## Résultat de `git diff --check`

Le contrôle global du dépôt signale des espaces en fin de ligne préexistants dans `logs/odoo17.log`. Aucun fichier journal n'a été modifié ou nettoyé pour masquer ce résultat. Le contrôle limité aux modifications de `odoo17.sh` passe.

## Contrôles conservés

Les commandes `start`, `stop`, `restart`, `status` et `logs` n'ont pas été remplacées. Les protections contre l'arrêt automatique, la sélection arbitraire d'une base et la mise à jour avec un serveur actif restent actives.

## Limites

- La mise à jour globale ne démarrera pas sur la configuration réelle tant qu'un administrateur n'ajoute pas explicitement un seul `db_name` valide à `config/odoo17.conf`.
- Les simulations vérifient les arguments et les codes de retour, mais ne remplacent pas une mise à jour contrôlée sur une base isolée.
- Aucun test réel, aucun arrêt/ démarrage de service, aucune modification de base et aucun changement de configuration n'ont été effectués.

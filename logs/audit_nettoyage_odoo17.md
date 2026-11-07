# Audit de nettoyage Odoo 17

Date : 2026-11-06

## 1. État initial

- PostgreSQL actif : PostgreSQL 18.6, cluster `18/main`.
- Aucune instance `odoo-bin` n'était active au moment de l'audit.
- PostgreSQL est accessible en lecture avec l'utilisateur `odoo17` sur `127.0.0.1:5432`.
- L’environnement contient 43 bases PostgreSQL visibles, regroupant des bases Odoo 17, des bases d’autres projets et les bases système PostgreSQL.
- 36 bases appartiennent à `odoo17`, 3 à `odoo` et 4 à `postgres` (`postgres`, `rich_vent`, `rich_vente`, `transport_coop`).
- Initialement, `config/odoo17.conf` ne contenait ni `db_name` ni `dbfilter`; seul `list_db=True` était configuré. Après confirmation de la base principale, `db_name = etat_civil_odoo17_test` a été ajouté.
- Le dépôt Git contient de nombreuses modifications locales préexistantes: 460 chemins modifiés/ajoutés/supprimés. Aucune modification Git n'a été effectuée par cet audit.

## 2. Liste complète des bases

Toutes les bases ci-dessous ont été observées. Les tailles sont celles de PostgreSQL au moment de l'audit.

| Base | Propriétaire | Taille | Classification de travail |
|---|---:|---:|---|
| ec_workflow_test_20261101 | odoo17 | 19 MB | À examiner — ancienne série workflow, base minimale |
| ec_workflow_test_20261101c | odoo17 | 25 MB | À examiner — série workflow, module civil absent |
| ec_workflow_test_20261101d | odoo17 | 30 MB | À examiner — copie workflow Odoo 17 |
| ec_workflow_test_20261101e | odoo17 | 30 MB | À examiner — copie workflow Odoo 17 |
| ec_workflow_test_20261101f | odoo17 | 30 MB | À examiner — copie workflow Odoo 17 |
| ec_workflow_test_20261101g | odoo17 | 29 MB | À examiner — copie workflow Odoo 17 |
| ec_workflow_test_20261101h | odoo17 | 29 MB | À examiner — copie workflow Odoo 17 |
| ec_workflow_test_20261101i | odoo17 | 30 MB | À examiner — copie workflow Odoo 17 |
| etat_civil_admin_roles_validation_20261104 | odoo17 | 31 MB | Validation — rôle administrateur |
| etat_civil_audit_targeted_20261102 | odoo17 | 30 MB | Validation/Audit |
| etat_civil_audit_targeted_b_20261102 | odoo17 | 30 MB | Validation/Audit — copie potentielle |
| etat_civil_dev_email_account_20261105 | odoo17 | 28 MB | Développement |
| etat_civil_dev_email_account_auth_20261105 | odoo17 | 41 MB | Développement — authentification/compte |
| etat_civil_dev_finalcheck_20261105 | odoo17 | 41 MB | Développement — contrôle final |
| etat_civil_dev_latest_20261105 | odoo17 | 41 MB | Développement — instantané récent |
| etat_civil_dev_regression_20261105 | odoo17 | 44 MB | Développement/régression |
| etat_civil_dev_verify_final_20261105 | odoo17 | 41 MB | Développement/vérification |
| etat_civil_final_audit_20261102 | odoo17 | 30 MB | Validation/Audit |
| etat_civil_final_audit_retry_20261102 | odoo17 | 30 MB | Validation/Audit — tentative ultérieure |
| etat_civil_final_audit_tests_20261105 | odoo17 | 42 MB | Validation/Audit récente |
| etat_civil_final_review_20261105_1304 | odoo17 | 41 MB | Validation — revue finale |
| etat_civil_isolated_review2_20261104_2240 | odoo17 | 30 MB | Validation isolée |
| etat_civil_isolated_review3_20261104_2300 | odoo17 | 33 MB | Validation isolée — la plus récente de la série |
| etat_civil_isolated_review_20261104_2225 | odoo17 | 30 MB | Validation isolée |
| etat_civil_odoo17_test | odoo17 | 63 MB | À examiner — principale historique probable |
| etat_civil_phase_next_auth_20261105_01 | odoo17 | 27 MB | Développement — authentification |
| etat_civil_phase_next_auth_incompatible_20261105_02 | odoo17 | 27 MB | À examiner — résultat incompatibilité |
| etat_civil_phase_next_finance_20261105_01 | odoo17 | 43 MB | Développement — tests financiers |
| etat_civil_predeploy_20261104_2146 | odoo17 | 31 MB | Validation pré-déploiement |
| etat_civil_restore_validation_20261105_01 | odoo17 | 40 MB | Validation de restauration |
| etat_civil_retry_20261102b | odoo17 | 28 MB | À examiner — ancienne tentative |
| etat_civil_stability_20261101 | odoo17 | 30 MB | À examiner — ancien test stabilité |
| etat_civil_stability_20261102 | odoo17 | 30 MB | À examiner — ancien test stabilité |
| etat_civil_validation_20261104_2125 | odoo17 | 31 MB | Validation historique |
| etat_civil_validation_20261106_0100 | odoo17 | 42 MB | Validation récente |
| etat_civil_validation_restore_20261106_0100 | odoo17 | 40 MB | Validation de restauration récente |
| gestion_detat_civil | odoo | 43 MB | À examiner — anciennement/base principale possible |
| gestion_detat_civil_clean_odoo17 | odoo | 29 MB | À examiner — propriété `odoo`, rôle inconnu |
| gestion_detat_civil_test_odoo17 | odoo | 29 MB | Test probable, rôle à confirmer |
| postgres | postgres | 768 kB | Base système PostgreSQL — conserver |
| rich_vent | postgres | 7750 kB | Projet externe/à examiner |
| rich_vente | postgres | 7966 kB | Projet externe/à examiner |
| transport_coop | postgres | 8158 kB | Projet externe/à examiner |

Une base `rich_vente` est bien présente dans PostgreSQL. Sa taille précise affichée lors de l’inventaire était `7750 kB`; elle n’est pas liée au module `etat_civil`.

## 3. Comparaison des versions Odoo

Pour les bases accessibles `odoo17`, les modules vérifiés sont systématiquement :

- `base` : `17.0.1.3:installed`
- `web` : `17.0.1.0:installed`
- `etat_civil` : `17.0.2.1.8:installed`

Aucune base PostgreSQL Odoo 18 exploitable n’a été identifiée dans cette liste. Les bases appartenant à `odoo` n’ont pas pu être interrogées avec l’utilisateur `odoo17`; leur version reste indéterminée.

## 4. Identification de la base principale

La base principale est confirmée comme `etat_civil_odoo17_test` par l’utilisateur le 2026-11-06.

`config/odoo17.conf` a été complété avec `db_name = etat_civil_odoo17_test` après cette confirmation. La base de développement retenue provisoirement est `etat_civil_dev_latest_20261105`. La base de validation récente retenue est `etat_civil_validation_20261106_0100`.

Éléments ayant justifié ce choix :

- plus grande base `etat_civil`, 63 MB;
- contient Odoo 17 et le module `etat_civil` installé;
- contient 8 utilisateurs dont 4 actifs;
- contient 1 acte de naissance, 2 centres, 6 individus et 3 pièces justificatives;
- le dump `sauvegarde_avant_installation.dump` indique explicitement `dbname: etat_civil_odoo17_test`;
- l’ancien gestionnaire précédent utilisait `-d etat_civil_odoo17_test`.

Cette confirmation permet maintenant au gestionnaire d’utiliser explicitement la base principale. Elle ne modifie aucune donnée PostgreSQL ni aucun filestore.
La base `gestion_detat_civil` est aussi un candidat historique possible mais appartient à l’utilisateur PostgreSQL `odoo` et n’est pas accessible depuis `odoo17` sans modification de rôle. Elle est classée **À examiner**, pas principale.

## 5. Bases à conserver

### Base de développement récente

- `etat_civil_dev_latest_20261105` : dépôt récent, 41 MB, 46 modules installés, aucune donnée métier factice détectée. À conserver provisoirement.
- `etat_civil_dev_finalcheck_20261105` : 41 MB, 46 modules, à conserver comme référence de contrôle.

### Bases de validation importantes

- `etat_civil_validation_20261106_0100` : base récente contenant les trois types d’actes, 1 naissance, 1 mariage, 1 décès, 6 individus, 13 pièces, 3 registres et 5 utilisateurs actifs.
- `etat_civil_admin_roles_validation_20261104` : validation ciblée du rôle administrateur à préserver.
- `etat_civil_restore_validation_20261105_01` et `etat_civil_validation_restore_20261106_0100` : référencent des restaurations et doivent être conservées jusqu’à validation du retour arrière.

### Sauvegardes importantes

- `sauvegarde_avant_installation.dump`, lié à `etat_civil_odoo17_test`.
- `logs/implementation_odoo17/backups/etat_civil_validation_20261106_0100.dump`, 42 base récente.
- Six archives ZIP Odoo avec PostgreSQL + filestore, vérifiées comme lisibles et ZIP cohérentes.

## 6. Bases candidats à suppression

**Aucune suppression n’est recommandée à ce stade.**

Les bases ci-dessous sont seulement des **candidats d’observation future**, pas des autorisations de suppression :

- série `ec_workflow_test_20261101*` : anciennes bases de workflow; elles peuvent constituer des preuves de régression et ne doivent pas être supprimées sans confirmation;
- `etat_civil_retry_20261102b`, `etat_civil_stability_20261101/02` : anciennes bases de stabilisation; utiles comme historique jusqu’à preuve de remplacement;
- séries anciennes `audit_targeted`, `final_audit` et `isolated_review` : ne sont pas encore démontrées dupliquées entre elles.

La suppression doit rester à zéro jusqu’à confirmation de l’utilisateur et vérification restaurable de chaque dépendance.

## 7. Sauvegardes disponibles

- Dump PostgreSQL ancien vérifiable : `sauvegarde_avant_installation.dump`, créé le 2026-11-01, 4.87 MB, correspondant à `etat_civil_odoo17_test`.
- Dump validation récent : `logs/implementation_odoo17/backups/etat_civil_validation_20261106_0100.dump`, créé le 2026-11-06, 3.71 MB, correspondant à la base de validation 20261106.
- Toutes les archives ZIP présentes dans `logs/implementation_odoo17/backups/` passent `unzip -tqq`.
- Le script de dumping utilisé n’a pas été restauré dans cette phase; « archive lisible » ne remplace pas une restauration complète vérifiée.

Filestores Odoo présents sous `data/filestore` :

- `etat_civil_odoo17_test`, environ 29 MB;
- huit filestores de validation/revue, chacun environ 35–36 MB;
- aucun filestore explicitement associé aux bases propriétaires `odoo`.

## 8. Risques identifiés

- Absence de `db_name` et de `dbfilter`, empêchant l’identification automatique de la base principale.
- Impossible d’interroger les trois bases propriétaires `odoo` avec l’utilisateur `odoo17` sans disposer d’une autorisation PostgreSQL supplémentaire.
- De nombreuses bases sans identité fonctionnelle claire.
- Plusieurs copies partageant des dates et des tailles proches; un nom seul ne permet pas de prouver qu’elles sont identiques.
- Les sauvegardes ne sont pas toutes restaurées et vérifiées dans une base isolée.
- PostgreSQL utilise la version 18.6 alors que les installations Odoo sont Odoo 17; la compatibilité doit rester séparée.
- Les enregistrements métier de certaines bases sont peu nombreux ou synthétiques; les données utiles ne peuvent pas être supposées à partir du volume PostgreSQL.

## 9. Ressources inutilisées observées

- Un seul environnement virtuel `venv` existe et doit être conservé pour Odoo 17.
- Une seule installation principale Odoo existe dans `odoo`, 1.1 GB.
- `logs` occupe environ 39 MB; certains journaux sont volumineux mais contiennent des preuves de validation.
- `data` occupe environ 494 MB; les filestores ne doivent pas être nettoyés avant confirmation des bases.
- `venv` et `odoo` sont nécessaires au fonctionnement/migration; aucune ressource dans ces répertoires n’est classée supprimable.
- Seule la branche Git locale `main` est visible.
- 460 chemins Git ont des modifications locales ou ajouts; préserver tout le travail existant.

## 10. Script de nettoyage

`scripts/cleanup_odoo17.sh` est strictement non destructif.

Options disponibles :

- `--list-databases` : inventaire PostgreSQL;
- `--verify-backups` : vérification ZIP et index des dumps;
- `--help` : aide.

Le script ne contient ni `DROP DATABASE`, ni `dropdb`, ni `rm -rf`, ni arrêt de service, ni modification de configuration.

## 11. Plan proposé après autorisation

1. Obtenir confirmation de la base principale réelle.
2. Identifier les bases de développement et de validation retenues.
3. Ajouter explicitement `db_name` uniquement après confirmation, sans jamais utiliser `dbfilter` comme substitut.
4. Pour chaque suppression future, autorisation nominative explicite de l’utilisateur.
5. Avant chaque suppression autorisée: vérifier l’absence de processus et de connexions, sauvegarder la base PostgreSQL, vérifier `pg_restore --list`, sauvegarder le filestore associé, supprimer un seul objet, vérifier puis conserver un rapport.
6. Ne jamais supprimer les bases propriétaires `odoo` avant résolution de l’accès PostgreSQL et confirmation de leur rôle.

## 12. Conclusion de l’audit

Aucune base n’est actuellement certifiable comme principale. Aucune base candidate à suppression n’est proposée sans réserve. Le résultat de cette phase est un inventaire sécurisant, avec comme priorité de confirmer la vraie base de production et la base de développement avant toute modification.

# Audit des dépendances Odoo 17 — état après implémentation isolée

Date : 2026-11-05. Projet : `/home/ulrich/tous_les_projet/stage_l3_odoo/`. Branche `main`, HEAD observé `62315fb3a8cb904f374c978310382449568595e6`; dépôt très non propre avant intervention. Aucun changement existant n'a été nettoyé.

## Versions

| Composant | Résultat | Statut |
|---|---|---|
| Odoo | Sources du checkout, `Odoo Server 17.0` | VALIDÉ |
| Python | Venv du projet, Python 3.14.4 | VALIDÉ pour les exécutions observées; test fonctionnel de modules passé |
| PostgreSQL | PostgreSQL 18.6, cluster local sur 5432 | VALIDÉ pour ces DB de test; compatibilité de toute migration de données non testée |
| Dépendances Python | `pip check`: aucune dépendance cassée | VALIDÉ |
| Addons path | `odoo/odoo/addons`, `odoo/addons`, `custom_addons` et addons du `data_dir` | VALIDÉ depuis les journaux Odoo |

La documentation Odoo 17 indique Python 3.10+ et PostgreSQL 12+; les versions observées satisfont ces planchers. La compatibilité fonctionnelle de toutes les extensions n'est pas déduite de ces versions.

## Registre final réellement contrôlé

Base `etat_civil_dev_latest_20261105`, créée vide et synthétique; registre interrogé en lecture seule après installation :

| Module | État |
|---|---|
| `base`, `web`, `product`, `account`, `account_payment`, `etat_civil`, `etat_civil_auth_email`, `etat_civil_account` | installed |
| `point_of_sale` | uninstalled |

Modèles présents dans le registre : `account.move`, `account.move.line`, `account.payment`, `product.product`, `res.partner`. La présence du modèle POS n'est pas affirmée. Aucun module comptable ni POS n'a été installé dans la base de revue ou un service actif.

## Environnements et services

Les configurations de développement sont sous `/tmp/etat_civil_dev_*_20261105.conf`, mode 600. Les filestores isolés sont sous `data/implementation_odoo17_dev/filestore/<nom exact de DB>`. Les tâches cron sont désactivées. Voir `environnement-developpement.md` pour les DB, ports et journaux exacts.

Les ports existants 8071, 18071/18072 et 18205 n'ont pas été arrêtés ni redémarrés. Aucun accès en écriture n'a été fait dans les bases actives. POS reste facultatif et non installé.

## Résultats et risques

- `etat_civil`: suite complète sur DB synthétique, résultat Odoo `0 failed, 0 error(s) of 91 tests`; statistique de classe affichée par Odoo: 105 tests. L'écart entre le compteur de post-tests et la statistique interne est conservé tel quel dans `odoo-regression.log`.
- Addons e-mail et passerelle: dernière vérification sur DB fraîche, `0 failed, 0 error(s) of 12 tests`; stats par addon: 9 pour email, 7 pour finance. Ces compteurs Odoo incluent ses regroupements/sous-tests et ne sont pas additionnés comme tests métier distincts.
- Aucune facture, aucun paiement ni aucune délivrance métier n'ont été créés; chart of accounts et configuration de paiement complète n'ont pas été établis.
- `account_payment` est installé comme dépendance standard d'Account; cela ne signifie pas qu'un fournisseur ou un paiement réel est configuré.

**Statut : PARTIEL.** Versions, dépendances de base et registre de l'environnement synthétique vérifiés. Migration de comptes réels, authentification réelle d'utilisateurs et chaîne comptable complète restent à valider.

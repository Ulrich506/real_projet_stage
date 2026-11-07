# Journal des modifications de l'intervention

Date : 2026-11-05. Le dépôt était non propre avant le travail : nombreuses modifications et fichiers non suivis préexistants, notamment dans `custom_addons/etat_civil/`, `data/`, `logs/`, IDE et `odoo17.sh`. Aucun reset, clean, commit, push ou nettoyage n'a été fait.

## Fichiers source modifiés ou créés par cette intervention

| Type | Chemin | Détail | Précaution |
|---|---|---|---|
| Modifié, déjà dirty avant travail | `custom_addons/etat_civil/controllers/main.py` | `/api/v1/auth/login` n'utilise plus le nom de DB de l'appelant ni un fallback codé en dur; seule `request.db` est acceptée. Les autres différences préexistantes sont conservées. | Copie exacte préalable `backups/source-before-auth-api/main.py`, SHA mentionné dans `audit-utilisateurs-login.md`. |
| Créé | `custom_addons/etat_civil_auth_email/__init__.py`, `__manifest__.py` | Addon installable dépendant de base/web/etat_civil; hook index. | Nouvel addon, aucun fichier préexistant écrasé. |
| Créé | `custom_addons/etat_civil_auth_email/models/__init__.py`, `models/res_users.py` | Normalisation et validation login, uniqueness, `_login`. | Testé dans DB neuve. |
| Créé | `custom_addons/etat_civil_auth_email/views/login_templates.xml` | Label et champ login email. | HTTP et Chromium contrôlés. |
| Créé | `custom_addons/etat_civil_auth_email/tests/__init__.py`, `tests/test_email_login.py` | Tests unitaires ciblés. | 0 échec/erreur finaux. |
| Créé | `custom_addons/etat_civil_account/__init__.py`, `__manifest__.py` | Addon Account passerelle. | Nouvel addon, Account standard comme seule comptabilité. |
| Créé | `custom_addons/etat_civil_account/models/__init__.py`, `copy_tariff.py`, `copy_request.py`, `operation_event.py` | Tarifs, demande copie, liaison facture/paiement, transitions, journal immuable. | Tests ciblés; parcours complet non testé. |
| Créé | `custom_addons/etat_civil_account/security/security.xml`, `security/ir.model.access.csv` | Groupe Régisseur, droits ACL/record rules, Account invoice group pour régisseur/admin. | État exact validé par installation Odoo. |
| Créé | `custom_addons/etat_civil_account/data/sequences.xml` | Séquence demande copie. | Installée seulement dans DB synthétique. |
| Créé | `custom_addons/etat_civil_account/views/copy_request_views.xml` | Formulaires, listes, actions et menus. | Installée; test visuel métier authentifié non fait. |
| Créé | `custom_addons/etat_civil_account/report/__init__.py`, `report/copy_document.py`, `report/copy_document.xml` | Garde d'accès serveur au rendu du PDF de copie. | Installé; génération d'un PDF autorisé/non autorisé non exercée avec acte réel. |
| Créé | `custom_addons/etat_civil_account/tests/__init__.py`, `tests/test_copy_request_security.py` | Tests de sécurité et tarif. | 0 échec/erreur finaux. |

Aucun fichier Python/XML/JS/CSS/manifeste existant de `etat_civil` autre que le contrôleur ciblé n'a été édité par cette intervention. Les tests préexistants n'ont pas été retouchés. Odoo a pu générer des `.pyc` dans le checkout lors des installations; les `.pyc`/états Git préexistants n'ont pas été nettoyés.

## Livrables de suivi mis à jour

`audit-dependances.md`, `environnement-developpement.md`, `audit-utilisateurs-login.md`, `utilisateurs-a-migrer.csv`, `rapport-migration-login.md`, `tests-connexion.md`, `tests-financiers.md`, `rapport-implementation.md`, `procedure-retour-arriere.md`, `SHA256SUMS.txt`.

Journaux Odoo et preuves Chromium créés sous `logs/implementation_odoo17/`; sauvegardes synthétiques sous `logs/implementation_odoo17/backups/`.

## Bases et services

Six DB neuves de développement, de vérification et de régression ont été créées pour éviter les mises à jour concurrentes des instances en fonctionnement. Les six serveurs dédiés observés (18171/72, 18173/74, 18175/76, 18177/78, 18179/80, 18181/82) utilisent leurs filestores sous le `data_dir` dédié. Aucun acte métier n'a été modifié; aucun paiement ni aucune facture n'a été créé. Les tests Odoo utilisent des transactions et données synthétiques.

Une instance intermédiaire sur 18173/74 et l'instance initiale 18171/72 ont été laissées disponibles comme demandé; le serveur de référence correspondant à la dernière source est `etat_civil_dev_latest_20261105` sur 18181/82. Les autres instances de validation restent des DB et processus distincts, pas des copies de la base de revue.

Les bases actives/revue, ports 8071, 18071/18072 et 18205 n'ont subi aucune intervention d'arrêt ou d'écriture. Aucun compte réel n'a été modifié.

## Audit final du 2026-11-05

- Contrôlé les logs antérieurs, source Odoo 17 du checkout, addons civils/auth/account, ACL, record rules, rapports, modèles et routes.
- Vérifié que le paiement `state='posted'` est cohérent avec le modèle `account.payment` hérité de `account.move` du checkout Odoo 17; écart observé dans une autre installation système écarté.
- Après copie exacte et SHA du `copy_request.py` initial dans `backups/source-before-final-audit/copy_request.py`, ajouté verrouillage/relecture de la demande dans `action_submit` et `action_deliver`, et ordre stable par ID. Suite complète post-changement : 96 tests, zéro échec/erreur. Pas de test multithread dédié.
- Restauré une archive synthétique vers `etat_civil_restore_validation_20261105_01`, filestore correspondant vérifié (43/43 objets présents), démarrage HTTP/gevent 18183/18184 et health 200.
- Quatre comptes temporaires `@example.test` créés seulement dans la copie restaurée et authentifiés via HTTP API; aucune donnée de secret conservée dans les rapports.
- Tests financiers de bout en bout non exécutés. Les risques de logins historiques, rapports directs, concordance montant/facture et remboursement sont décrits dans les rapports finaux.
- Aucune base active/revue ou aucun compte réel modifié; aucun commit, push, reset ou clean exécuté.
- Une tentative de dump bloquée par `list_db=False` a laissé un fichier ZIP vide; celui-ci a été renommé `etat_civil_final_audit_tests_20261105_pre_update.empty-invalid` et explicitement marqué inutilisable. Le dump réessayé avec le réglage temporaire de processus est `...pre_update_verified.zip`, non vide et vérifié.
- `git diff --check` du dépôt complet signale de nombreux espaces finaux dans des journaux Git déjà modifiés (`logs/odoo17.log`, `logs/update_etat_civil.log` entre autres); ces journaux préexistants n’ont pas été réécrits par ce contrôle.

## Phase suivante — sécurisation et validation (2026-11-05)

Avant modification, le dépôt a été contrôlé (`git status --short`, `git diff` ciblé). Il était déjà très sale; aucun état préexistant n’a été nettoyé. Copies exactes préalables des sources sous `backups/source-before-phase-next/` :

- `custom_addons/etat_civil_auth_email/models/res_users.py` — SHA256 `3972df6936bae386d3ecdc0d6eb8ca3708cd6a31e3c931c09aa8d890c0df0322`.
- `custom_addons/etat_civil_auth_email/__manifest__.py` — `ddc04f9bd9ba0aae668754542c0022b9fc711579f6cb59cb9dedfd1a4f21d92d`.
- `custom_addons/etat_civil_auth_email/__init__.py` — `f9028de0845de4f9cdc83da6037594079d44535eb7a9b0c1d5f995f95c9d7d3e`.
- `custom_addons/etat_civil_account/models/copy_request.py` — `2c25e58251d88536162438ae85911d0483e50de6a1457c9552ef3fb381db26db`.
- `custom_addons/etat_civil/controllers/main.py` — `e31f404a1b823c7af830472c477af5aee8ebeac79d7f34036c09ba4865a07db0`.
- `custom_addons/etat_civil/tests/test_acte_workflow.py` — `8214036dc0bbcc8689ba8d9e63c5ad0d3e8c0ebb0584166522e6f952b7ced4f1`.

Sources changed: auth hook/pre-migration/version/index; demande de copie (snapshot product/unit/tax/total, concordance facture et rapprochement Account, paiement in_payment/paid, refus d’avoir posté, acte revalidé au rendu/délivrance, verrou d’annulation); API (health sans database, JSON login sans session_id); test health mis à jour. Les rapports QWeb legacy n’ont pas été changés en attendant clarification métier.

Bases synthétiques créées/restaurées : `etat_civil_phase_next_auth_20261105_01` depuis archive pré-auth; et `etat_civil_phase_next_finance_20261105_01` depuis archive régression pré-finance. Aucune base existante n’a été écrasée. Filestore de finance : 43 objets attendus, 0 manquant. Les données sont synthétiques. Pas de facture/paiement créé. Ports du test HTTP : 18191/18192, vérifiés libres avant usage et processus éphémère terminé ensuite.

Tests/commandes : archives `unzip -tq` valides; installation auth incompatible bloquée comme prévu; installation compatible 7 post-tests sans échec/erreur; mise à jour auth 7 post-tests sans échec/erreur; mise à jour account 5 post-tests sans échec/erreur; compileall + xmllint + git diff --check ciblé sans erreur; health HTTP 200 sans nom DB; login malformé HTTP 401 générique; capture Chromium page de login. Régression `HttpCase` en HTTP actif a terminé 96 post-tests avec 13 entrées ERROR dues à `ReadTimeout` vers le serveur temporaire, code de sortie 1; ne pas appeler cette suite verte. Le passage `--no-http` antérieur a également échoué et n’est pas retenu comme test de code.

Le compte admin `synthetic-admin@example.test` n’a été renommé que dans la copie auth isolée pour éprouver l’installation; hash/mot de passe inchangé. Aucun compte réel n’a été inventorié ou migré. Aucun commit/push/reset/clean exécuté. Aucun service préexistant arrêté ou redémarré.

**Précision de conservation :** `report/copy_document.py` a été modifié après sa lecture, mais son snapshot n’a pas été pris avant le patch. Un fichier de comparaison a ensuite été reconstitué en inversant l’unique changement observé (`_assert_deliverable_act()` → `_selected_act()`) à partir du contenu affiché dans l’audit. SHA du fichier reconstitué : `91d25d674bc64c47e6206e09769f476d43bad8d5d92343f25dc603af94d4b53e`. Ce n’est pas une copie binaire capturée avant écriture; cette limite est documentée et doit être prise en compte avant tout rollback.

Re-test final du précontrôle auth après ajustement comptes inactifs : restauration dans `etat_civil_phase_next_auth_incompatible_20261105_02` depuis l’archive synthétique pré-auth, puis installation refusée comme prévu avec diagnostic agrégé 1 login actif invalide, 4 inactifs conservés et 0 collision. Aucun login n’a été modifié; preuve `phase-next-auth-final-incompatible.log`.

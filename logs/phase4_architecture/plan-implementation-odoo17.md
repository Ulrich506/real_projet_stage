# Plan d’implémentation Odoo 17 — non exécuté

Toutes les phases ci-dessous sont prospectives. Il faudra une autorisation explicite de développement et une base isolée autorisée. Aucun module ne sera installé dans la base de revue par ce plan.

## Phase A — Préparer l’environnement isolé

- **Fichiers:** aucun fichier métier au départ; documenter config Odoo/addons, logs, DB de test et filestore isolés.
- **Dépendances:** checkout Odoo 17 cohérent, PostgreSQL de test, Chromium, wkhtmltopdf selon rapports.
- **Risques:** confusion base/filestore, port/service actif, secrets dans logs.
- **Tests:** identité du processus, chemins core/addons, DB sélectionnée, filestore associé, ports dédiés.
- **Acceptation:** environnement reproductible sans contact avec 8071/18205 ou base réelle.
- **Preuves:** inventaire versions/path, health HTTP, configuration expurgée des secrets, DB name et filestore map.

## Phase B — Vérifier/installer dépendances standards en environnement de test seulement

- **Fichiers:** aucun code custom; manifestes officiels présents dans le checkout seulement.
- **Dépendances:** addon `product` et `account`; éventuellement `account_payment`; POS uniquement après décision.
- **Risques:** installation modifie schéma, données par défaut, droits, société/journaux/taxes; dépendances Odoo.
- **Tests:** installation dans DB temporaire vierge, registre des modèles, configuration comptable MGA, facture test synthétique puis rollback/destruction de DB de test par procédure autorisée.
- **Acceptation:** `account.move`, lines, `account.payment`, `product.product` enregistrés et workflows Account compris; aucune mise à jour revue.
- **Preuves:** logs install, liste modules/modèles, paramètres entreprise et résultats tests synthétiques.

## Phase C — Développer `etat_civil_account`

- **Fichiers prévus:** `custom_addons/etat_civil_account/__manifest__.py`, `__init__.py`, `models/*`, `security/*`, tests unitaires. Voir `plan-modifications.md` pour inventaire précis.
- **Dépendances:** `etat_civil`, `account`; standard `product` via `account`.
- **Risques:** relation vers acte abstrait, concurrence gratuité, snapshots prix, règles multi-centres.
- **Tests:** modèle, contrainte 3 FK exactly-one, droits, tarif/période, entitlement concurrent, migration install.
- **Acceptation:** nouvelle base de test installe; ancien `etat_civil` demeure indépendant; aucune comptabilité custom.
- **Preuves:** logs Odoo, schéma ORM et tests TransactionCase.

## Phase D — Relier demandes de copie et factures

- **Fichiers:** `models/copy_request.py`, `copy_tariff.py`, séquence, vues demande/tarif, tests account invoice.
- **Dépendances:** C et configuration entreprise/journal/produit/taxe.
- **Risques:** doublons de facture, partenaire incorrect, tarif modifié, facture postée depuis mauvais centre.
- **Tests:** gratuite sans invoice; tarif absent/ambigu; invoice client unique par request, idempotence, snapshot et avoir de test.
- **Acceptation:** création de facture via API ORM standard; invoice references une demande et aucun paiement n’est généré implicitement.
- **Preuves:** records synthétiques demande/facture/lignes et audit transaction.

## Phase E — Paiements et Régisseur

- **Fichiers:** groupe Regisseur, méthodes métier de confirmation, extension légère de `account.payment` si reçu/référence l’exige, views dashboard de base, tests paiement.
- **Dépendances:** `account`; choix de journal et DEC-006 à 009.
- **Risques:** saisie confondue avec encaissement, rapprochement banque mal interprété, séparation tâches insuffisante.
- **Tests:** draft, posted, partial, in_payment, paid, annulation, retour, double confirmation, droit center/company.
- **Acceptation:** confirmation régisseur n’altère pas de champ comptable; aucune copie payable ne passe en autorisée sans état prérequis.
- **Preuves:** rapprochements synthétiques, événement acteur/date et refus négatifs.

## Phase F — Sécuriser les accès, fichiers et workflows

- **Fichiers:** ACL/rules bridge, routes/report contrôleur, validations des pièces seulement si besoin démontré, journal événement.
- **Dépendances:** groupes civils, centres et règles actuelles; politique conservation.
- **Risques:** `sudo`, route/report direct, `web/content`, IDOR, cache PDF, unlink justificatifs.
- **Tests:** `with_user`, ORM/RPC/HTTP/URL/report, centre croisé, fichiers image/PDF, téléchargement et viewer.
- **Acceptation:** toutes actions sensibles refusent les acteurs non habilités à chaque surface; preuves sans données réelles.
- **Preuves:** codes HTTP, captures Chromium authentifiées, traces audit, rapports test sécurité.

## Phase G — Tableaux de bord et reçus

- **Fichiers:** menus/actions/views dashboard, rapport reçu si celui standard n’est pas suffisant, rapport copie final et QWeb.
- **Dépendances:** source de données Accounting; DEC-010, DEC-019.
- **Risques:** chiffres divergents, exposition financière, reçu légal erroné, PDF avant gate.
- **Tests:** rapprochement indicateurs avec lignes comptables synthétiques, périodes/centres, reçus annulés/réimprimés, accès direct.
- **Acceptation:** totaux liés aux données Odoo et filtrés; impression reçus/copies sous autorisation serveur.
- **Preuves:** captures, calculs rapprochés, PDF text/visual checks.

## Phase H — Tests unitaires, intégration et sécurité

- **Fichiers:** `tests/test_copy_request.py`, `test_copy_accounting.py`, `test_copy_security.py`, HTTP tour/JS selon choix.
- **Dépendances:** DB dédiée et données synthétiques uniquement.
- **Risques:** tests modifient bases partagées ou ne testent pas les endpoints.
- **Tests:** 25 cas d’acceptation, race concurrency, Odoo HttpCase, suite ciblée.
- **Acceptation:** zéro fail/erreur inattendue; noms de base/date/commit et skips justifiés.
- **Preuves:** logs complets expurgés, XML/JSON résultats, checksum et base utilisée.

## Phase I — Validation fonctionnelle avec données de test

- **Fichiers:** aucun nouveau fichier attendu; éventuels correctifs isolés autorisés séparément.
- **Dépendances:** comptes Agent/Officier/Régisseur/Admin synthétiques, fixtures non réelles, Chromium.
- **Risques:** identifiants secrets, données réelles, résultats de clics confondus avec droits serveur.
- **Tests:** parcours création, première copie, copie payante, réception/vérification pièce, paiement, délivrance et reconsultation.
- **Acceptation:** preuves par rôle et tests backend/API cohérents; utilisateurs saisissent eux-mêmes leurs identifiants si nécessaire.
- **Preuves:** captures sans données personnelles, requêtes HTTP/RPC, invoice/payments synthetic.

## Phase J — Préparer déploiement, sauvegarde et retour arrière

- **Fichiers:** runbook déploiement, migration, sauvegarde/restore et rollback; pas de changement actif sans approbation distincte.
- **Dépendances:** feu vert métier/comptable/sécurité, sauvegarde PostgreSQL + filestore exactement correspondant, fenêtre d’intervention autorisée.
- **Risques:** schéma partiellement migré, filestore croisé, perte de configuration, module Accounting inattendu.
- **Tests:** restore rehearsal dans environnement isolé, intégrité PostgreSQL/attachments et rollback applicatif/données.
- **Acceptation:** rollback chronométré et documenté; aucune mise à jour active dans cette phase documentaire.
- **Preuves:** checksums sauvegardes, logs restore, liste modules et smoke tests post-restore.

## Conditions de passage entre phases

DEC-001 à DEC-022 pertinentes résolues, code de travail isolé de l’état préexistant non propre, revue sécurité approuvée, base test identifiée, données synthétiques, sauvegardes pour toute DB cible. Les phases B–J ne sont pas démarrées par ce livrable.

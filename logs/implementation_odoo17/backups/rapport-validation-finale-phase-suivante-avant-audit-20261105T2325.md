# Rapport de validation finale — phase suivante

Date/heure : 2026-11-05 22:11 EAT (+03:00). Statut global : **B — PARTIELLEMENT VALIDÉ**. Environnement : checkout Odoo 17.0; Python 3.14.4; PostgreSQL 18.6. Les tests d’écriture de cette phase ont ciblé des bases synthétiques neuves/restaurées uniquement.

## Résumé des résultats

| Domaine | Résultat |
|---|---|
| Auth e-mail | Pré-init refuse une base avec identifiant actif non e-mail; install et upgrade compatibles ont chacun exécuté 7 tests sans erreur. Comptes inactifs non conformes conservés. Connexion positive HTTP/browser non refaite. |
| Comptabilité | Garde de concordance facture/demande et paiement renforcé; addon mis à jour et 5 tests ciblés sans erreur. Aucune facture/paiement/avoir E2E créé. |
| Régression civile/API | Exécution complète de 96 post-tests a terminé avec 13 erreurs ReadTimeout dans HttpCase; ne pas revendiquer succès. 105 stats civiles, 7 compte module affichées; la suite n’est pas verte. |
| API publique | Health HTTP 200 sans nom de base; login invalide HTTP 401 générique; le JSON ne renvoie plus `session_id` selon code. |
| PDF / délivrance | Rapport de copie garde serveur renforcé; rapports directs d’acte restent accessibles aux groupes existants; classification juridique à décider. Tests URL/PDF manquants. |
| Concurrence | Verrous présents/revus, annulation verrouillée; aucune transaction réellement concurrente. |
| Chromium | Page login ouverte et capturée; pas de session authentifiée par rôle. |
| Restauration | Archive synthétique restaurée sous nouvelle base; 43 pièces stockées, 0 objet filestore absent. Aucun restore sur base existante. |

## Bases, ports et preuves

- Auth : `etat_civil_phase_next_auth_20261105_01` (installation compatible après modification ORM d’un compte synthétique) et `etat_civil_phase_next_auth_incompatible_20261105_02` (installation refusée sur login actif invalide); logs `phase-next-auth-final-incompatible.log`, `phase-next-auth-compatible-install.log`, `phase-next-auth-upgrade.log`.
- Finance/régression : `etat_civil_phase_next_finance_20261105_01`, filestore `data/implementation_odoo17_dev/filestore/etat_civil_phase_next_finance_20261105_01`; archive source `backups/etat_civil_dev_regression_20261105_pre_finance_retest.zip`, SHA 61ac9b97e9f32b4f622b45b58e524f8685009557c76c2b65e04d4269cc0903d6; logs `phase-next-finance-final-tests.log`, `phase-next-regression-http.log`, `phase-next-regression-correct-db.log`.
- Essai HTTP/Chromium : 18191/18192, processus propre à la base synthétique terminé; capture et réponses dans `proofs/phase-next-*`.
- Services préexistants : 8071, 18071/18072, 18181/18182, 18183/18184, 18205 toujours en écoute lors du contrôle après essai. Aucun d’eux redémarré.

Commandes clés : `unzip -tq` sur trois archives; `venv/bin/python odoo/odoo-bin ... -i/-u ... --test-enable`; `compileall`; `xmllint --noout`; `curl` endpoints de test; Chromium headless screenshot; audit ORM en lecture seule des objets filestore. Les sorties détaillées sont dans les logs cités.

## Modifications cette phase

- `etat_civil_auth_email`: pre-init et pre-migrate, diagnostic agrégé et migration index unique, version `17.0.1.0.1`.
- `etat_civil_account`: snapshots du prix/produit/taxes, concordance facture, paiement prouvé par partial reconciliations de la facture même, blocage note de crédit et contrôle de l’état de l’acte; verrou d’annulation.
- `etat_civil/controllers/main.py`: suppression du nom DB public et session_id JSON.
- `etat_civil/tests/test_acte_workflow.py`: assertion health sans clé database.
- Aucune migration d’utilisateurs réels; aucun compte, facture ou paiement de production/revue modifié.

## Décision

Pas de mise en production. Préconditions restantes : parcours comptable E2E avec configuration fictive, concurrence multi-transaction, validation des rapports officiels/interne par métier puis tests directs, authentification Chromium de comptes synthétiques, remboursement et régression HTTP verte. Aucun commit/push réalisé. Les changements Git préexistants ont été conservés.

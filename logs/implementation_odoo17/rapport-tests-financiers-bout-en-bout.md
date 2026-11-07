# Rapport — tests financiers de bout en bout

Date/heure : 2026-11-05 22:11 EAT (+03:00). Base disponible pour tests : `etat_civil_phase_next_finance_20261105_01`, restaurée vers un nom neuf depuis `backups/etat_civil_dev_regression_20261105_pre_finance_retest.zip`; Odoo 17.0, Python 3.14.4, ports de test HTTP/gevent 18191/18192; processus temporaire arrêté après vérification HTTP. Filestore restauré de la même archive : 43 pièces jointes stockées, 0 objet manquant.

## Tests réellement exécutés

| Scénario | Préparation/action | Résultat | Statut |
|---|---|---|---|
| Mise à jour `etat_civil_account` | `-u etat_civil_account --stop-after-init --no-http --test-enable --test-tags /etat_civil_account` | 5 post-tests, aucune erreur ni assertion; log `phase-next-finance-final-tests.log`. | TERMINÉ ET TESTÉ |
| Gratuité, acte synthétique et PDF | Aucun acte/demande ni PDF créé. | Non exécuté. | NON IMPLÉMENTÉ |
| Facture créée/postée, paiement complet, régisseur, copie PDF | Aucun compte bancaire/journal/produit/taxe de test, aucune facture ou paiement généré. | Non exécuté. | NON IMPLÉMENTÉ |
| Paiement partiel, facture mal paramétrée, autre partenaire/devise | Garde serveur statique seulement. | Non exécuté. | TERMINÉ MAIS NON TESTÉ |
| Annulation, avoir et remboursement | Aucun avoir/remboursement dans Odoo. | Non exécuté. | NON IMPLÉMENTÉ |
| Régression HTTP complète | Les 96 post-tests atteignent la fin, 13 erreurs ReadTimeout; commande code 1. | Blocage du client HTTP de la suite. | BLOQUÉ |

## Suite de régression

Une exécution correcte de 96 post-tests sur la base restaurée a atteint le résumé, mais a quitté avec code 1 : 13 erreurs `ReadTimeout` de tests `HttpCase` vers le serveur temporaire, malgré 18191 à l’écoute; le log est `phase-next-regression-http.log`. Une tentative antérieure avec `--no-http` a aussi échoué car les tests HTTP ne pouvaient pas appeler leur serveur. Ces exécutions ne prouvent donc pas une régression code, mais la suite HTTP n’est pas validée. Aucun résultat de ces exécutions n’est compté comme test réussi.

Aucun rapprochement bancaire, journal de revenus, configuration fiscale, tarif métier ou reçus commune n’a été modifié. Les tests unitaires/ciblés ne sont pas présentés comme parcours complet. Statut des parcours financiers : NON IMPLÉMENTÉ pour la preuve E2E; statut global B.

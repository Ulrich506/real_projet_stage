# Rapport — tests de concurrence

Date/heure : 2026-11-05 22:11 EAT (+03:00). Odoo 17.0, PostgreSQL 18.6, environnement synthétique du checkout; pas de test de concurrence multi-transaction lancé.

## Revue du verrouillage

`action_submit`, `action_create_invoice`, `action_confirm_payment`, `action_deliver` et `action_cancel` verrouillent maintenant la ligne `etat_civil_copy_request` avec `SELECT ... FOR UPDATE`, relisent les champs après le verrou et trient les demandes par ID lorsqu’elles sont traitées en lot. `action_submit` verrouille en plus la ligne de l’acte avant de calculer copie précédente et réservation de gratuité. Cette stratégie protège la double transition d’une demande et sérialise l’allocation d’une première copie pour le même acte.

Le code contrôle les états actuels avant la transition; les événements sont créés dans la transaction. La correction à `action_cancel` a été faite pendant cette phase pour éviter annulation concurrente avec délivrance.

## Résultats

| Course | Analyse source | Transactions concurrentes exécutées | Statut |
|---|---|---|---|
| Deux soumissions même demande | Verrou request + relecture | Non | TERMINÉ MAIS NON TESTÉ |
| Deux délivrances même demande | Verrou request + relecture | Non | TERMINÉ MAIS NON TESTÉ |
| Deux demandes simultanées de première copie | Verrou commun de l’acte | Non | TERMINÉ MAIS NON TESTÉ |
| Confirmation et annulation | Verrou request et relecture | Non | TERMINÉ MAIS NON TESTÉ |
| Annulation et délivrance | Verrou ajouté à l’annulation; états exclusifs | Non | TERMINÉ MAIS NON TESTÉ |

Les 5 tests unitaires ciblés de la passerelle réussissent, mais ne créent pas deux curseurs/transactions qui se chevauchent. Le test de concurrence réelle demandé reste bloquant avant production; les cas doivent être exercés avec plusieurs connexions PostgreSQL sur une base synthétique dédiée et vérifier qu’un seul événement de délivrance/gratuité est enregistré.

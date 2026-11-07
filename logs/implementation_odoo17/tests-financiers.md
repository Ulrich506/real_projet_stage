# Tests financiers — passerelle Odoo Accounting

## Base et modules

Tests ciblés finaux effectués sur `etat_civil_dev_latest_20261105` (DB synthétique), sources Odoo du checkout. `account`, `account_payment`, `product`, `etat_civil`, `etat_civil_account` installés; `point_of_sale` laissé désinstallé. Registre contrôlé : `account.move`, `account.move.line`, `account.payment`, `product.product`, `res.partner` présents.

## Contrôles exécutés

| Test | Résultat | Statut |
|---|---|---|
| Demande avec zéro acte typé | Refus par contrainte ORM | VALIDÉ |
| Changement direct du statut par ORM/RPC | Refus | VALIDÉ |
| Confirmation paiement sans rôle Régisseur/Admin | Refus serveur | VALIDÉ |
| Tarif négatif | Refus | VALIDÉ |
| Installation vues, modèles, ACL, record rules et rapport sécurisé | Réussie | VALIDÉ |
| Suite module `etat_civil_account` | 7 au compteur Odoo; `0 failed, 0 error(s)` | VALIDÉ |
| Suite `etat_civil` complète sur base synthétique séparée | 91 post-tests; stats Odoo 105; `0 failed, 0 error(s)` | VALIDÉ |

Logs : `odoo-latest.log` et `odoo-regression.log`. Ces tests unitaires/statistiques ne constituent pas un test de facturation de bout en bout.

## Fonctionnalités de code disponibles mais non testées de bout en bout

Le nouveau module définit tarifs datés et par centre, demandes reliées à un des trois modèles d'actes concrets, association unique à `account.move`, génération d'une facture brouillon via Account, condition paiement (facture postée, résiduel nul, état paid, paiement posted rapproché à la facture, option `is_matched` par paramètre), confirmation côté Régisseur/Admin, journal d'événements protégé, annulation draft par transition native Account, refus d'annulation d'une facture postée, et garde au rendu du rapport avant/après confirmation.

Aucune facture, ligne comptable, paiement, reçu, demande métier, tarif en monnaie réelle ou acte n'a été créée. Aucun plan comptable de commune, journal, taxes, devise de caisse ou méthode de paiement n'a été configuré. Aucune facture n'a été postée, aucun paiement n'a été rapproché, et aucune confirmation Régisseur ni délivrance PDF autorisée n'a été effectuée.

## Statut des scénarios métier/acceptation

- Gratuité première copie, demandes concurrentes, tarif absent/actif, facture brouillon/postée, paiement partiel/complet, reconciliation banque, annulation/remboursement, double délivrance, URLs PDF directes avec acte existant : **NON TESTÉ** ou **PARTIEL** (contrôles unitaires seulement).
- Sécurité center-à-center sur actes réels et attachements : **NON TESTÉ** dans cette passerelle.
- POS, sessions de caisse, POS order/payment : **NON TESTÉ**, module absent du registre final.
- Tableau de bord Régisseur : **NON IMPLÉMENTÉ** dans le module livré.
- Reçus : aucune comptabilité de reçus parallèle n'a été créée; leur émission/consultation relève du processus Account à définir. Une vue métier complète des reçus reste **NON IMPLÉMENTÉE**.

**Conclusion financière : PARTIEL.** La passerelle compile, s'installe et ses contrôles unitaires ciblés passent, mais l'acceptation comptable complète requiert une configuration comptable de test et des scénarios d'intégration synthétiques.

Pendant l'installation, Odoo a d'abord rejeté la vue `partner_id` pour absence du champ dépendant `company_id`; la vue a été corrigée et les installations/tests finaux ont réussi. Aucun artefact comptable n'a été créé par cet échec ou les tests.

## Retest final après audit de concurrence

Upgrade/test de `etat_civil_account` puis `etat_civil` sur `etat_civil_final_audit_tests_20261105` : 96 post-tests au total, zéro échec/erreur; détail dans `odoo-final-audit-regression.log`. Les tests restent des tests ORM. Aucun parcours de facture, paiement, remboursement, reçu ou document délivré n’a été effectué. Le checkout Odoo 17 définit ici `account.payment` avec l’état hérité d’`account.move`; `state='posted'` correspond donc à ce checkout, et ne doit pas être déduit de l’installation système parallèle.

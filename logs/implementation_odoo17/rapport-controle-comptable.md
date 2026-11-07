# Rapport — contrôle de la passerelle comptable

Date/heure : 2026-11-05 22:11 EAT (+03:00). Odoo 17.0 du checkout; Python 3.14.4; PostgreSQL 18.6. Base de contrôle `etat_civil_phase_next_finance_20261105_01`, restaurée d’une archive synthétique, filestore correspondant. `account` est disponible et installé dans cette copie; POS n’a pas été utilisé.

## Revue et correction

La passerelle utilise les modèles standards `account.move`, `account.payment`, `account.tax` et `product.product`; aucun ledger parallèle n’est ajouté. Avant cette phase, la seule condition de paiement contrôlait facture postée, paiement_state payé et résiduel nul. Cela ne garantissait pas que la facture était celle de la demande ni que son partenaire, sa devise, ses lignes, prix et taxes correspondaient.

Changements faits dans `models/copy_request.py` :

- La demande conserve le produit, le prix unitaire et les taxes effectives à la soumission. Les taxes sont mappées avec la position fiscale du partenaire; `amount` correspond au total TTC calculé par Odoo. Première copie gratuite demeure contrôlée par la configuration synthétique du tarif.
- La création de facture verrouille la demande, accepte un seul document et utilise produit/prix/taxes figés. Une devise de tarif différente de la devise société est explicitement refusée faute de journal étranger configuré.
- Avant confirmation et à chaque impression/délivrance, la facture doit être une `out_invoice`, être liée à cette demande, être postée, appartenir au partenaire et à la société demandés, être dans la devise attendue et avoir exactement une ligne avec produit, quantité, prix, taxes et total attendus.
- Le paiement doit provenir des lignes de rapprochement de cette facture même, être `account.payment` entrant client, comptabilisé, même partenaire/société/devise et rapproché de la facture. Les rapprochements partiels doivent couvrir le total; une note de crédit/write-off ne compte pas comme paiement. `paid` ou `in_payment` est acceptable si résiduel nul et rapprochement facture-paiement intégral. Le rapprochement bancaire reste optionnel via `etat_civil_account.require_bank_match`; la décision communale sur cette exigence reste ouverte.
- Une note de crédit postée liée par `reversed_entry_id` bloque la délivrance. La comptabilité conserve son historique; aucun document comptabilisé n’est supprimé.
- L’annulation de demande verrouille et relit aussi son état; l’état de l’acte est contrôlé à la délivrance et au rendu du rapport.

Odoo 17 checkout: `account.payment` hérite de `account.move`; `state='posted'` et les liens de réconciliation sont confirmés dans `odoo/addons/account/models/account_payment.py`, `account_move.py` et `account_partial_reconcile.py`. `reconciled_invoice_ids` est calculé non stocké; le nouveau code ne l’utilise plus comme domaine de recherche.

## Limites de preuve

Les contrôles de concordance sont revus statiquement et la mise à jour de schéma/module a réussi; 5 tests ciblés `etat_civil_account` réussissent. Aucun journal, produit, compte de revenu, taxe, facture, paiement, avoir ou remboursement synthétique de bout en bout n’a été créé dans cette base. Les scénarios de montant inférieur/supérieur, devise, partenaire, paiement partiel/annulé, rapprochement, avoir et remboursement ne sont donc pas dynamiquement validés.

| Cas de contrôle | Code serveur | Exécution réelle | Statut |
|---|---|---|---|
| Mauvais montant / produit / taxes / partenaire / société / devise | Refus par `_invoice_matches_request` | Pas de facture de scénario | TERMINÉ MAIS NON TESTÉ |
| Facture annulée ou non postée | Refus | Pas de scénario comptable | TERMINÉ MAIS NON TESTÉ |
| Paiement autre facture / partiel / non comptabilisé | Refus par lignes de rapprochement et montant résiduel | Pas de scénario comptable | TERMINÉ MAIS NON TESTÉ |
| Paiement complet même facture | Contrôle code présent | Non réalisé | TERMINÉ MAIS NON TESTÉ |
| Avoir/remboursement | Avoir posté lié bloque; aucun workflow régisseur-remboursement | Non réalisé | NON IMPLÉMENTÉ |
| Taxes/devise étrangère/journaux communaux | Devise étrangère refusée sans journal configuré; paramétrage non fait | Non réalisé | EN ATTENTE DE VALIDATION MÉTIER |
| Confirmation du régisseur | Groupe et contrôle côté serveur présents | Pas de compte/opération finance E2E cette phase | TERMINÉ MAIS NON TESTÉ |

Anomalie résiduelle ÉLEVÉE : aucun flux de remboursement complet ne relie avoir, paiement sortant et état de demande; la politique après délivrance et contestation doit être décidée et développée avant exploitation.

# Workflow des copies et délivrances

## Statuts séparés

| Domaine | États existants ou proposés | Autorité |
|---|---|---|
| Acte | `brouillon`, `en_attente`, `a_corriger`, `valide`, `rectifie`, `annule`, `archive` (selon workflow actuel) | Modèle `etat.civil.acte.officiel`; action Agent/Officier/Admin métier. |
| Pièce | `a_fournir`, `recu`, `verifie` | `etat.civil.piece.justificative`; Agent reçoit, Officier vérifie. Aucun état rejeté actuel. |
| Facture | états standards Odoo `draft`, `posted`, `cancel` et `payment_state` comptable | `account.move`; seuls groupes Accounting et règles standard. |
| Paiement | `account.payment.state` (état de l’écriture de paiement), `is_reconciled`, `is_matched`; aucun ne doit être confondu avec facture payée | `account.payment`/lignes de rapprochement; pas de write du bridge sur état financier. `is_matched` vise le relevé bancaire. |
| Demande de copie | cible `draft`, `awaiting_payment`, `payment_confirmed`, `authorized`, `delivered`, `canceled`, `rejected` | Nouveau modèle passerelle, transitions Python exclusivement. |

La réception d’une pièce, sa vérification, la validation de l’acte, le règlement d’une facture et la délivrance d’une copie restent des événements distincts. La validation d’acte ne crée pas de facture et un paiement ne valide pas un acte.

## Parcours gratuit proposé

1. Un Agent/Officier/Admin autorisé demande une copie liée à un acte existant.
2. Le service vérifie ACL/règle de centre, que l’acte est `valide` ou `rectifie` et n’est ni annulé ni archivé; vérifie la compétence/qualité de demandeur suivant règle à décider.
3. L’action verrouille l’acte en base, examine les délivrances et réservations en cours, puis détermine si l’entitlement première copie est toujours disponible. Le type `first` ne vient pas du client.
4. Si l’entitlement est disponible, la demande est enregistrée comme première copie gratuite, montant calculé 0 et motif d’éligibilité, sans facture/paiement.
5. L’Agent autorisé (ou admin) autorise la délivrance; action serveur revalide encore entitlement et acte.
6. `action_deliver()` verrouille la demande, attribue numéro/date, auteur et marque `delivered` dans la même transaction. L’historique conserve cet usage; aucune suppression/remise à zéro.
7. Le rapport final n’est rendu que par l’action de délivrance, après nouveau contrôle à chaque requête URL/RPC.

Annuler/rejeter la demande avant délivrance peut libérer la réservation selon motif et autorité; une délivrance déjà enregistrée n’est jamais effacée. Le propriétaire métier doit confirmer si une demande annulée conserve ou libère le bénéfice gratuit.

## Parcours payant proposé

1. L’utilisateur demande un extrait/duplicata avec lien à un acte autorisé.
2. Sous verrou acte, le service détermine que l’entitlement première copie est déjà consommé ou réservé; marque `additional` et choisit le tarif actif par type, centre, société et date.
3. Aucun tarif ou plusieurs tarifs applicables → transaction refusée avec anomalie claire; aucun montant codé en dur et aucun fallback « gratuit ».
4. L’utilisateur voit le montant, devise, taxes et produit avant confirmation de demande. Snapshot figé dans la demande.
5. La méthode crée exactement une facture client `account.move` standard associée à un seul request. Elle utilise `res.partner`, produit service et taxes configurés; l’état reste `awaiting_payment`. Les demandes ne créent pas `account.payment`.
6. Le paiement est enregistré dans le journal Accounting standard (ou POS si cette option est approuvée et dédiée). Un reçu attaché ou annoncé seul ne marque rien comme payé.
7. Le Régisseur ouvre la demande et la facture liée; vérifie montant, devise, référence, confirmation matérielle d’encaissement selon procédure, annulation/avoir, et état des paiements rapprochés à la facture. `account.payment.state == 'posted'` signifie que l’écriture du paiement est comptabilisée. Le paiement peut être rapproché à la facture sans rapprochement bancaire (`is_matched`); l’exigence de rapprochement bancaire reste [À CONFIRMER]. Pour paiement partiel, facture `in_payment`, facture annulée ou impayée, l’action refuse.
8. `action_confirm_payment()` applique ACL et contrôle de groupe Régisseur/Admin, verrouille la demande, relit via ORM : facture client `posted`, partenaire/société/montant/devise exacts, `amount_residual` nul et `payment_state == 'paid'`; examine les paiements rapprochés, leur état `posted`, retours/avoirs et références non annulées. Il enregistre l’acteur/horodatage/références de paiements dans un journal append-only. Double appel ne poste rien et ne répète pas le journal. La condition « encaissement matériellement reçu » par Régisseur reste une attestation métier distincte de l’état comptable, à définir.
9. La demande passe à `payment_confirmed`, puis `authorized`. Les contrôles sont rejoués avant délivrance.
10. À la remise, la demande est verrouillée, vérifie encore l’état complet du paiement (et que demande non annulée, facture/payments non inversés), réserve le numéro de copie et devient `delivered`.
11. Le PDF final est rendu après ces contrôles. Une route directe, action rapport standard, `web/content`, RPC ou autre client ne peut pas rendre le document en contournant `action_deliver`.

## Annulation, remboursement et incidents

- Demande payante annulée avant facture : annulation tracée, aucun invoice.
- Facture créée mais non postée : action Accounting autorisée pour annuler la demande; ne pas supprimer la facture sans procédure de comptabilité.
- Paiement partiel : reste en attente; aucun accès au PDF.
- Annulation après paiement mais avant délivrance : ne pas supprimer ni modifier directement paiement/facture postés. Révoquer l’autorisation côté état civil, ouvrir une tâche d’avoir/remboursement via le processus comptable autorisé et garder la demande/historique; [À CONFIRMER] si la demande est réactivable après remboursement.
- Remboursement : utiliser avoir (`account.move` de type refund) et remboursement comptabilisé/rapproché selon la politique Account; l’extension ne supprime pas l’écriture. Bloquer toute délivrance future et journaliser les références. Les champs exacts du workflow d’avoir/remboursement restent à valider dans la configuration cible.
- Délivrée puis contestée : ne pas révoquer ou supprimer le PDF/historique; consigner un incident et traiter remboursement/avoir séparément. [À CONFIRMER] pour les effets administratifs/légaux.
- Paiement annulé/inversé/avoir avant livraison : révoquer l’autorisation et retourner en `awaiting_payment` ou `rejected` selon décision, avec évènement d’audit; ne pas effacer l’historique comptable.
- Paiement remboursé après livraison : créer incident/réclamation auditée; l’acte délivré n’est pas révoqué silencieusement.
- Double confirmation : refuser transition ou renvoyer l’état déjà confirmé sans side effects; jamais créer un nouvel `account.payment`.
- Paiement consolidé sur plusieurs factures : reporté hors premier lot; le bridge initial exige une relation non ambiguë et paiements rapprochés imputés à l’unique facture de la demande.
- Échec du module financier ou modèle inaccessible : pas de confirmation optimiste; demande reste bloquée et journalise une erreur sans fuiter les détails privés.

## Document final et contrôles d’URL

Créer un rapport distinct basé sur `etat.civil.copy.request`, pas une URL publique du rapport `etat.civil.acte.*`. Avant première délivrance, son contrôleur/chemin serveur vérifie utilisateur, ACL/règle, centre, autorisation, état de facture/paiement courant et acte; le simple état local `authorized` ne suffit pas si le paiement a depuis été annulé. Après délivrance, la consultation d’une copie archivée s’autorise depuis l’historique immuable `delivered` et les droits d’accès courants; elle ne réécrit ni n’efface la remise passée si un remboursement intervient plus tard. `attachment_use=False` évite un cache commun qui contourne l’autorisation. Inline et téléchargement volontaire reçoivent le même contrôle de propriétaire/centre et journalisation.

La possibilité de visionner directement dans navigateur ne réduit pas la sensibilité du document; aucun token public ne doit être créé. Les logs doivent indiquer une référence interne et acteur/heure, sans nom de fichier personnel ou contenu du document.

## Tests prévus (exécutables seulement dans base isolée autorisée)

`FIRST01` entitlement disponible; `FIRST02` seconde demande simultanée; `FIRST03` annulation puis nouvelle demande; `COPY01` acte non validé refusé; `COPY02` tarif manquant; `COPY03` tarifs chevauchants; `COPY04` facture idempotente; `PAY01` état unpaid; `PAY02` partial; `PAY03` in-payment non réconcilié; `PAY04` paid rapproché; `PAY05` facture/paiment annulé; `PAY06` double confirmation; `PAY07` justificatif sans paiement; `DEL01` URL rapport avant paiement; `DEL02` RPC direct; `DEL03` double délivrance/concurrence; `DEL04` réimpression autorisée; `SEC01` inter-centres; `SEC02` Régisseur ne valide pas acte; `SEC03` Agent ne confirme pas paiement; `SEC04` Admin trace action. Les fixtures sont temporaires avec rollback Odoo; aucune pièce de la base revue ne sera réutilisée.

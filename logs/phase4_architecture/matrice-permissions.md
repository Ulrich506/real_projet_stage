# Matrice des permissions cible

Cette matrice est une conception; elle ne décrit pas une configuration déjà installée. « Oui sous condition » suppose ACL/record rule, méthode serveur et état métier tous favorables. Masquer un bouton seul n’est jamais un contrôle.

| Fonctionnalité | Agent | Officier compétent | Régisseur | Administrateur État civil |
|---|---|---|---|---|
| Consulter acte / pièce | Oui, centre affecté | Oui, centre affecté | Non par défaut; métadonnées de demande seulement | Oui, tous centres |
| Ajouter/remplacer pièce | Oui en brouillon/retour correction, avant verrouillage légal | Oui uniquement acte assigné/en attente si règle validée; sinon lecture | Non | Oui sous règles d’audit/conservation |
| Passer pièce à `recu` | Oui (état actuel) | Non par défaut; selon responsabilité si politique approuvée | Non | Oui, transition tracée |
| Passer pièce à `verifie` | Non | Oui, officier assigné et acte en attente | Non | Oui, transition tracée |
| Rejeter pièce | Non (état absent actuellement) | Proposition : oui avec motif si état `rejected` approuvé | Non | Oui avec motif/audit si cette transition est approuvée |
| Valider l’acte | Non | Oui, officier compétent désigné | Non | Oui, explicitement contrôlé et tracé |
| Demander première copie | Oui, centre affecté et acte éligible | Oui, centre affecté et acte éligible | Non (séparation tâches) | Oui, tous centres |
| Demander copie supplémentaire | Oui, centre affecté; tarif calculé serveur | Oui, centre affecté; tarif calculé serveur | Peut initier workflow financier, mais ne crée pas la demande civile par défaut | Oui, tous centres |
| Modifier montant/tarif d’une demande | Non | Non | Non; tarif source readonly | Non après snapshot/facturation; paramètre tarif seulement selon rôle comptable/admin prévu |
| Consulter paiement/facture/reçu | Non, sauf statut minimal de sa demande | Non par défaut, sauf statut de demande | Oui, centres/sociétés autorisés et ACL Accounting | Oui, tous centres; informations Accounting uniquement si groupes de comptabilité explicitement attribués |
| Créer/poster facture | Non | Non | Selon ACL comptable assignée; la confirmation de paiement ne crée pas de facture cachée | Oui selon ACL comptable, avec audit |
| Enregistrer paiement comptable | Non | Non | Oui si `account` ACL le permet; par action standard Odoo | Oui selon ACL comptable; aucune écriture directe d’état |
| Confirmer encaissement pour délivrance | Non | Non | Oui, après vérification server-side de facture postée, rapprochée, payée en totalité | Oui, mêmes contrôles et traçabilité |
| Autoriser délivrance gratuite | Oui si politique l’autorise, et acte/entitlement validés | Oui dans son centre | Non | Oui, tous centres |
| Autoriser délivrance payante | Non avant état `payment_confirmed` | Non avant état `payment_confirmed` | Non; il confirme le paiement, sans délivrer | Oui seulement après contrôle de l’état Accounting |
| Délivrer/télécharger document final | Oui si autorisation existante et centre correct | Oui si autorisation existante et centre correct | Non | Oui si même condition serveur satisfaite, action journalisée |
| Consulter historique de délivrance | Oui sur ses centres/demandes | Oui sur ses centres | Oui sur périmètre financier; pas besoin de contenu civil complet | Oui global, append-only |
| Gérer tarif/configuration | Non | Non | Lecture; modification seulement si cumul de rôle comptable/config explicitement approuvé | Oui, changement versionné avec auteur/date et période d’effet |
| Accéder à tous les centres | Non | Non (centres affectés) | Non (centres/sociétés affectés) | Oui |
| Gérer utilisateurs et groupes | Non | Non | Non | Oui; pas de modification automatique de mot de passe hors procédure |
| Supprimer demande/pièce/facture | Non | Non | Non | Pas d’effacement d’historique délivré/comptabilisé; annulation/reversal tracé. Suppression brouillon seulement si règles légales le permettent. |

## Implémentation de sécurité proposée

### Groupes et ACL

- Réutiliser `etat_civil.group_etat_civil_agent`, `.officier`, `.admin`; ajouter `etat_civil_account.group_etat_civil_regisseur` au bridge seulement après confirmation.
- Le groupe Régisseur implique `base.group_user` et seulement les ACL nécessaires à la demande de copie, au reçu et aux informations comptables validées. Ne pas lui accorder `base.group_system`, `account.group_account_manager` ou unlink comptable par défaut. Pour enregistrer/valider un paiement au moyen des écrans Account standards, lui attribuer le groupe comptable minimum requis après vérification des groupes exacts de la configuration Odoo 17; le groupe applicatif Régisseur seul ne donne aucun droit sur `account.move`/`account.payment`.
- Configurer les permissions Accounting standard (par exemple rôle de facturation Odoo approprié) explicitement; la possession du groupe Régisseur n’est pas une permission comptable implicite.
- L’administrateur civil a les droits fonctionnels civils de demande/lecture/confirmation/délivrance demandés. La consultation ou l’action sur les factures/paiements standard dépend de groupes Accounting explicitement attribués; le groupe civil ne contourne pas les ACL/règles `account`. Chaque action administrative sensible reste auditée. La portée exacte du « tous droits fonctionnels » vs responsabilités comptables est [À CONFIRMER].

### Record rules

- Demandes de copie et pièces : domaine par `centre_id in user.etat_civil_centre_ids` pour Agent/Officier/Régisseur selon besoin de poste; Admin global.
- Actes : conserver les règles actuelles du modèle légal, jamais accorder un acte par le seul lien de facture.
- Tarifs : lecture aux rôles de demande et Régisseur; création/modification à Admin ou groupe comptable tarif dédié, filtres société/centre.
- `account.move`, `account.payment`, `account.move.line` : laisser les record rules Accounting standards faire le contrôle entreprise; le bridge filtre en plus par request autorisée, ne fait pas de `sudo()` pour élargir les résultats.
- Pièces jointes : `public=False`; lecture via `ir.attachment` et l’accès au record propriétaire. Toute URL image/PDF repasse les droits du parent.

### Méthodes Python et routes

Chaque méthode de changement d’état doit contrôler `check_access_rights`, `check_access_rule`, rôle, centre, état source/transition, relation de facture, société/devise, et verrou transactionnel avant écriture. `create` refait la validation d’acte, tarif et gratuité; `write` refuse état, montant, auteur/date et relations financiers édités par import/RPC; `unlink` est refusé après soumission/facture/délivrance. Le report final et toute route directe refont les mêmes contrôles avant de charger le QWeb ou les bytes.

Les transitions `confirm_payment` et `deliver` journalisent l’utilisateur, l’heure et l’origine; un double appel est sans effet financier et ne crée pas de doublon. Aucune route de consultation ne renvoie le contenu via `sudo()` sans contrôle préalable du propriétaire et du centre.

## Contrôle particulier Administrateur

Dans le CSV du checkout courant, la ligne Admin pour `etat.civil.piece.justificative` a `perm_unlink=1`; le modèle ne surcharge pas `unlink()`. Cela signifie que le code du checkout accorde la suppression ORM d’une pièce à l’Admin, malgré le risque de perte de justificatif. L’état réel de l’ACL installée en base n’a pas été relu (le CSV local est modifié et aucune mise à jour module n’a été lancée). Décision recommandée : préserver « tous les droits fonctionnels » par actions tracées, mais remplacer l’effacement après réception/validation par rejet, remplacement versionné ou archivage; ne pas modifier cette règle avant validation de conservation légale.

## Risques de cumul de rôles

- Un Administrateur qui confirme aussi un paiement peut réduire la séparation des tâches; au minimum chatter et pièce de rapprochement obligatoires, idéalement deuxième approbation au-dessus d’un seuil que le propriétaire définira.
- Un Régisseur doit voir suffisamment de données pour vérifier montant et bénéficiaire, sans recevoir automatiquement accès aux actes intégraux ou aux justificatifs d’identité.
- L’Officier ne doit ni confirmer un encaissement ni utiliser un statut paiement pour valider l’acte.
- Un administrateur Accounting standard n’est pas automatiquement un Administrateur civil; les deux ensembles de permissions doivent être explicitement reliés.

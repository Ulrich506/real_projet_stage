# Architecture actuelle — état civil et finance

**Base observée :** `etat_civil_final_review_20261105_1304`  
**Serveur :** HTTP `127.0.0.1:18071`, gevent `127.0.0.1:18072`  
**Date :** 2026-11-05 UTC  
**Périmètre :** code présent dans le checkout de travail, manifestes, historique de rapports et catalogue ORM lu en transaction `READ ONLY`.

## État d’intégrité du checkout

Le checkout est non propre : `git status --short --untracked-files=no` montrait déjà de nombreux fichiers modifiés sous `custom_addons/etat_civil`, `logs`, `odoo17.sh` et des suppressions dans `data/filestore`. Les références visibles sont `main` et `origin/main`. Faute de snapshot avant les travaux antérieurs, ce rapport décrit le contenu courant et ne peut pas attribuer les écarts à un commit. Rien n’a été restauré ou supprimé pour cet audit. Les livrables de cette phase sont ajoutés uniquement sous `logs/phase4_architecture/`.

## Module personnalisé

Le seul manifeste trouvé sous `custom_addons` est `custom_addons/etat_civil/__manifest__.py` (version déclarée 17.0.2.1.8). Ses dépendances sont `base`, `mail`, `web`. Il ne déclare aucune dépendance financière/POS.

Modèles principaux :

- `etat.civil.individu` : personne civile, distincte de `res.partner`.
- `etat.civil.centre`, `etat.civil.registre` : centres et registres.
- `etat.civil.acte.officiel` (AbstractModel), concrétisé par `etat.civil.acte.naissance`, `.mariage`, `.deces` : numéro, registre, feuillet, statut légal, agent transmetteur, officier responsable, dates, empreinte et QR.
- `etat.civil.mention.marginale` : mentions avec relations typées vers les actes concernés.
- `etat.civil.piece.justificative` : justificatifs reliés à exactement un acte ou une mention, Many2many vers `ir.attachment`.
- `etat.civil.demande.guichet` : tickets de file guichet, pas des demandes de délivrance financières.
- `etat.civil.exchange.log` et assistants Transmettre, Retour correction, Annulation, Gestion utilisateur, Import/Export.

## Workflows actuels

### Actes et pièces

L’acte suit les transitions métier de brouillon, transmission `en_attente`, correction/refus, validation, rectification, annulation et archivage. Les champs workflow protégés ne doivent passer que par les méthodes dédiées. Seul un officier compétent et affecté valide; l’administrateur métier est inclus explicitement dans certains contrôles.

La pièce possède seulement `a_fournir`, `recu`, `verifie`; elle trace `recu_par_id`, `date_reception`, `verifie_par_id`, `date_verification` et poste les transitions dans le chatter. Les pièces obligatoires doivent être `verifie` pour valider l’acte. Aucun statut `rejete` ou reçu financier n’existe.

### Demande guichet et copies

`etat.civil.demande.guichet` a `ticket_numero`, des champs nom/CIN, `type_acte`, `type_demande` (copie intégrale, extrait, déclaration immédiate), priorité et statuts `en_attente`, `en_cours`, `traite`, `annule`. Le modèle n’a pas de relation Many2one à un acte, partenaire, facture, paiement ou justificatif de paiement; pas de tarif, numéro de copie ou date/utilisateur de délivrance. Le changement de statut est contrôlé par action dédiée.

Il n’existe donc ni historique de premières copies, ni règle gratuite, ni demande de copie payante, ni paiement/régisseur, ni garde de téléchargement liée au paiement.

## Vues, rapports et pièces

- Menus : guichet; actes naissance/mariage/décès; mentions; citoyens/import/export; administration centres/registres/utilisateurs/journal d’échanges.
- Actes : vues liste, kanban, formulaire et recherche, workflow, onglets pièces, chatter.
- Formulaires des trois actes : widget personnalisé `etat_civil_piece_attachments` avec action « Consulter » via le FileViewer Odoo et action distincte « Télécharger ». Les mentions utilisent `many2many_binary` standard. Le code prouve la présence du composant, pas le parcours Chromium authentifié complet; formats, URL directes, grosse image et centre [PREUVE MANQUANTE].
- Rapports QWeb : naissance, mariage, décès, mention. Les rapports d’actes sont imprimables pour contrôle/signature physique, y compris avant validation, avec avertissement « non validé ». Ils ne sont pas des reçus de paiement ni un workflow de délivrance payante.
- Aucun tableau de bord de ventes actuel; les migrations 2.1.1/2.1.2 retirent l’ancien menu/action client.

## Sécurité présente et limites observées

- Groupes métier Agent, Officier, Administrateur d’état civil; le groupe Admin implique Agent, pas Officier. Les règles de centres filtrent actes, mentions et pièces; Admin reçoit des règles globales. Les méthodes vérifient rôle, centre, officier affecté et états.
- L’ACL CSV courant donne aux Agents/Officiers lecture/écriture/création sans unlink sur les pièces; la ligne Admin donne les quatre permissions, unlink inclus. Le modèle `piece_justificative.py` n’a pas de méthode `unlink()` dans le checkout courant. Les `ir.model.access` installés en base peuvent différer du CSV modifié, car aucune mise à jour du module n’a été faite pour cet audit.
- Les rapports ont des groupes `groups_id`; cela ne constitue pas une autorisation financière. Aucun mécanisme de copie payante n’existe à protéger.
- Preuve historique déjà documentée : le test automatisé sur la base revue a obtenu 200 à l’attachement inline pour un agent affecté et 404 pour un utilisateur d’un autre centre. Il s’agit d’une preuve HTTP automatisée limitée, non d’une validation visuelle Chromium ni de toutes les routes/formats. Aucun nouveau test Chromium authentifié n’a été exécuté dans cette phase.

## Addons standards Odoo 17 : disponibilité et installation

Les modèles ci-dessous sont définis dans le code Odoo 17 du checkout. Leur présence sur disque ne signifie pas qu’ils sont installés dans la base.

| Modèle | Addon propriétaire dans le checkout | Présent sur disque | État catalogue de la revue | Note |
|---|---|---:|---|---|
| `res.partner` | `base` (`odoo/odoo/addons/base/models/res_partner.py`) | Oui | `base=installed`; modèle enregistré | Compte client/facturation Odoo, distinct de `etat.civil.individu`. |
| `product.product` | `product` (`odoo/addons/product/models/product_product.py`) | Oui | `product=uninstalled`; modèle non enregistré | Variantes produit; requis par `account`, candidat pour le produit service « copie ». |
| `account.move` | `account` (`odoo/addons/account/models/account_move.py`) | Oui | `account=uninstalled`; modèle non enregistré | Factures, avoirs et autres pièces comptables. |
| `account.move.line` | `account` (`odoo/addons/account/models/account_move_line.py`) | Oui | `account=uninstalled`; modèle non enregistré | Lignes des écritures/factures, produit/taxe/compte. |
| `account.payment` | `account` (`odoo/addons/account/models/account_payment.py`) | Oui | `account=uninstalled`; modèle non enregistré | Paiement comptabilisé; rapproché avec les échéances de facture. |
| `pos.config` | `point_of_sale` | Oui | `point_of_sale=uninstalled` | Configuration d’une caisse POS. |
| `pos.session` | `point_of_sale` | Oui | `point_of_sale=uninstalled` | Session/caisse, ouverture et clôture. |
| `pos.order` | `point_of_sale` | Oui | `point_of_sale=uninstalled` | Commande/vente POS. |
| `pos.payment` | `point_of_sale` | Oui | `point_of_sale=uninstalled` | Moyen et montant de paiement POS. |

`account_payment` (addon Odoo en ligne dépendant de `account` et `payment`) est désinstallé. `account_accountant` est déclaré uninstallable dans cette base. `sale`, `sale_management`, `pos_restaurant` sont désinstallés. `account` standard dépend notamment de `product`; aucune de ces installations n’a été demandée ni réalisée.

## Conclusion

La base actuelle couvre les actes, les pièces, les rôles civils, les demandes guichet et les PDF d’actes. Elle n’a pas de comptabilité activée ni de processus de copies/délivrance. Le modèle `res.partner` existe, mais la personne civile et le client comptable ne sont pas reliés dans le modèle actuel. Architecture cible recommandée : addon passerelle séparé vers `account`, sans POS ni deuxième ledger par défaut.

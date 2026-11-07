# Architecture cible proposée

## Décision d’architecture proposée

Architecture A : laisser `etat_civil` propriétaire du workflow légal des actes, ajouter un module compagnon `etat_civil_account` (nom de travail) dépendant de `etat_civil` et du standard Odoo `account`. Ce bridge porte le dossier de copie, le calcul de gratuité/tarif, le rôle Régisseur et l’autorisation de délivrance. Il ne remplace ni `account.move`, ni `account.move.line`, ni `account.payment`, ni le rapprochement bancaire/comptable.

La base de revue n’a pas ces modèles enregistrés : `account`, `product`, `account_payment` et POS y sont désinstallés. Ils sont présents dans les sources Odoo 17 du checkout. Aucune installation ou mise à jour n’est faite par ce livrable.

## Frontières des responsabilités

### `etat_civil` existant

- Source d’autorité des actes, personnes civiles, centres/registres, pièces et statuts légaux.
- La validation d’acte reste indépendante d’une demande de copie ou d’un paiement.
- Les rapports physiques de validation/signature restent imprimables selon les règles légales courantes; ils ne sont pas le document de délivrance payante.

### `etat_civil_account` proposé

- Introduit `etat.civil.copy.request` et la configuration `etat.civil.copy.tariff`.
- Conserve des Many2one typées vers les trois modèles persistants concrets `etat.civil.acte.naissance`, `.mariage` et `.deces`; le socle `etat.civil.acte.officiel` est abstrait et n’est pas une cible FK valide. Une contrainte serveur/SQL impose exactement un lien concret. Le centre et l’individu sont dérivés du modèle concret/registre; l’acte doit être éligible et dans le périmètre utilisateur.
- Détermine « première » ou « supplémentaire » côté serveur à partir de l’historique des délivrances; le formulaire ne peut pas imposer le champ gratuit ou le montant.
- Pour une première copie admissible, autorise un montant nul calculé par la règle et inscrit cette délivrance dans l’historique. Aucun montant gratuit n’est sélectionnable par l’Agent.
- Pour une copie supplémentaire, choisit un tarif actif et valide à la date applicable; tarif absent ou ambigu bloque la création de la facture et signale l’erreur.
- Crée une facture Odoo client `account.move` avec un produit service configuré, le partenaire facturé, la société/journal et taxes validés. La valeur unitaire, devise, taxes et tarif appliqués sont figés dans la demande comme snapshot audit, jamais recalculés silencieusement après émission.
- Relie la demande à une seule facture source. L’état financier est lu depuis la facture comptabilisée et le rapprochement Odoo. Les paiements rapprochés ne sont pas copiés dans un registre custom.
- L’action Régisseur confirme seulement après vérification serveur de la facture client postée, du montant/devise attendus, du solde résiduel nul et de `account.move.payment_state == 'paid'` dans le code Odoo 17 du checkout. `not_paid`, `partial`, `in_payment`, facture annulée, remboursement/avoir non traité ou justificatif image seul ne suffisent pas. Dans Odoo, le paiement peut être comptabilisé et rapproché à la facture sans être encore rapproché à un relevé bancaire (`account.payment.is_matched`); ce dernier n’est requis que si la politique comptable de la commune le décide. Le Régisseur confirme la preuve d’encaissement à délivrance, pas un champ comptable.
- Trace l’utilisateur, l’heure, le montant, la facture et les paiements rapprochés associés dans chatter et un historique non éditable par l’Agent.
- Autorise la délivrance seulement après état de paiement conforme (ou gratuité validée) et transition d’autorisation. La même condition est revalidée dans chaque action PDF et route URL directe.

### Finance Odoo

- `res.partner` identifie le partenaire facturé; le modèle `etat.civil.individu` reste la personne civile. Ne pas assimiler automatiquement les deux identités ni fusionner des contacts sans règle métier.
- `product.product` représente la prestation facturée (produit service). Il est fourni par le module standard `product`, dépendance de `account`.
- `account.move` porte la facture/avoir et `account.move.line` les lignes et montants comptabilisés.
- `account.payment` porte le paiement comptable; sa relation aux factures vient de la réconciliation des lignes comptables. Le rapport de reçu standard ou un QWeb d’extension de `account.payment` produit le reçu imprimable.
- Distinctions d’état : facture `draft` = brouillon non comptabilisé; `posted` = facture comptabilisée, pas nécessairement réglée; `account.payment` créé/enregistré = paiement saisi; `account.payment.state == 'posted'` = écriture de paiement comptabilisée; rapprochement facture = lignes de créance rapprochées; `account.payment.is_matched` = rapprochement à un relevé bancaire, distinct du rapprochement facture. Pour l’éligibilité de base, facture `posted`, résiduel nul et `payment_state == 'paid'`, puis confirmation Régisseur séparée. Politique de rapprochement bancaire: [À CONFIRMER].
- Un justificatif numérisé est une pièce jointe privée du paiement. Son dépôt ne modifie jamais `payment_state` et ne vaut pas confirmation.
- `account_payment` n’est ajouté que si les providers/liens de paiement sont requis; POS est optionnel et exclu du premier lot.

## Modèles et flux logiques

1. `etat.civil.copy.request` référence par trois champs typés un acte naissance OU mariage OU décès (exactement un), un demandeur/facturé, un type de document, une catégorie première/supplémentaire calculée, le tarif et le snapshot financier, un lien facture facultatif (gratuit) ou obligatoire (payant), confirmation Régisseur, autorisation, numéro/date de copie et utilisateur de délivrance. Le modèle abstrait `etat.civil.acte.officiel` ne reçoit pas de FK.
2. `etat.civil.copy.tariff` définit produit, type de document/prestation, montant/devise, taxes, société, centre facultatif, périodes d’effet et activation. Les recouvrements de périodes ambiguës sont interdits.
3. Les transitions sont explicites et contrôlées par actions serveur. Les états d’actes (`brouillon`, `en_attente`, `valide`, etc.), pièces (`a_fournir`, `recu`, `verifie`), facture Odoo et demande de copie restent des axes distincts.
4. Une consultation d’un PDF de copie ne donne jamais accès au rapport de signature physique avant paiement. Un rapport distinct sur `etat.civil.copy.request` vérifie l’ACL, le record rule du centre, l’état autorisé, l’acte, l’authentification et le non-annulé à chaque appel.

## États cibles de demande de copie

Sélection initiale proposée : `draft`, `awaiting_payment`, `payment_confirmed`, `authorized`, `delivered`, `canceled`, `rejected`. Pour la demande gratuite, la transition `draft → authorized` est permise après contrôle de l’entitlement et de l’acte; elle ne passe pas par la facturation. Pour la demande payante : `draft → awaiting_payment → payment_confirmed → authorized → delivered`.

Ne pas stocker une deuxième valeur modifiable `paid` concurrente avec la facture. La transition `payment_confirmed` est l’événement de contrôle Régisseur, distinct du statut Odoo; avant la première délivrance, la route recontrôle le statut Odoo courant. Un remboursement ou une annulation avant délivrance invalide l’autorisation et bloque le rapport. Après délivrance, le PDF archivé reste reconsultable par utilisateurs autorisés via l’historique de délivrance; remboursement ultérieur crée un incident comptable/métier et ne supprime ni la trace ni la délivrance passée, sauf décision légale particulière [À CONFIRMER].

## Sécurité et surfaces d’accès

- Chaque méthode publique (RPC inclus) appelle `ensure_one`, contrôle les ACL/record rules, le rôle métier, le centre, l’état, la relation à l’acte, la société et l’état de facture/paiement.
- Pas de `sudo()` pour lire/délivrer un document au demandeur. Si une lecture privilégiée est techniquement requise dans un compute, limiter les champs et refaire un contrôle explicite du droit avant tout retour.
- La route/report de copie vérifie le droit à chaque requête; aucun `access_token` public ni URL permanente de pièce jointe. Utiliser un rapport non mis en cache (`attachment_use=False`) pour la copie, ou régénérer après contrôle plutôt que publier une pièce jointe stable.
- Les règles de copie limitent Agent/Officier aux centres affectés; Régisseur voit uniquement demandes financières de ses centres/sociétés assignés; administrateur civil a une vue globale, actions tracées. Les droits Accounting standards restent séparés et non élargis à tout Agent.
- Idempotence et verrous transactionnels empêchent doubles factures, confirmations et délivrances. Les états financiers ne sont jamais changés directement par l’état civil.

## Option POS

Ne pas inclure POS pour le premier lot. Si le paiement au guichet doit obligatoirement être une commande POS, ajouter plus tard `etat_civil_pos`, dépendant de la passerelle et de `point_of_sale`, liant une demande à un `pos.order` puis aux `pos.payment`. La validation devra vérifier commande payée et session caisse dans l’état autorisé; la clôture et le rapprochement restent Odoo POS/Accounting. La facture ne sera pas générée en parallèle si le POS a déjà produit l’écriture comptable.

## Dépendances proposées

```text
base + mail + web
       └── etat_civil (déjà présent)
             └── etat_civil_account (proposé; dépend de etat_civil + account)
                      ├── product (installé comme dépendance account)
                      ├── account_payment (optionnel, selon flux/provider effectivement requis)
                      └── etat_civil_pos (optionnel; seulement si POS est confirmé)
```

Aucune dépendance inversée de `etat_civil` vers `account` : le module légal civil reste installable sans Accounting.

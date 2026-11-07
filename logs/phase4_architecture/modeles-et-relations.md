# Modèles et relations proposés

Les modèles ci-dessous sont une conception, pas du code installé. Ils appartiennent au nouveau module `etat_civil_account` (nom de travail), sauf les modèles Odoo et État civil déjà existants. Les relations comptables doivent être des liens ORM et les paiements réels restent dans Accounting.

## 1. `etat.civil.copy.request`

Modèle principal de demande de copie/délivrance. `mail.thread` peut assurer le chatter, mais l’historique des transitions financières/délivrances doit être append-only et les champs d’audit readonly côté ORM.

| Champ proposé | Type | Règle |
|---|---|---|
| `name` | Char/sequence | Référence unique séquencée à la création. |
| `acte_type` | Selection | `naissance`, `mariage`, `deces`; déterminé côté serveur depuis le lien. |
| `acte_naissance_id`, `acte_mariage_id`, `acte_deces_id` | Many2one typés | Exactement un renseigné; vraies FKs vers les trois modèles persistants concrets. `etat.civil.acte.officiel` est un `AbstractModel`, donc ne peut pas être une cible Many2one. Ajouter une contrainte SQL robuste (somme des liens = 1) et revalider dans `create/write`. |
| `centre_id` | Many2one `etat.civil.centre`, related/store ou snapshot contrôlé | Calculé depuis le registre de l’acte; jamais choisi arbitrairement par l’utilisateur. Sert aux règles de centre. |
| `individu_id` | Many2one `etat.civil.individu`, related/computed | Sujet de l’acte, pas nécessairement demandeur ou payeur. |
| `requester_partner_id` | Many2one `res.partner` | Partenaire payeur/facturé; association à une personne civile seulement si le processus d’identité est explicitement défini. |
| `requester_name_snapshot` / référence externe | Char optionnels | À limiter; ne pas dupliquer plus de données personnelles que nécessaire. À décider si demandeur sans compte Odoo. |
| `document_type` | Selection/config relation | Copie intégrale/extrait/autre prestation autorisée; tarif résolu par configuration. |
| `copy_kind` | Selection readonly | `first` ou `additional`, calculé/confirmé transactionnellement; non éditable par UI/RPC. |
| `copy_number` | Integer readonly | Affecté au moment de délivrance sous verrou de l’acte; unique par acte. Ne pas consommer un numéro pour une demande rejetée/annulée. |
| `tariff_id` | Many2one `etat.civil.copy.tariff` | Requis pour une copie supplémentaire; absent/interrompu/ambigu bloque. Pour la première copie, gratuité est une règle d’entitlement, non un tarif nul caché. |
| `product_id` | Many2one `product.product`, snapshot | Produit service configuré sur le tarif; readonly après facture. |
| `amount_untaxed_snapshot`, `tax_amount_snapshot`, `amount_total_snapshot` | Monetary | Calculés côté serveur au moment de la demande/facture; monnaie liée par `currency_id`; pas d’entrée libre. Première copie admissible : montant calculé nul. |
| `currency_id` | Many2one `res.currency` | Copiée du tarif/société/facture, contrôlée contre la société. |
| `company_id` | Many2one `res.company` | Dérivée de la société comptable autorisée; `check_company=True` sur liens finance. |
| `invoice_id` | Many2one `account.move` | Une facture client postée, facture origine exclusivement cette demande; unique côté relation si le traitement reste unitaire. Pas de facture pour copie gratuite. |
| `payment_ids` | Many2many calculée/non stockée vers `account.payment` | Résolue depuis la réconciliation Odoo de l’invoice; pas une seconde source de vérité. N’expose que paiements auxquels l’utilisateur a accès. |
| `payment_state` | Champ calculé/related readonly ou méthode de contrôle | Dérivé de `account.move.state`, `payment_state` et `amount_residual`; aucun `write` direct. La confirmation exige facture client `posted`, `payment_state == 'paid'` et montant résiduel zéro, plus contrôles société/devise/partenaire. Odoo peut retourner `paid` lorsque le paiement est rapproché à la facture même si `account.payment.is_matched` (rapprochement bancaire) est faux; exiger ce dernier uniquement si D06 le confirme. |
| `payment_confirmed_by_id`, `payment_confirmed_at` | Many2one/Datetime readonly | Événement de confirmation Régisseur après contrôle financier réel; non substituable au statut Accounting. |
| `payment_evidence_attachment_ids` | Many2many vers `ir.attachment` ou pièces sur paiement | Facultatif, accès privé; image reçue seule ne vaut pas paiement confirmé. Recommandation : attacher le justificatif à l’objet paiement comptable. |
| `state` | Selection | `draft`, `awaiting_payment`, `payment_confirmed`, `authorized`, `delivered`, `canceled`, `rejected`; transitions par actions dédiées uniquement. |
| `authorized_by_id`, `authorized_at` | Many2one/Datetime readonly | Auteur/heure de l’autorisation de délivrer. Pour gratuit, autorisation après contrôle première copie; pour payant, après confirmation Régisseur. |
| `delivered_by_id`, `delivered_at` | Many2one/Datetime readonly | Auteur/heure de remise. Transition idempotente, verrouillée, non effaçable. |
| `delivery_reference` | Char optionnel | Trace d’impression/remise au guichet si nécessaire. Pas de stockage public du PDF. |
| `rejection_reason`, `cancel_reason` | Text | Obligatoires selon transition; chatter/événements gardent auteur et heure. |

Contraintes : exactement un acte; demande uniquement pour acte validé/rectifié et non archivé/annulé; unité monétaire/société cohérentes; une facture par demande payante; liens comptables non modifiables après émission; interdiction d’éditer montant, type gratuit/supplémentaire et état depuis RPC; demande d’acte sans permission centre rejetée.

## 2. Première copie et unicité concurrente

La première copie doit être déterminée par un historique serveur, non une case UI. Recommandation de règles techniques : verrouiller la ligne de l’acte (`SELECT ... FOR UPDATE` dans une courte transaction) dans l’action métier commune avant de décider l’éligibilité; recharger l’historique après verrou; réserver l’entitlement à la première demande en cours; libérer la réservation uniquement par transition autorisée annulée/rejetée si aucune délivrance n’a eu lieu; marquer définitivement l’entitlement à la délivrance. Numéro de copie et transition délivrée sont aussi sous verrou.

Pour une garantie inter-chemin et anti-course plus forte, ajouter un registre `etat.civil.copy.entitlement` avec un lien typé vers un seul acte et contrainte d’unicité par acte (une valeur non nulle parmi les trois relations), état de réservation et lien vers la demande/délivrance. Ne pas utiliser uniquement un champ `is_first_copy` posté par le client. La règle métier (par acte ou par personne/type) reste à approuver avant la contrainte.

## 3. `etat.civil.copy.tariff`

Configuration d’un tarif, pas facturation parallèle.

| Champ proposé | Type | Règle |
|---|---|---|
| `name`, `active` | Char/Boolean | Paramètre administrable, inactif par défaut si inachevé. |
| `service_code` / `document_type` | Selection/Many2one | Type exact de copie/prestation. |
| `product_id` | Many2one `product.product` | Produit service existant; son compte de revenu/taxes suivent la config Accounting. |
| `amount` / `currency_id` | Monetary | Aucun montant en dur; positif ou zéro explicitement configuré seulement si règle autorisée. |
| `tax_ids` | Many2many `account.tax` | Taxes applicables validées par société et pays. |
| `company_id` | Many2one `res.company` | Obligatoire si comptabilité multi-société; compatible avec le journal/facture. |
| `centre_id` | Many2one `etat.civil.centre`, optionnel | Surclasse le tarif société seulement si une tarification territoriale est décidée. |
| `date_start`, `date_end` | Date | Période inclusive; date de demande ou de facturation à fixer comme base d’application. |
| `sequence` | Integer | Départage non ambigu uniquement selon une règle explicite; sinon plusieurs tarifs actifs constituent une erreur bloquante. |
| `write_uid`, `write_date` / mail tracking | audit | Modification réservée Administrateur/Comptabilité, journalisée. Les tarifs historiques utilisés restent référencés et snapshottés. |

Il faut une contrainte de non-chevauchement pour le même `company_id + centre_id + service_code + document_type`; vérifier les tarifs côté serveur sous verrou avant création de facture. Les modifications futures n’altèrent pas les demandes déjà facturées.

## 4. Modèles standards liés

- `res.partner` (`base`) : client/payer de facture; ne pas remplacer `etat.civil.individu` automatiquement.
- `product.product` (`product`) : ligne de prestation; le module `account` le dépend.
- `account.move` (`account`) : facture client/avoir et états comptables. Lien Many2one depuis demande. La création de facture est idempotente et suit le workflow standard de comptabilisation.
- `account.move.line` (`account`) : ligne invoice, taxe, revenu, échéance et compte débiteur. Créé par Odoo à partir du produit et de la taxe configurés; jamais par SQL.
- `account.payment` (`account`) : modèle d’enregistrement comptable (dans Odoo 17 il délègue des champs à `account.move` via `_inherits`), référence de paiement, état d’écriture, `is_reconciled`, `is_matched` et `reconciled_invoice_ids`. `is_matched` signifie rapproché à relevé bancaire; ce n’est pas le même fait que la facture réglée. Source d’éligibilité: facture Odoo postée, résiduel nul et `payment_state == 'paid'`; vérifier aussi les paiements liés et avoirs/annulations. Le critère de rapprochement bancaire est [À CONFIRMER].
- `account.partial.reconcile` / lignes comptables : source de vérité technique du rapprochement, à lire via l’ORM Odoo, non à modifier directement depuis le bridge.
- `ir.attachment` : preuve jointe privée à une pièce ou au paiement; ne transforme pas l’état comptable.
- POS éventuel : `pos.order`, `pos.payment`, `pos.session`, `pos.config` ne sont utilisés que par un addon POS distinct si ce mode est approuvé. Ne pas créer ensuite une seconde facture comptable si le POS a déjà posté la vente.

## 5. Modèle de reçu

Ne pas créer un modèle custom de paiement/reçu qui concurrence `account.payment`. Le reçu de paiement est le rapport standard disponible dans la configuration cible ou un QWeb dérivé après confirmation, avec identifiant de paiement, journal, montant, partenaire, date et référence. Un reçu papier/attachement est une preuve matérielle, pas l’état comptable. Si une séquence légale distincte est obligatoire, l’extension doit la porter sur une extension auditée de paiement et journaliser émission/réimpression/annulation. La disponibilité et le contenu du reçu standard dans la base cible sont [PREUVE MANQUANTE].

## 6. Cardinalités

- Un acte → plusieurs demandes de copie/délivrance historiques.
- Une demande → zéro ou une facture `account.move` (zéro si gratuit); une facture liée à une seule demande dans le premier lot.
- Une facture → zéro à plusieurs paiements `account.payment` via rapprochement Odoo; les paiements partiels n’autorisent pas la délivrance.
- Une demande → au plus une délivrance finale.
- Un partenaire payeur (`res.partner`) peut être distinct du sujet civil (`etat.civil.individu`).
- Un tarif actif correspond à une combinaison période/société/centre/prestation non ambiguë.

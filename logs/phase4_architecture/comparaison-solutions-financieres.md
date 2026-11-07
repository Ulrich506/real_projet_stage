# Comparaison des solutions financières

## Constat préalable

Aucun addon financier personnalisé n’a été trouvé dans `custom_addons` ni dans les branches locales/distantes disponibles (`main`, `origin/main`). Le checkout contient les addons standard Odoo 17 `account`, `account_payment`, `product` et `point_of_sale`; dans la base de revue, `account`, `account_payment`, `product`, `sale` et POS ne sont pas installés. Le seul modèle standard parmi les candidats vérifié comme actif dans cette revue est `res.partner` fourni par `base`.

Les deux architectures ci-dessous sont donc des **options**, et non des systèmes en fonctionnement. La recommandation est A, sous réserve de l’approbation comptable/produit et de l’installation ultérieure dans une base isolée autorisée.

## Options

| Critère | A — Odoo `account` + passerelle légère | B — Finance métier personnalisé connecté à Accounting |
|---|---|---|
| Comptabilité source | `account.move`, `account.move.line`, `account.payment`, journaux, rapprochements et taxes standards Odoo. | Le module custom gère son workflow métier, mais doit poster/relier chaque opération à `account`; `account` reste le ledger comptable obligatoire. |
| Sécurité | ACL/groupes Odoo, sociétés, journaux, règles standard et groupe Régisseur spécialisé, avec vérification côté serveur dans les actions de copie. | Deux surfaces de sécurité : ACL custom en plus des droits comptables; risque accru de divergence de permissions et d’élévation. |
| Maintenance | Faible à moyenne : config comptable Odoo + un addon d’intégration et tests de compatibilité Odoo 17. | Élevée : modèles, vues, migrations, rapports, journaux, rapprochements, annulations, arrondis et états propres à maintenir en parallèle. |
| Complexité | Facture client une-à-une par demande (recommandation initiale), paiements rapprochés standard; workflow civil conservé séparément. | Forte : synchronisation à double sens, idempotence, remboursements, paiements partiels, écritures, période clôturée et reprise après incident. |
| Dépendances | L’addon d’intégration dépend de `etat_civil` et `account`; `account` installe ses dépendances dont `product`. `account_payment` seulement si paiement portail/providers est requis. | Module métier dépend toujours d’`account` pour éviter une comptabilité parallèle; dépendances custom supplémentaires non présentes aujourd’hui. |
| Cohérence comptable | Élevée si paiement confirmé uniquement par rapprochement complet de facture postée et que l’extension ne modifie jamais manuellement les états comptables. | Moyenne à faible sans audits et réconciliation robustes; possibilité de dédoublement du montant, reçu ou état. |
| Évolutivité | Compatible avec taxes, devises, avoirs, journalisation et évolutions standards; possibilité d’un bridge POS séparé ultérieurement. | Peut satisfaire une procédure locale spécifique, mais augmente le coût des changements de version et le risque de dette technique. |
| Doublons | Faibles si un `account.move` source par demande et aucune table `payment`/`receipt` custom; référence civile stockée dans l’origine et le lien ORM. | Élevés si facture, paiement, statut ou séquence de reçu sont répliqués dans un registre autonome. |
| Reçus | Rapport de reçu standard de paiement ou rapport dérivé de `account.payment`; justificatif de paiement conservé en attachement privé au paiement, si besoin. | Doit gérer la numérotation, duplication, annulation, réimpression et rapprochement du reçu avec l’écriture; même si la couche custom est connectée à `account`. |
| Régisseur | Petit groupe custom dans le bridge; action d’encaissement/confirmation vérifie la facture réelle et garde les permissions accounting minimales. | Rôle custom complet; il faut éviter qu’il puisse éditer des écritures sans rôle comptable distinct. |
| POS | Non requis pour la délivrance comptable de copies. Ajout éventuel par addon distinct `etat_civil_pos` si session/caisse est une exigence validée. | Le module custom pourrait piloter le workflow POS, mais le modèle POS standard reste la source de commande et paiements; ne pas réimplémenter une caisse. |
| Compatibilité Odoo 17 | Bonne : les modèles demandés existent dans Odoo 17 du dépôt; l’intégration doit cibler les champs/méthodes de cette version et être couverte de tests. | Possible, mais chaque modèle custom suit les changements d’API comptable 17 et exige migrations propres. |

## Recommandation

Choisir A : un addon compagnon proposé `etat_civil_account` qui dépend de `etat_civil` et du module `account`. Il contient le modèle de demande de copie, le tarif lié à un produit service et le rôle Régisseur, mais ne crée **aucun** journal de paiement, grand livre, facture ou table miroir de paiement. `account.move` et les rapprochements Odoo déterminent l’état financier; `account.payment` est lié via la réconciliation Odoo. Le code d’état civil conserve les règles de gratuité/délivrance, indépendantes des états d’acte et de pièce.

`account_payment` n’est pas nécessaire par défaut pour les encaissements manuels en caisse; son utilité dépend de la demande de paiement en ligne/provider. `point_of_sale` n’est pas nécessaire si le Régisseur enregistre un paiement comptable via le journal standard. Si une vraie caisse POS est exigée, développer ultérieurement un addon optionnel `etat_civil_pos` qui référence `pos.order`/`pos.payment` et garde `account` comme comptabilité source.

L’option B n’est pertinente que si le propriétaire fournit des règles métier financières absentes du standard et une équipe responsable de les maintenir. Même dans B, toutes les opérations doivent poster/rapprocher dans `account`; un ledger custom autonome est exclu.

## Scénarios d’encaissement pour la commune

| Critère | 1 — Régisseur via Accounting (recommandé au premier lot) | 2 — Régisseur via POS connecté à Accounting |
|---|---|---|
| Parcours | Facture de la demande → paiement manuel dans journal caisse/banque → rapprochement à facture → confirmation Régisseur. | Session POS → commande/prestation et paiement POS → clôture/validation → écriture reliée → demande autorisée. |
| Simplicité | Moins de modèles/workflows; facture, état de paiement et rapprochement natifs. | Interface caisse pratique, mais ajoute `pos.config/session/order/payment`, caissier, ouverture/clôture, retours et mapping demande/vente. |
| Fiabilité | Bonne si config Account et rapprochements corrects; une facture par demande. | Bonne si la commune exploite déjà POS et clôture correctement; ne pas créer une facture parallèle pour la même vente. |
| Sécurité | Groupe comptable minimum + Régisseur, surface spécifique plus faible. | Ajouter permissions POS/session/caissier et vérifier qu’une commande source correspond à la demande et à l’écriture. |
| État dans la revue | `account` non installé en base; à préparer en DB de test. | POS et Account non installés; aucun parcours observé. |
| Décision | Recommandé si paiements au guichet et besoin d’une facture par copie. | À retenir seulement si la commune exige une caisse POS ou l’utilise déjà comme source d’encaissement. |

Sans besoin POS confirmé, le scénario 1 est le plus simple et réduit les doublons de commande/facture. Décision finale [À CONFIRMER] par Régisseur/comptabilité. Aucun second système d’encaissement.

## Critères de confirmation avant tout développement

- Confirmer qu’`account` standard est la cible comptable et déterminer la configuration MGA/société/journaux/taxes avant d’installer le module.
- Indiquer si les paiements sont en espèces, virement, POS ou en ligne; cela détermine la nécessité d’`account_payment` et/ou d’un bridge POS.
- Définir quel utilisateur peut enregistrer un paiement et quel rôle en confirme la preuve, avec séparation des tâches souhaitée.
- Valider le tarif, sa date d’effet, le centre et les taxes. Aucun montant n’est codé par défaut.
- Définir la règle « première copie » avant d’utiliser une contrainte unique.

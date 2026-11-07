# Cahier des charges technique et fonctionnel — copies d’actes et intégration financière

**Version de conception :** 1.0 — 2026-11-05  
**Statut global : B — PARTIELLEMENT VALIDÉ**  
**Nature :** spécification cible; aucun code ni fonctionnalité financière décrits ici ne sont présentés comme implémentés.

## 1. Présentation et états de connaissance

Le projet `etat_civil` gère les personnes civiles, actes, justificatifs, mentions, demandes de guichet et rapports d’actes. Il faut couvrir une demande de copie et son historique, avec gratuité de première copie proposée, tarification des copies suivantes, comptabilisation via Odoo Accounting, vérification par un Régisseur et blocage sécurisé du document jusqu’à autorisation.

Etiquettes utilisées :

- **EXISTANT ET VÉRIFIÉ** : constaté dans les sources ou catalogue de la base.
- **EXISTANT MAIS NON TESTÉ** : code/vue présent, comportement non confirmé en parcours réel.
- **ABSENT / NON IMPLÉMENTÉE** : non trouvé dans l’architecture auditée.
- **PROPOSÉ** : conception future, non installée.
- **À CONFIRMER** : décision métier, comptable ou juridique requise.
- **[PREUVE MANQUANTE]** : aucun test approprié ne permet de conclure.

## 2. Périmètre et exigences

### Exigences fonctionnelles

| ID | Exigence | État / acceptation |
|---|---|---|
| REQ-001 | Conserver la gestion actuelle des personnes, actes naissance/mariage/décès, centres, registres, pièces, mentions et workflows légaux. | EXISTANT ET VÉRIFIÉ dans les sources; comportements authentifiés complets restent à tester. |
| REQ-002 | Créer une demande de copie liée à un acte concret et un demandeur/facturé identifié. | PROPOSÉ; demande guichet actuelle non reliée à un acte. |
| REQ-003 | Déterminer la gratuité côté serveur depuis l’historique des délivrances; aucune donnée UI/RPC ne fixe le droit. | PROPOSÉ; règle précise À CONFIRMER. |
| REQ-004 | Pour une copie payante, choisir un tarif actif unique, avec société/centre/date/type; bloquer si tarif absent ou ambigu. | PROPOSÉ; aucun tarif actuel; montant À CONFIRMER. |
| REQ-005 | Créer/associer une facture client standard `account.move`, avec lignes/taxes standard `account.move.line`; idempotence d’une facture par demande au premier lot. | PROPOSÉ; `account` et `product` sont désinstallés dans la base de revue. |
| REQ-006 | Lire les paiements standard `account.payment` à travers les relations de rapprochement; ne pas créer de modèle miroir. | PROPOSÉ; aucun paiement de copie actuel. |
| REQ-007 | Séparer l’écriture de facture, enregistrement/comptabilisation paiement, rapprochement facture, rapprochement bancaire et confirmation de délivrance. | PROPOSÉ; définition ci-après. |
| REQ-008 | Un Régisseur autorisé confirme la satisfaction des conditions avant délivrance; toute confirmation est historisée. | PROPOSÉ; rôle réel et procédure À CONFIRMER. |
| REQ-009 | Délivrer une seule fois chaque demande, conserver numéro/date/utilisateur et interdire les doubles gratuités concurrentes. | PROPOSÉ; historique actuel absent. |
| REQ-010 | Générer un document de copie distinct des rapports d’acte pour contrôle/signature. | PROPOSÉ; rapports actuels ne sont pas une fonction de copie payante. |
| REQ-011 | Distinguer consultation inline et téléchargement volontaire des justificatifs; images/PDF privés sous contrôle serveur. | Widget/visionneuse EXISTANT MAIS NON TESTÉ authentifié intégralement; parcours de téléchargement distinct présent dans le code. |
| REQ-012 | Tableau civil de volume/statuts et tableau financier alimenté par données Accounting réelles. | ABSENT / NON IMPLÉMENTÉE dans base revue. |
| REQ-013 | POS peut encaisser si requis, sans double facture ni ledger parallèle. | OPTION PROPOSÉE; POS désinstallé, besoin À CONFIRMER. |
| REQ-014 | Reçu comptable lié au paiement Odoo et reçu légal tracé si la réglementation en impose un distinct. | PROPOSÉ; contenu/numérotation À CONFIRMER. |

### Exigences de sécurité

| ID | Exigence | Règle d’acceptation |
|---|---|---|
| SEC-001 | Appliquer ACL, record rules et contrôle des méthodes Python aux actions sensibles. | Aucun accès permis uniquement parce qu’un bouton est visible. |
| SEC-002 | Appliquer la restriction de centre aux demandes, actes et pièces, y compris URL directe, RPC et rapport. | Utilisateur d’un autre centre reçoit refus/absence d’objet sans fuite de données. |
| SEC-003 | Ne jamais exposer copie payante avant autorisation et paiement courant conforme. | Le contrôle est répété à chaque rendu/route/téléchargement; pas de token public/caching contournant. |
| SEC-004 | Refuser le marquage de statut financier depuis `write`, import ou RPC. | Seul Accounting pilote états comptables; actions civiles enregistrent seulement événements métier permis. |
| SEC-005 | Empêcher double gratuité, facture, confirmation et délivrance par idempotence/contraintes/verrou. | Tests concurrents et répétitions passent. |
| SEC-006 | Limiter lecture de pièce jointe à l’accès au propriétaire et au centre. | `/web/image`, `/web/content`, endpoints viewer et téléchargements testés authentifiés. |
| SEC-007 | Préserver l’audit des actes, pièces, paiements, corrections et suppressions. | Aucun effacement silencieux après réception/validation/comptabilisation/délivrance. |
| SEC-008 | Régisseur ne valide pas un acte; Officier ne confirme pas un paiement; Agent ne vérifie pas officiellement une pièce. | Appels serveur directs refusés selon rôle. |
| SEC-009 | Administrateur civil dispose des fonctions civiles globales, avec événements auditables. | Les droits Accounting restent issus des groupes comptables attribués, pas d’un contournement du modèle. Portée fonctionnelle finale À CONFIRMER. |

## 3. Fonctionnalités actuelles, absentes et proposées

| Domaine | Constat |
|---|---|
| Actes, citoyens, centres, registres, mentions | EXISTANT ET VÉRIFIÉ dans les sources du checkout. |
| Pièces et états `a_fournir`, `recu`, `verifie` | EXISTANT ET VÉRIFIÉ dans le code. L’Agent reçoit, l’Officier vérifie selon les méthodes; pas de statut rejeté trouvé. |
| Visionneuse intégré / bouton consulter et télécharger | EXISTANT dans le code; comportement authentifié multi-format et multi-centre [PREUVE MANQUANTE]. |
| Demande guichet | EXISTANT mais ne porte pas lien à l’acte, facture, paiement, tarif ou délivrance. Ne pas la traiter comme une demande financière. |
| Accounting (`account.move`, `account.move.line`, `account.payment`) | Modèles présents dans sources Odoo; addon `account` non installé dans base de revue, donc non enregistré à l’instant du contrôle. |
| `product.product`, POS (`pos.config`, `pos.session`, `pos.order`, `pos.payment`) | Addons disponibles sur disque mais non installés dans base revue. |
| Module custom financier/Régisseur, demande de copie, tarif, reçus métier et tableaux de bord ventes | ABSENT / NON IMPLÉMENTÉE dans le checkout examiné. |
| PDF d’actes | Rapports QWeb existants; ils ne sont pas une barrière de paiement et peuvent servir au flux papier légal/validation. |

## 4. Architecture retenue et dépendances

Recommandation : module compagnon proposé `etat_civil_account`, dépendant de `etat_civil` et `account`. `etat_civil` conserve les règles légales et actes; `account` garde factures, lignes, paiements, rapprochements, journaux et états comptables; le bridge ajoute le lien demande ↔ facture, tarif, confirmation Régisseur et autorisation de copie. Aucun ledger, facture, paiement ou reçu miroir.

Odoo 17 dans le checkout fournit les modèles annoncés. `res.partner` appartient à `base`; `product.product` à `product`; `account.move`, `account.move.line`, `account.payment` à `account`. POS n’entre que dans un addon optionnel ultérieur. Installation de ces modules dans la base de revue interdite durant cette phase.

## 5. Modèles et relations proposés

- `etat.civil.copy.request`: demande, un lien typé vers acte naissance/mariage/décès (exactement un), centre dérivé, sujet civil, demandeur/partenaire facturé, type de document, classification gratuite/supplémentaire calculée, snapshots de montant/devise/taxe, état, facture, confirmation, autorisation et remise.
- `etat.civil.copy.tariff`: produit de service, montant/devise/taxes, société, centre optionnel, période d’effet, activité; aucun montant par défaut.
- `etat.civil.copy.delivery` ou événement append-only équivalent: une seule délivrance rattachée à la demande, numéro/date/utilisateur/référence.
- `account.move`: facture client / avoir standard; `account.move.line`: lignes et comptes; `account.payment`: paiement standard dont les lignes se rapprochent de la facture. `res.partner` est facturé; `etat.civil.individu` reste personne civile séparée.
- L’historique métier est immuable fonctionnellement et audit append-only; les comptabilités ne sont ni supprimées ni corrigées par SQL.

`etat.civil.acte.officiel` est abstrait et ne peut pas être la cible d’une FK; trois Many2one concrets sont recommandés avec contrainte exactement un. Toute source de polymorphisme non référentielle est exclue pour l’intégrité.

## 6. Statuts financiers et condition serveur

1. **Facture brouillon (`account.move.state == 'draft'`)** : non comptabilisée; aucune délivrance.
2. **Facture confirmée/comptabilisée (`state == 'posted'`)** : écriture officielle enregistrée, mais potentiellement impayée/partielle.
3. **Paiement saisi** : enregistrement créé; ne prouve pas un paiement comptabilisé ou affecté à cette facture.
4. **Paiement comptabilisé** : écriture du paiement postée (Odoo `account.payment` délègue à son écriture `account.move`; examiner `state`). Cela ne signifie pas forcément que la facture est soldée.
5. **Rapprochement à la facture** : lignes de créance rapprochées; état calculé de la facture indique solde et relation aux paiements.
6. **Rapprochement bancaire** : `account.payment.is_matched` en Odoo 17 signale rapprochement à un relevé bancaire; distinct du rapprochement avec la facture.
7. **Paiement confirmé pour délivrance** : événement applicatif immuable du Régisseur après contrôle; ce n’est pas un état comptable natif.

Condition technique minimale proposée pour le flux manuel standard avant première délivrance : facture client liée à la demande et `posted`, partenaire/société/devise/montant cohérents, `amount_residual` nul (avec précision monétaire), `payment_state == 'paid'`, paiement(s) comptabilisé(s) rapproché(s), aucun remboursement/avoir/annulation rendant le paiement insuffisant, Régisseur autorisé. Le Régisseur atteste l’encaissement selon procédure locale; exiger `is_matched` à un relevé bancaire est [À CONFIRMER]. Aucun justificatif seul, `in_payment`, `partial`, simple écriture brouillon ou booléen manuel ne suffit. Après délivrance, le document archivé demeure reconsultable sous contrôle d’accès et preuve de remise; un remboursement ultérieur crée un incident sans effacer l’événement historique, sous réserve de règle légale [À CONFIRMER].

## 7. Workflows

### WF-001 — première copie proposée

Demande → contrôle acte validé/rectifié et centre → verrouillage et lecture historique → détermination serveur de l’entitlement → autorisation gratuite → délivrance unique → archivage/journal. Une demande abandonnée/annulée sans délivrance peut libérer l’entitlement selon règle à confirmer. Le droit exact « une première copie gratuite par acte » est une proposition de politique communale, sans preuve juridique fournie.

### WF-002 — copie payante

Demande → détermination supplémentaire → tarif actif unique → snapshot tarif → facture client Odoo → paiement standard → contrôle comptable et confirmation Régisseur → autorisation → délivrance unique → document protégé → archivage/journal. Paiement partiel, tarif absent, facture annulée ou remboursement bloque. La facture/écriture n’est pas supprimée; avoir/remboursement via Account.

### WF-003 — justificatifs

Agent ajoute/remplace selon état autorisé, consulte et marque réception `À fournir` → `Reçu`; Officier affecté ouvre, vérifie et marque `Reçu` → `Reçu et vérifié`; chaque transition journalise acteur/date/motif. Administrateur peut effectuer transitions fonctionnelles permises sous audit. Refus n’est pas un état existant; à confirmer avant ajout.

## 8. Matrice fonctionnelle synthétique

| Action | Agent | Officier | Régisseur | Administrateur civil |
|---|---|---|---|---|
| Créer demande de copie | Oui centre autorisé | Oui centre autorisé si politique approuvée | Non par défaut | Oui tous centres |
| Consulter actes/pièces | Oui centre | Oui centre/affectation | Métadonnées financières minimales | Tous centres |
| Réceptionner pièce | Oui | Selon règle validée | Non | Oui, tracé |
| Vérifier pièce | Non | Oui si assigné | Non | Oui, tracé |
| Valider acte | Non | Oui compétence | Non | Oui, tracé |
| Modifier tarif | Non | Non | Non par défaut; futur droit dédié éventuel | Oui avec version et audit |
| Lire facture/paiement complet | Non | Non par défaut | Oui dans périmètre et groupes comptables requis | Oui si ACL Accounting explicitement assignées |
| Confirmer paiement délivrable | Non | Non | Oui après condition serveur | Oui après mêmes contrôles et trace |
| Délivrer document | Selon autorisation centre/état | Selon autorisation centre/état | Non | Oui, après mêmes contrôles |
| Gérer utilisateurs | Non | Non | Non | Oui |

Groupes Odoo (`res.groups`) identifient fonctions, ACL autorisent opérations modèle globalement, record rules réduisent enregistrements par centre/société, méthodes Python valident la transition concrète. Vues/boutons sont ergonomiques seulement. Le groupe Régisseur ne confère pas automatiquement des droits `account`; l’Admin civil reçoit les groupes comptables nécessaires explicitement.

## 9. Justificatifs et expérience visuelle

Exigences: « Consulter » ouvre une visionneuse inline et « Télécharger » démarre volontairement le téléchargement; contrôle de parent/centre à chaque action et réponse. Images JPG/JPEG/PNG peuvent être affichées en navigateur selon navigateur/MIME; PDF via viewer intégré navigateur/OWL avec limites d’impression et pièces volumineuses. SVG/HTML et formats actifs nécessitent refus ou assainissement explicite; type MIME fourni par client ne suffit pas. Limiter taille et types par liste serveur, sans rendre `ir.attachment` public. Prévisualisation navigateur ne garantit pas l’affichage de tout format. [PREUVE MANQUANTE] pour sessions Chromium authentifiées et tests de chaque format.

## 10. Journalisation

Chaque action significative journalise modèle/référence, état précédent/nouveau, acteur, date serveur, centre/société, motif lorsque requis, facture/paiements et identifiant de délivrance. Les consultations/téléchargements sensibles sont journalisés selon politique de conservation sans enregistrer contenu, secret, URL tokenisée ni données inutiles. Chatter seul n’est pas une preuve d’immutabilité; droits de modification et événements structurés à définir. `ir.logging`/journaux techniques ne remplacent pas l’historique métier durable.

## 11. Tableaux de bord

### État civil (non comptable)

Volumes d’actes par type; demandes par état; premières copies gratuites; demandes payantes; copies délivrées; demandes bloquées; répartition centre/période; historique de délivrance. Les agrégats suivent les record rules et n’exposent pas de dossiers civils hors périmètre.

### Régisseur (source Accounting)

Encaissements journaliers/période; factures en attente; paiements rapprochés à vérifier; confirmations; demandes bloquées; copies autorisées; reçus émis; historique par agent/régisseur/journal. Les montants sont agrégés depuis factures/paiements Account accessibles et rapprochés, jamais recalculés dans une comptabilité custom. Indiquer devise et période; séparer comptabilisé, rapproché facture et rapproché banque.

## 12. Traçabilité besoin → implémentation → test

| Besoin | Exigence | Workflow | Modèle | Méthode/action cible | Vue/route | Test |
|---|---|---|---|---|---|---|
| Première copie unique | REQ-003, SEC-005 | WF-001 | `copy.request`, `copy.delivery` | `action_request`, `action_authorize`, `action_deliver` transactionnelles | Formulaire demande, rapport protégé | TEST-001, TEST-003, TEST-009, TEST-024/025 |
| Facturation supplémentaire | REQ-004/005 | WF-002 | `copy.tariff`, `copy.request`, `account.move` | résolution tarif, création facture idempotente | Tarif et demande | TEST-002, TEST-004, TEST-005 |
| Encaissement | REQ-006/007/008 | WF-002 | `account.payment` + demande | contrôle serveur `action_confirm_payment` | Espace Régisseur | TEST-006 à 008, TEST-015 |
| Livraison sûre | REQ-009/010 | WF-001/002 | demande + délivrance | `action_deliver`, report/contrôleur | action impression privée | TEST-009, TEST-024/025 |
| Pièce privée | REQ-011, SEC-002/006 | WF-003 | `piece.justificative`, `ir.attachment` | réception/vérification, accès record sécurisé | widget, viewer, download | TEST-017 à 023 |
| Droits et audit | SEC-001/007/008/009 | tous | groupes, ACL, règles, événement | transitions serveur + méthodes report | menus/actions contrôlés | TEST-013/014/015/016/024/025 |

Les noms de méthodes et vues ci-dessus sont des propositions, pas des symboles existants.

## 13. Critères globaux d’acceptation

- Aucun droit gratuit ne peut être accordé deux fois, y compris par requêtes concurrentes.
- Aucune copie payante ne peut être délivrée par UI, URL, RPC, report ou accès pièce jointe avant paiement courant conforme et validation Régisseur.
- Facture/paiement/reçu proviennent d’Account; aucun doublon comptable ni état payé manuel.
- Annulations/remboursements utilisent avoirs/contre-écritures et laissent une piste complète.
- Rôles et centres sont vérifiés côté serveur; parcours authentifiés Chromium, RPC/HTTP et ORM ont preuves reproductibles.
- Actions de pièces respectent Agent/Reçu, Officier/Vérifié et audit; consultation et téléchargement sont distincts.
- Les 25 tests du document `specifications-tests-acceptation.md` passent en base de test dédiée synthétique.
- Métriques financières concordent avec vues/listes Accounting et rapprochements sur jeu de test.

## 14. Dépendances et limites

- `etat_civil` actuel : dépend de `base`, `mail`, `web`.
- Bridge proposé : `etat_civil` + `account`; `account` inclut `product` et ses dépendances.
- `account_payment` selon paiements en ligne/providers; POS uniquement si décision d’encaissement par caisse POS.
- Aucun module ne peut être déclaré installé ici; la revue n’a pas installé Accounting/POS.
- Règle de gratuité, montant, taxes, commune/société, reçu légal, statut de remboursement, utilisateurs de test, seuils de séparation tâches et conservation sont [À CONFIRMER].
- Résultat de visualisation authentifiée complète [PREUVE MANQUANTE]. Aucun rapport ne prétend cette validation.

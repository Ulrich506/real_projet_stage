# Rapport — Phase 4, architecture financière et délivrance de copies

**Projet :** `/home/ulrich/tous_les_projet/stage_l3_odoo/`  
**Base de revue examinée :** `etat_civil_final_review_20261105_1304`  
**Instance de contrôle :** `http://127.0.0.1:18071` ; gevent `127.0.0.1:18072`  
**Date :** 5 novembre 2026  
**Conclusion globale : B — Partiellement validé.** Cette phase produit une architecture proposée. Elle ne constitue ni une intégration implémentée ni une validation fonctionnelle des paiements.

## 1. Résumé exécutif

Le module `etat_civil` existant couvre les personnes, les actes, les pièces justificatives, les mentions, les demandes guichet, les rapports d’actes et les workflows de validation. Il ne possède pas de modèle de demande de copie, d’historique de délivrance, de tarif, de paiement, de reçu financier ou de rôle Régisseur identifié. Le ticket guichet ne constitue pas une demande de paiement.

La base de revue a `base`, `mail`, `web` et `etat_civil` installés. Les modèles standard `res.partner`, `product.product`, `account.move`, `account.move.line`, `account.payment` et les modèles POS ne sont pas tous disponibles dans son registre : `res.partner` est présent via `base`, tandis que `product`, `account`, `account_payment` et `point_of_sale` sont désinstallés. Aucun module financier personnalisé n’a été trouvé sous `custom_addons` ou dans les branches locales examinées.

**Recommandation :** une passerelle séparée `custom_addons/etat_civil_account` dépendant de `etat_civil` et de `account`, qui réutilise la comptabilité standard et ne crée ni deuxième grand livre ni modèles parallèles de paiement/reçu. POS reste facultatif et hors premier lot. Cette recommandation n’installe aucun module et ne modifie pas les sources.

La conception précise deux points Odoo 17 : `etat.civil.acte.officiel` est abstrait et ne peut pas être la cible d’une FK; la demande doit référencer l’un des trois modèles d’actes concrets par Many2one typé avec contrainte exactement-un. `account.payment.is_matched` signifie rapprochement bancaire, distinct du rapprochement/règlement de facture. La condition minimale proposée requiert facture postée, résiduel nul et `payment_state == 'paid'`; exiger aussi le rapprochement bancaire est [À CONFIRMER].

## 2. Portée et méthode

Audit statique des modèles Python, des vues XML, des groupes/ACL, des rapports QWeb, du manifeste et des modules Odoo présents dans le checkout. État d’installation vérifié en lecture seule dans la base de revue. La transaction d’inspection a été annulée sans écriture. État HTTP du serveur contrôlé par requête de lecture; aucun redémarrage ni changement de port.

L’analyse décrit le checkout de travail, qui était déjà non propre. Aucun état antérieur complet n’est disponible pour attribuer toutes les modifications suivies à cette phase; la phase n’a édité que sa documentation sous `logs/phase4_architecture/`.

Pas d’installation de module, d’écriture ORM/SQL persistante, de facture, paiement, reçu, acte ou donnée test créé. Pas de test navigateur authentifié ni de parcours financier exécuté. Pas de génération de nouveaux PDF métier.

## 3. État de l’instance et de la base

| Contrôle | Résultat | Statut |
|---|---|---|
| Service isolé | Actif au contrôle | VALIDÉ |
| HTTP 18071 `/web/login` | Réponse HTTP 200 | VALIDÉ |
| gevent 18072 | Port en écoute au contrôle | VALIDÉ |
| Base sélectionnée | `etat_civil_final_review_20261105_1304` | VALIDÉ |
| Tâches cron | L’état antérieur signalait cron désactivés; non modifié ici | PARTIEL |
| Service actif 8071 / instance 18205 | Non redémarrés ni touchés | VALIDÉ |
| Filestore | Aucun accès/écriture pendant cette phase; correspondance non réauditée ici | NON TESTÉ |

## 4. Architecture actuelle et modules

- Actes d’état civil et workflows de brouillon, transmission, correction, validation, rectification, annulation et archivage.
- Pièces liées aux actes avec états `a_fournir`, `recu`, `verifie`, date/utilisateur d’audit et chatter; pas de statut financier.
- Demande guichet avec types de demande et états de file; pas de relation ORM constatée vers une facture, un paiement, un acte ou une délivrance.
- Rapports d’actes principaux et de mentions marginales; ils ne doivent pas être considérés comme des copies payantes protégées.
- Groupes Agent, Officier et Administrateur. Aucun rôle Régisseur identifié.
- Le manifeste `etat_civil` dépend de `base`, `mail`, `web`, sans dépendance à `account`.
- Le checkout courant de l’ACL des pièces permet `unlink` au groupe Admin (`1,1,1,1`); le registre runtime n’a pas été contrôlé pour cette ACL précise. Revoir la conservation des preuves avant d’accorder/retirer ce droit.

Voir [architecture-actuelle.md](architecture-actuelle.md).

## 5. Choix d’architecture financière

| Option | Conclusion |
|---|---|
| A — Account standard + extension Régisseur/reçus métier | Recommandée : conserve factures, lignes, paiements, rapprochements et état de règlement standard; bridge séparé maintient le couplage facultatif. |
| B — finance personnalisée indépendante connectée à Account | Non recommandée comme noyau : risque de double comptabilité et de divergence. Un module métier léger n’est acceptable que comme couche opérationnelle reliée à Account, sans grand livre/payment mirror. |

Ce choix est une recommandation à confirmer avec les décisions métier/comptables, pas un arbitrage déjà approuvé. Détails : [comparaison-solutions-financieres.md](comparaison-solutions-financieres.md), [architecture-cible.md](architecture-cible.md).

## 6. Modèles, relations et workflow cible

Le bridge proposé porte `etat.civil.copy.request`, `etat.civil.copy.tariff` et un historique immuable de délivrance. La demande référence l’acte, le demandeur/partenaire, le tarif capturé, l’`account.move` et les métadonnées de délivrance. Les paiements restent ceux d’Odoo Account et sont contrôlés via l’état comptable réel et le rapprochement; aucun champ d’état ne doit être écrit directement pour simuler un paiement.

Première copie : vérifier l’historique sous verrou, puis autoriser une seule délivrance gratuite conformément à la règle juridique qui reste à confirmer. Copies suivantes : tarif actif non ambigu, facture unique, règlement complet confirmé par le rôle autorisé, puis autorisation et délivrance unique. L’accès à l’action rapport, route PDF et téléchargement revalide l’autorisation à chaque requête.

Les statuts proposés distinguent demande, facture/paiement et délivrance; ils ne remplacent pas les états existants des pièces justificatives. Voir [modeles-et-relations.md](modeles-et-relations.md) et [workflow-copies.md](workflow-copies.md).

## 7. Sécurité et permissions

La matrice Agent/Officier/Régisseur/Administrateur est une proposition contrôlée côté modèle, ACL, record rules, méthodes, contrôleurs et accès au rapport. Les boutons d’interface ne sont pas une frontière de sécurité. Les opérations sensibles — vérifier paiement, autoriser et délivrer — doivent contrôler utilisateur, centre, montant, état comptable et idempotence sur le serveur. Le Régisseur ne reçoit pas le droit de valider un acte. L’administrateur peut exécuter les opérations fonctionnelles autorisées tout en laissant une trace d’audit.

Voir [matrice-permissions.md](matrice-permissions.md) et le registre des risques. Les tests négatifs par RPC, URL directe, inter-centres et double appel restent à exécuter dans une base dédiée.

## 8. Liste des livrables

| Fichier | Contenu |
|---|---|
| `architecture-actuelle.md` | Modèles, workflows, modules et limites constatées. |
| `architecture-cible.md` | Addon passerelle recommandé et séparation des responsabilités. |
| `comparaison-solutions-financieres.md` | Comparaison A/B et recommandation. |
| `modeles-et-relations.md` | Modèles, champs, cardinalités et contraintes. |
| `workflow-copies.md` | Parcours gratuit/payant, états et protections. |
| `matrice-permissions.md` | Matrice et contrôles serveur/ORM/HTTP. |
| `plan-modifications.md` | Liste précise des fichiers proposés, risques et tests. |
| `diagrammes-uml.puml` | Diagrammes PlantUML de classes, séquence, activité, permissions et dépendances. |
| `risques-et-decisions.md` | Risques et décisions métier/comptables à trancher. |
| `rapport-phase4.md` | Ce rapport de synthèse. |
| `cahier-des-charges-final.md` | Exigences REQ/SEC/WF, statuts, architecture, traçabilité et critères. |
| `decisions-metier-a-confirmer.md` | Décisions métier/comptables à arbitrer. |
| `specifications-tests-acceptation.md` | 25 scénarios avec préconditions, action, contrôle serveur et preuves. |
| `architecture-securite.md` | Sécurité en couches, justificatifs, paiements et documents. |
| `plan-implementation-odoo17.md` | Phases A–J, fichiers, dépendances, risques, tests et preuves; non exécutées. |
| `SHA256SUMS.txt` | Empreintes des 15 documents de conception. |

## 9. Anomalies et risques résiduels

1. Pas de workflow de demande/délivrance de copies ni d’historique de première copie : risque élevé si la fonctionnalité est utilisée sans ajout d’une trace transactionnelle.
2. Pas de tarif ni de confirmation financière côté état civil : aucune délivrance payante ne peut être considérée comme sécurisée aujourd’hui.
3. Modules `account` et `product` désinstallés de la base revue : facturation/paiements indisponibles dans cette base, même si les sources Odoo existent sur disque.
4. Pas de rôle Régisseur identifié; responsabilités et comptes de test à définir.
5. Aucun parcours visuel ou authentifié financier testé.
6. ACL Admin `unlink` pour pièce justificative dans le checkout courant mérite une décision explicite de conservation; runtime à revérifier lors d’une future phase autorisée.
7. Modification du workspace préexistante et provenance générale non établie; changements conservés tels quels.

## 10. Contrôle de cohérence final

- Les modèles sont compatibles avec les addons Odoo 17 du checkout; leur disponibilité non installée dans la base est explicite.
- Les liens de copie visent les actes persistants concrets, pas `etat.civil.acte.officiel` abstrait.
- Facture brouillon/postée, paiement saisi/posté, rapprochement facture, rapprochement bancaire et confirmation Régisseur sont distincts.
- Toute route de délivrance proposée revalide les permissions et le paiement courant; les boutons XML ne protègent pas seuls.
- POS est comparé à la saisie Accounting; Accounting est recommandé pour le premier lot sous réserve de confirmation communale.
- Le PlantUML a été relu statiquement; aucun exécutable PlantUML n’était disponible pour le rendre [PREUVE MANQUANTE].

## 11. Préconditions à une phase d’implémentation

Les phases A–J de `plan-implementation-odoo17.md` sont prospectives et non exécutées.

- Arbitrer DEC-001–DEC-022 dans `decisions-metier-a-confirmer.md`, en priorité gratuité, tarifs, société/journal/taxes, preuve de paiement, Régisseur, remboursements, POS et conservation.
- Autoriser explicitement les modifications de code et désigner une branche de travail qui préserve les changements déjà présents.
- Préparer une base de test distincte avec données synthétiques et configuration Accounting; ne pas installer `account` dans la base revue sans autorisation distincte.
- Exécuter les tests automatisés, HTTP/RPC, accès direct au PDF et Chromium authentifié; les identifiants sont saisis par l’utilisateur dans le navigateur.
- Soumettre séparément toute sauvegarde, restauration, installation ou migration de base.

## 12. Conclusion

Le système financier utilisable dans l’architecture cible est **Odoo Accounting (`account`)**, absent du registre de la base revue. Aucun module financier custom réutilisable n’a été identifié. La passerelle proposée permet une intégration sans comptabilité parallèle, mais reste à concevoir puis tester après arbitrages et autorisation.

Les documents sont livrés; aucune fonctionnalité financière ou copie n’est déclarée opérationnelle sur cette base. **Statut global maintenu : B — Partiellement validé.**

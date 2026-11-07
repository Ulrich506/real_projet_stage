# Plan de modifications proposé — aucun changement exécuté

**Dépendance de séquence :** aucun fichier ci-dessous ne doit être créé/modifié avant décision écrite sur le module cible, la gratuité, le tarif, les droits Régisseur et la conservation. La base de revue reste exclue jusqu’à une autorisation séparée d’installation/mise à jour.

## Addon recommandé : `custom_addons/etat_civil_account/`

| Chemin prévu | Fonction prévue | Dépendances | Risques / tests requis |
|---|---|---|---|
| `__manifest__.py` (nouveau) | Module passerelle leaf, dépend de `etat_civil`, `account`; charge modèle, sécurité, séquence, vues et rapports. Ne modifie pas le manifeste `etat_civil`. | `etat_civil`, `account` (qui dépend de `product`) | Installer/mettre à jour modifie le schéma et crée la configuration; test install dans DB vierge et upgrade d’une DB d’essai. |
| `__init__.py` (nouveau) | Importer modèles, éventuellement contrôleurs QWeb seulement si nécessaire. | Addon | Imports Odoo 17; pas de side effects à import. |
| `models/__init__.py` (nouveau) | Charger tarifs, demandes et extension de partenaire/paiement si validée. | ORM | Vérifier ordre de champs et dépendances de modèle. |
| `models/copy_request.py` (nouveau) | `etat.civil.copy.request`: acte lié, demandeur, type, gratuité calculée, snapshot tarif/montants, lien facture, state, confirmer, autoriser, délivrer, historique. Verrouiller l’acte/demande et transitions. | `account.move`, `account.payment`, modèles `etat_civil` | Concurrence first-copy, double invoice/confirm/deliver, paiement partiel/annulé, report direct, Multi-company, droit RPC. |
| `models/copy_tariff.py` (nouveau) | `etat.civil.copy.tariff`: prestation/type, `product.product`, amount/currency/taxes, société/centre, périodes et activation. Validation anti-chevauchement. | `product.product`, `account.tax`, `res.company`, `res.currency`, centre | Prix ambigu/absent, multi-devise, compagnie, changement de tarif sans mutation des snapshots. |
| `models/res_users.py` (nouveau si nécessaire) | Champ centre du rôle Régisseur ou relation existante si elle convient; groupe ne doit pas recopier les groupes système. | `res.users`, centre, Accounting | Ne pas ajouter de champs dupliqués si centre mapping existant suffit. Tests rôle cumulatif. |
| `security/security.xml` (nouveau) | Groupe `group_etat_civil_regisseur`; règles de centre/société; règles tarifs et demandes; rôle Admin. | Groupes `etat_civil` et Accounting standards | Vérifier ACL Accounting; aucune règle globale qui élargit `ir.move`. Tests cross-centre, cross-company et multi-group. |
| `security/ir.model.access.csv` (nouveau) | ACL request/tariff/historique par groupe; unlink refusé après soumission; Admin complet selon conservation. | Modèles du bridge | Paires ACL × record rules; tests create/read/write/unlink. |
| `data/copy_request_sequence.xml` (nouveau) | Séquence référence demande; pas de numérotation de copie finale avant délivrance. | `ir.sequence` | Trous en séquence tolérés et documentés; transaction simultanée. |
| `views/copy_request_views.xml` (nouveau) | Liste, formulaire, search, kanban éventuellement; boutons visibles selon groupe/état; afficher facture, tarif, historique, état; readonly snapshot. | Modèle et groupes | Visibilité UX n’est pas sécurité; tests tours Chromium et contraintes server. |
| `views/copy_tariff_views.xml` (nouveau) | CRUD tarif limité Admin/comptabilité; périodes, société, centre, produit, devise, taxes et historique. | Modèle tarif | Aucun champ prix sans monnaie; pas de tarif default codé. |
| `views/menus.xml` (nouveau) | Menus Demandes de copies, Régisseur (attente, confirmées, historiques) et Tarifs. | Actions | Menus limités aux groupes sans exposer les pièces d’identité à la caisse. |
| `reports/copy_reports.xml` (nouveau) | Action PDF distincte pour copie délivrée, `attachment_use=False`, groupe strict, modèle `etat.civil.copy.request`. | Report model | URL directe/RPC, cache, token et multi-centres; test avant/après paiement. |
| `reports/copy_templates.xml` (nouveau) | QWeb copie intégrale/extrait avec numéro de délivrance, références et éléments autorisés; aucune signature fictive. | Actes et request | Conformité légale, données protégées, pagination/impression. |
| `tests/__init__.py` et `tests/test_copy_request.py` (nouveaux) | Tests transactionnels première/gratuite, copies supplémentaires, tarifs, relations et états. | `TransactionCase` | Données temporaires uniquement; rollback/cleanup contrôlé. |
| `tests/test_copy_accounting.py` (nouveau) | Facture, invoice/payment state, rapprochement complet, partial/cancelled, double confirmation, avoir. | Accounting installé dans DB tests | Ne toucher ni aux relevés ni aux factures existantes; tests fixture exclusifs. |
| `tests/test_copy_security.py` (nouveau) | Agent/Officier/Régisseur/Admin, centres, companies, méthodes privées/direct RPC, URLs rapport. | ACL/rules | Appels par `with_user` et `HttpCase`, tests d’accès. |
| `tests/test_copy_tour.js` (nouveau, optionnel) | Tour Chromium: demande, montant, facture, statut, bloqueur et preview autorisée. | web tour, fixture | Compte/données synthétiques et base test; pas de secrets. |

## Fichiers existants envisagés

| Fichier existant | Modification envisagée | Statut |
|---|---|---|
| `custom_addons/etat_civil/__manifest__.py` | Aucune. La dépendance à Accounting reste dans le bridge afin d’éviter d’imposer l’installation à tous les utilisateurs d’État civil. | Ne pas modifier |
| `models/acte_officiel.py`, modèles naissance/mariage/décès | Aucune modification initiale; relations typées du bridge vers actes. Une méthode mixin dédiée n’est envisagée qu’en cas de besoin prouvé. | Ne pas modifier |
| `models/demande_guichet.py` / vues | Aucune. Réutiliser uniquement le type ou ticket guichet si un mapping métier est confirmé; ne pas convertir un ticket en demande de paiement. | Ne pas modifier |
| `models/piece_justificative.py` et ses vues | Aucune modification pour la facturation; un reçu justificatif attaché n’est jamais une preuve de paiement comptable. | Ne pas modifier |
| `reports/actes_reports.xml` | Aucune restriction nouvelle sur le PDF prévalidation/signature physique; ne pas recycler pour la copie payante. | Ne pas modifier |
| `security/ir.model.access.csv`, `security.xml` existants | Aucune dans la première architecture; ajout de droits dans l’addon bridge. ACL du checkout actuel doivent être validées face au runtime avant toute future opération. | Ne pas modifier |

## Extension POS, uniquement si approuvée

Addon optionnel futur `custom_addons/etat_civil_pos/` : manifeste dépendant de `etat_civil_account` et `point_of_sale`, relation request ↔ `pos.order`, lecture de `pos.payment` et `pos.session`; aucun enregistrement financier custom parallèle. À concevoir après clarification du matériel/caisse, session, clôture, annulation et source de reçu. Aucun fichier POS n’est inclus dans le premier lot.

## Ordre de livraison futur

1. Figer décisions métier/comptables et code de référence; isoler les changements de workspace préexistants dans une branche dédiée autorisée.
2. Vérifier les dépendances, droits et plan de migration dans le module nouveau uniquement.
3. Tests unitaires sur base de test temporaire dédiée; aucune fixture dans base revue.
4. Mettre à jour/install bridge dans une nouvelle base de test autorisée et vérifier schema/ACL.
5. Tests HTTP, RPC et accès fichier/rapport direct.
6. Chromiums authentifiés par saisie utilisateur; capturer données synthétiques seulement.
7. Soumettre plan de sauvegarde/upgrade séparé avant toute installation sur la base de revue ou autre environnement.

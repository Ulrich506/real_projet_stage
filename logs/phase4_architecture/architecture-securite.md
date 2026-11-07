# Architecture de sécurité cible — copies, justificatifs et finance

Ce document décrit des contrôles proposés. Aucun d’eux n’est déclaré implémenté par le bridge, qui n’existe pas encore.

## 1. Défense en profondeur Odoo

| Couche | Fonction | Vérifications obligatoires |
|---|---|---|
| Groupes `res.groups` | Attribuer les rôles Agent, Officier, Régisseur, Admin civil et groupes Accounting. | Pas d’héritage de droits comptables implicite; cumul de rôles explicite; superuser technique distinct. |
| ACL `ir.model.access` | Autoriser CRUD sur chaque modèle. | Permissions minimales; unlink interdit pour demande soumise, délivrance, historique et justificatif conservé. ACL sont cumulatives entre groupes. |
| Record rules | Restreindre les enregistrements visibles par centre/société. | Domaine appliqué liste, read, write, unlink; attention règles globales et OR cumulatif de règles de groupe. `company_id` et `centre_id` validés. |
| Méthodes ORM | Valider transitions métier, valeurs dérivées, idempotence et permissions. | `check_access_rights`/`check_access_rule`, groupe, centre, état, relation invoice/payment, société/devise, verrou; ignorer les paramètres sensibles client. |
| Contrôleurs/routes/report | Contrôler accès aux fichiers/PDF, HTTP direct, preview/download et rapport. | Authentication appropriée, ACL/record rules parent, état actuel, centre; aucune URL publique/token ou cache sans authorisation. |
| Vues XML/OWL | Présenter boutons et données selon état/rôle. | UX uniquement; ne remplace aucune des couches ci-dessus. |
| Comptabilité Odoo | Garder écritures, factures, paiements, rapprochement et avoirs. | Ne pas écrire manuellement `state`, `payment_state`, residual ou réconciliations; utiliser actions standards autorisées. |

## 2. Flux de justificatifs

### Transitions

- Agent et Admin civil : `a_fournir` → `recu` par action serveur seulement; ajouter/remplacer fichier uniquement dans les états métier autorisés, conserver version/hash/auteur/date selon politique.
- Officier affecté et Admin civil : `recu` → `verifie` après ouverture/examen; journaliser auteur/date et motif éventuel.
- Agent ne peut pas définir `verifie` même via `write`, import, JSON-RPC ou contexte client. Un paramètre contextuel ne constitue pas une preuve d’autorité.
- Aucun statut `rejected` n’existe actuellement; cette transition et son motif doivent être décidés avant implémentation.

### Lecture image/PDF

Le viewer est présent dans le checkout, mais test authentifié complet absent [PREUVE MANQUANTE]. Les routes `/web/image/` et `/web/content/`, les appels de widget et actions de download doivent être testés directement. `ir.attachment.public` ne doit pas être activé pour les pièces. Le serveur vérifie modèle propriétaire, groupe, centre et droit sur le parent avant de fournir bytes ou métadonnées. Le bouton consulter peut retourner `inline`; le bouton télécharger peut retourner `attachment`; les deux demandent la même autorisation serveur. Le PDF peut nécessiter requêtes range; chaque requête doit garder session/droit. MIME et nom de fichier utilisateur ne sont pas fiables; liste autorisée/taille limite/scan antivirus et traitement des formats actifs à définir.

Les journaux des consultations sensibles peuvent journaliser utilisateur, pièce, parent, centre, date et action (view/download) sans stocker le contenu, URL contenant jeton, nom personnel inutile ou secret. Durée de conservation [À CONFIRMER].

## 3. Condition d’autorisation de délivrance

Avant toute première délivrance — UI, RPC, URL rapport, endpoint PDF ou téléchargement — le serveur doit contrôler :

1. Session/identité et droits sur demande et acte.
2. Acte admissible, non annulé, centre correspondant.
3. Demande non annulée/rejetée et pas déjà délivrée sauf reconsultation protégée autorisée.
4. Première copie: entitlement historique unique accordé et non consommé auparavant; supplémentaire: tarif et facture correspondants.
5. Pour payant : facture client `account.move` liée à la demande, `state=posted`, partenaire, compagnie, devise, montant total cohérents, residual nul et `payment_state=paid` après arrondi monétaire; paiements reliés postés et absence d’inversion/avoir/remboursement invalidant le total.
6. Confirmation séparée du Régisseur autorisé, avec centre/société corrects et événement audit.
7. Permission explicite de délivrance pour rôle/centre; numéro/délivrance unique sous verrou.

`account.payment.is_matched` indique rapprochement à relevé bancaire dans la version Odoo 17 auditée; il n’est pas équivalent au rapprochement facture. Son obligation est [À CONFIRMER]. `payment_state` est calculé par Account et jamais modifié par le bridge. Un paiement enregistré/posté seul, pièce de caisse, capture écran ou reçu papier ne suffit pas.

Rapport recommandé distinct lié à demande, non attaché dans un cache partagé (`attachment_use=False` à confirmer selon exigences de réarchivage). Ne pas réutiliser le rapport d’acte imprimable avant validation/signature. Reconsultation après délivrance est une fonction d’archive privée : vérifier qu’une délivrance immuable existe et les droits/centre actuels. Un remboursement ultérieur génère un incident et ne change pas rétroactivement le fait de la remise; accès après délivrance révocable seulement selon règle légale [À CONFIRMER]. Aucun `web/content` public ne contourne le gate initial.

## 4. Contrôles des méthodes et des entrées

- Les méthodes publiques RPC ne font confiance à aucun champ `state`, `amount`, `copy_kind`, `center_id`, `company_id`, `payment_confirmed_by_id`, auteur/date ou ID d’acte fournis par client.
- Les méthodes de transition sont séparées : recevoir pièce, vérifier pièce, demander copie, résoudre tarif, créer facture, confirmer paiement, autoriser, délivrer, annuler, traiter incident/remboursement.
- Vérifier l’accès avant et après `sudo()` si un accès élevé est strictement nécessaire; préférer absence de `sudo`. Aucun `sudo` pour délivrer ou lire pièces sans ACL parent vérifiée.
- Contrôle `check_company` sur les relations financières; vérifier la société effective de la facture et journaux.
- Utiliser verrous transactionnels/contrainte unique contre course première copie, double invoice et double delivery; transitions idempotentes.
- Ne pas supprimer facture/paiement posté. Utiliser avoir/remboursement via Account et créer un événement incident lié.
- Empêcher write/unlink sur historique; corrections par nouvel événement lié, auteurs/dates immuables.
- Contrôler direct report action, `report_download`, route, `/web/content`, RPC, export/import et pièces jointes liées.

## 5. Matrice de refus côté serveur

| Attaque/action | Contrôle attendu |
|---|---|
| Agent écrit `piece.state='verifie'` | Refus action/méthode et `write`; seule transition Officier assigné/Admin. |
| Agent règle `amount=0` ou `copy_kind=first` | Valeurs recalculées côté serveur; write rejeté. |
| Utilisateur appelle `action_confirm_payment` sans Régisseur | Refus groupe avant effets; pas d’événement de confirmation. |
| Régisseur confirme sans invoice paid | Refus sous contrôle ORM de l’état actuel; aucune délivrance. |
| Agent récupère URL PDF avant paiement | 403/404 sans PDF, pour report/route/RPC/download. |
| Agent A demande ID pièce/acte centre B | record rule et contrôle parent renvoient refus/absence sans existence révélée. |
| Paiement confirmé puis annulé/avoir avant copie | Revalidation bloque; demande en incident/attente selon règle; garder historique. |
| Double clic/webhook/retry | Verrou/idempotence; pas de doublon invoice, confirmation, reçu ou delivery. |
| Admin civil corrige un acte ou pièce | Opération permise seulement par transition admin explicite; journal d’audit non effaçable. |
| Régisseur appelle validation d’acte | Refus; rôle financier ne crée aucun droit officier. |

## 6. Tests sécurité requis

Voir TEST-004–017, TEST-022–025 dans `specifications-tests-acceptation.md`. Exécuter ORM (`with_user`), JSON-RPC, HTTP direct, `report` action, Chromium authentifié et au moins un test concurrentiel en DB dédiée. Capturer code retour/état serveur sans donnée personnelle réelle. Une revue statique ou bouton masqué ne prouve pas l’absence de vulnérabilité.

## 7. Limites et décisions ouvertes

- ACL runtime actuelle de la pièce n’a pas été re-vérifiée; le CSV du checkout donne unlink Admin. Nouvelle politique de conservation et état réel runtime [PREUVE MANQUANTE].
- Viewer présent mais tests authentifiés JPG/PNG/PDF, charge volumineuse, URL directe et différentes résolutions non terminés.
- Groupes comptables minimums Régisseur/Admin selon installation cible [À CONFIRMER].
- Règle juridique première copie, conservation, reçu légal, rapprochement bancaire requis et procédure après remboursement [À CONFIRMER].

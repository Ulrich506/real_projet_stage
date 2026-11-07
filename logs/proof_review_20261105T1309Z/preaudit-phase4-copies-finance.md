# Pré-audit — pièces, délivrance de copies et architecture financière

**Date : 5 novembre 2026 (UTC)**  
**Étape accomplie :** étapes 1–3 (architecture, inventaire, anomalies).  
**Base examinée :** `etat_civil_final_review_20261105_1304`, lecture seule.  
**Instance :** `127.0.0.1:18071` / gevent `18072`, unité `odoo-etat-civil-review-mp-18071.service`.  
**Changements code/base : aucun. Tests d’écriture/UI authentifiés : aucun dans cette intervention.**

## 1. État de l’environnement

À la vérification, l’unité isolée est active, `/web/login` répond 200 et `/api/v1/health` retourne `status=ok` pour la base de revue. Les ports 18071/18072 restent liés; les services 8071 et 18205 n’ont pas été touchés.

Les seules requêtes de catalogue ORM utilisées dans cette étape ont été exécutées après `SET TRANSACTION READ ONLY`, ne contiennent que des SELECT puis se terminent par `ROLLBACK`.

## 2. Inventaire des modules financiers

### Dépôt et historique Git

- `custom_addons` contient un seul manifeste : `custom_addons/etat_civil/__manifest__.py`.
- Le manifeste État civil dépend de `base`, `mail`, `web`; il ne dépend pas de `account`, `account_payment`, `sale` ou `point_of_sale`.
- La branche locale et la branche distante visibles sont `main` et `origin/main`. La recherche des fichiers et chemins financiers sur les branches disponibles n’a pas révélé de module financier métier personnalisé. Le checkout contient les addons standards Odoo `account` et `point_of_sale` sous `odoo/addons`, ainsi que `account_payment`.
- Cette vérification porte sur le dépôt et les références Git présentes localement; elle ne peut pas exclure un autre dépôt/serveur de code non monté dans le projet.

### Catalogue de la base de revue

| Module | État lu dans `ir_module_module` |
|---|---|
| `account` | `uninstalled` |
| `account_payment` | `uninstalled` |
| `account_accountant` | `uninstallable` |
| `sale` | `uninstalled` |
| `sale_management` | `uninstalled` |
| `point_of_sale` | `uninstalled` |
| `pos_restaurant` | `uninstalled` |

**Conclusion :** aucune intégration financière n’est opérationnelle dans la base de revue et aucun module financier personnalisé n’a été identifié dans le dépôt disponible. Les briques standard Odoo sont sur disque mais désinstallées. L’installation de `account` ou POS est exclue de cet audit et nécessitera une autorisation explicite distincte.

## 3. Architecture métier État civil actuellement présente

### Pièces et workflow des actes

- `etat.civil.piece.justificative` relie ses pièces à un acte de naissance, mariage, décès ou une mention marginale; une contrainte vérifie exactement un propriétaire.
- Ses états sont `a_fournir`, `recu`, `verifie`. Réception et vérification sont tracées par utilisateur/date et message dans le chatter.
- Les actions serveur limitent la réception à l’Agent (ou admin métier) et la vérification à l’Officier, l’admin métier ou l’admin système. L’Officier doit traiter le dossier qui lui a été assigné. La validation d’acte exige le statut en attente et les justificatifs obligatoires vérifiés.
- Le groupe `Administrateur d’état civil` implique le groupe Agent, mais pas le groupe Officier. Les contrôles métier incluent toutefois des branches explicites `_is_etat_civil_admin()` pour la validation/réception/vérification et l’accès inter-centres.
- L’ACL pièce accorde lecture/écriture/création aux groupes Agent, Officier et Administrateur, mais `unlink=0`; seul `base.group_system` a suppression directe par ACL. Le modèle conserve en outre des protections selon l’état de l’acte.
- Les formulaires naissance, mariage et décès emploient la visionneuse intégrée; le formulaire de mention utilise `many2many_binary`. Les deux actions « Consulter » et « Télécharger » existent dans le widget d’acte. Le libellé présent est « Consulter », non le libellé demandé « Voir le fichier ».
- La suite historique sur la base revue a testé la route inline `/web/content` : l’Agent affecté a obtenu 200 et l’utilisateur d’un autre centre 404. Aucun nouveau parcours Chromium n’a été réalisé ici.

### Demandes de guichet et délivrance

`etat.civil.demande.guichet` possède un numéro de ticket unique, les champs nom/CIN du citoyen, type d’acte et type de demande (`copie_integrale`, `extrait`, `declaration_immediate`), priorité et états (`en_attente`, `en_cours`, `traite`, `annule`). Les transitions sont contrôlées par actions et l’édition directe des statuts est interdite.

Ce modèle est une file de tickets, pas une demande de délivrance de copie : il n’a pas de relation au dossier d’acte, de catégorie première/copie supplémentaire, tarif, montant, facture, paiement, reçu, confirmation régisseur, autorisation ou date/utilisateur de délivrance. Il n’existe pas de modèle distinct de copies ni de relation financière dans les modèles importés par le module.

### Impression et accès aux documents

Les actions PDF existantes produisent les actes officiels (naissance, mariage, décès, mention). Les rapports d’actes sont délibérément imprimables avant validation pour contrôle/signature physique et marquent le document comme non validé. Ce flux ne représente pas une copie délivrée après paiement et n’a aucun état financier à vérifier. Il ne faut pas réutiliser directement ces actions comme délivrance payante sans un point d’autorisation serveur distinct. Le QR et le hash valident l’intégrité du document; ils ne sont pas un paiement ni une signature manuscrite.

## 4. Écarts et risques identifiés

| Gravité | Écart / risque | Conséquence |
|---|---|---|
| ÉLEVÉE | Aucun module financier métier n’existe dans le dépôt disponible; `account`/`account_payment` désinstallés en base. | Impossible de créer/configurer et confirmer facture/paiement/régisseur dans cette revue. L’intégration demandée n’est pas réalisable à partir d’un module financier personnalisé déjà présent. |
| ÉLEVÉE | Aucun modèle de demande de copie ni registre de délivrances. | Le système ne peut pas déterminer de façon fiable première copie, copies supplémentaires ou empêcher deux premières copies concurrentes. |
| ÉLEVÉE | Aucun tarif, statut paiement ou lien d’acte à un paiement. | Aucune copie payante n’a de montant défini; aucune confirmation serveur n’est possible. |
| ÉLEVÉE | Les rapports d’actes servent au workflow légal de prévisualisation/impression avant validation. | Confondre ce rapport avec une copie payante créerait un accès hors du futur contrôle régisseur. Il faut maintenir ces parcours séparés. |
| MOYENNE | Les pièces n’ont pas d’état `rejeté`; seules les transitions à fournir → reçu → vérifié existent. | L’officier ne peut pas enregistrer un rejet explicite ni son motif sans étendre le modèle. À arbitrer : état distinct ou retour/correction du dossier existant. |
| MOYENNE | L’Agent/Officier/Admin ont tous `unlink=0` sur pièces; le modèle verrouille les pièces sur états traités. | Une politique admin demandant l’effacement/modification après validation est incompatible avec les ACL actuelles. Il faut conserver les traces légales et définir une correction/annulation append-only, pas supprimer silencieusement. |
| MOYENNE | L’admin métier est un groupe distinct sans implication du groupe Officier. Certains contrôles incluent explicitement l’admin, d’autres doivent être relus pour chaque nouvelle méthode. | Un nouvel endpoint peut facilement omettre l’admin ou lui attribuer une permission trop forte; les méthodes doivent vérifier explicitement les rôles et tracer l’action. |
| MOYENNE | Prévisualisation réelle des formats et parcours role-based non vérifiés en Chromium. | Les garanties de zoom, ratio, fermeture, responsive, erreurs d’accès et téléchargement volontaire restent non certifiées. |
| FAIBLE | L’action de prévisualisation s’appelle « Consulter ». | Écart d’étiquette UX par rapport à « Voir le fichier », sans preuve d’un problème fonctionnel. |

## 5. Architecture proposée — à valider avant développement

### 5.1 Séparation des responsabilités

1. **État civil** garde les actes, les pièces et leurs états actuels. Ne pas renommer `recu`/`verifie` et ne pas assimiler ces états à un paiement.
2. Ajouter un modèle dédié de **demande de copie/délivrance**, distinct du ticket `demande_guichet`. Il référence l’acte, le demandeur, le type de document, `premiere`/`supplementaire`, son état métier, l’utilisateur/date d’autorisation et l’utilisateur/date de délivrance.
3. La gratuité de la première copie doit venir d’un historique persistant des délivrances. L’opération doit être protégée contre les demandes simultanées (verrou/contrainte d’unicité définie après choix des règles : par acte et catégorie de copie). L’état « délivrée » ne se réinitialise pas en supprimant un ticket.
4. La demande payante reste bloquée tant que le montant n’est pas obtenu d’une configuration tarifaire autorisée et que l’objet financier lié n’indique pas réellement un paiement confirmé. Aucun montant de secours/codé en dur.
5. Garder des actions et routes séparées pour : PDF de contrôle/signature physique, consultation sécurisée d’une pièce, et délivrance d’une copie finale. Chaque accès à la copie finale revérifie côté serveur le droit et l’état de paiement; une URL directe ne doit pas bypasser le modèle de demande.
6. **Financier** : si Odoo `account` est le module retenu, le scénario pourrait utiliser une facture client (`account.move`) et son état de paiement réellement rapproché, avec référence de paiement selon les modèles installés/configurés. La confirmation régisseur doit venir de son flux d’encaissement configuré, pas d’un booléen saisi par l’état civil ni de la seule présence d’une image de reçu. Le module exact, la configuration comptable, la société, la devise MGA, taxes et séquences doivent être audités avant de coder.
7. Ne pas intégrer POS par défaut : il n’est utile que si le paiement doit passer par une session de caisse Odoo. La portée, le matériel et les règles de fermeture de caisse doivent être explicitement validés.
8. Journaliser les changements d’état et les liens d’acte, facture, paiement, reçu, régisseur, demande et délivrance. Pour les actes validés, privilégier la correction tracée plutôt que la suppression.

### 5.2 Politique admin à expliciter

Le code permet à l’Administrateur d’état civil de vérifier des pièces et de valider des actes sans être dans le groupe Officier, tout en traçant les transitions. Les règles de conservation bloquent certaines modifications et la suppression de pièces n’est pas accordée par ACL aux rôles métier. Cela semble protéger l’historique légal; ce n’est pas un privilège total. Avant d’élargir les droits, confirmer les opérations que l’admin peut faire sur les pièces après réception/validation, si une suppression est légalement permise, et quelles raisons/pièces d’audit sont obligatoires. Aucun contournement des transitions ou de la conservation ne sera introduit sans cette politique.

## 6. Plan de modifications et de tests proposé (non exécuté)

| Lot | Proposition | Risque / dépendance |
|---|---|---|
| A — Prévisualisation | Conserver le viewer existant pour actes, le réutiliser sur les pièces de mentions si souhaité; libellé « Voir le fichier »; tests OWL/tour Chromium JPG/JPEG/PNG/PDF, zoom, proportions, fermeture, téléchargement distinct, tailles et accessibilité inter-centres. | Ne pas rendre public; tester URLs `/web/content` et `/web/image`; limites de taille sur upload web à confirmer. |
| B — Permissions pièces | Tests `with_user` agent/officier/admin et outsider sur état, remplacement, suppression et URL; ajouter l’admin explicitement seulement aux méthodes où la politique le prévoit; conserver logs chatter. | Les documents et actes validés peuvent être soumis à conservation légale; pas de suppression brute. |
| C — Demande de copie | Nouveau modèle et vues de demande; lien typé vers un seul acte (FK explicite selon les types), historique de délivrance, état distinct de l’acte et des pièces; contrainte anti-double première copie après arbitrage métier. | Nécessite statut libre/gratuit, identité du demandeur, règle première copie (par personne, par acte ou par type), annulation et justificatifs. |
| D — Tarif/paiement | Dépendance à `account` ou à un module financier fourni par le propriétaire; tarif provenant d’un modèle paramétré; lien ORM à la facture/paiement et confirmation régisseur. | Installation d’account et configuration comptable modifient le schéma et les réglages; nécessite décision explicite, données de test isolées et autorisation de mise à jour de base. |
| E — Délivrance sécurisée | Route/action/report de copie distincts avec garde serveur à chaque consultation/téléchargement; idempotence paiement/délivrance; notification et journal. | CORS/CSRF, partage de liens, accès multi-centres, révocation et téléchargement par administrateur doivent être spécifiés/testés. |
| F — Tests isolés | Fixtures temporaires Odoo dans une base de test isolée, sans modifier les actes existants; tests de concurrence, paiement partiel/annulé, double notification, rôles et URLs directes; ensuite tours Chromium authentifiés. | Comptes de rôles, tarifs factices explicitement autorisés et environnement distinct nécessaires. |

## 7. Décisions nécessaires avant l’étape 4

1. **Module financier cible :** confirmer si le projet doit s’appuyer sur Odoo `account`/`account_payment` standard (désinstallés dans la revue), ou fournir le dépôt/branche du module financier personnalisé évoqué. Aucun code financier personnalisé correspondant n’a été trouvé dans les branches locales/distantes consultées.
2. **Gratuité :** la « première copie gratuite » s’applique-t-elle par acte, par personne et type d’acte, ou une fois par demandeur? Les duplicatas après perte/erreur suivent-ils cette règle?
3. **Tarif et fiscalité :** quel modèle sera source de vérité pour le tarif, quelle société/devise/taxe s’applique, et qui peut modifier le tarif? Aucun montant ne sera inventé.
4. **Régisseur :** le rôle vient-il d’un module existant hors dépôt ou doit-il être créé? Qui confirme un paiement en espèces/virement et quel justificatif constitue une preuve recevable?
5. **Actes existants :** faut-il conserver l’impression de contrôle prévalidation ouverte aux rôles actuels, tout en créant un document de copie postpaiement séparé? C’est la séparation recommandée.
6. **Administrateur et conservation :** quelles opérations de correction/suppression sont légalement permises après qu’une pièce ou un acte a été reçu/vérifié/validé? Confirmer les motifs/audits obligatoires.
7. **Rejet d’une pièce :** faut-il ajouter un état `rejeté` avec motif et possibilité de remplacement, ou utiliser le workflow existant `a_corriger` de l’acte?
8. **Tests authentifiés :** fournir des comptes autorisés ou saisir les identifiants directement dans Chromium; ne pas envoyer les mots de passe dans un fichier.

## 8. Résultat des étapes 1–3

- Architecture et implémentation présentes inventoriées; aucun module financier custom n’est trouvé sur `main`/`origin/main` du dépôt disponible.
- Facturation/paiement/POS/régisseur non opérationnels dans la base de revue; addons standards présents sur disque mais désinstallés.
- Le modèle de guichet ne réalise pas la délivrance de copies payantes.
- Viewer de pièces existant pour les actes; preuve d’accès inline automatisée historique ciblée; vérification visuelle/authentifiée toujours en attente.
- Séparation de la réception/vérification de pièces, validation d’actes et future délivrance de copies nécessaire.
- Aucune modification code/base, aucun module installé, aucune facture/paiement/acte créé.

**Statut : B — Partiellement validé.** Étape 4 (modifications) suspendue conformément à la méthode demandée, en attente des décisions/autorisation ci-dessus.

## 9. État du répertoire de travail observé à la clôture

`git status --short` montre déjà de nombreux fichiers suivis modifiés, notamment des sources sous `custom_addons/etat_civil`, ainsi que des changements/suppressions et fichiers non suivis sous `data/filestore`, et des éléments `.idea`. Aucune photographie Git du répertoire avant cette phase n’est disponible; leur provenance ne peut donc pas être attribuée à cette intervention ni à une autre. Je n’ai pas inspecté/modifié ces fichiers, restauré quoi que ce soit ou supprimé de contenu. Les seules modifications intentionnelles de cette phase sont les deux documents de rapport/preuve. Le serveur et la base restent inchangés par les requêtes de lecture seule. Garder les écarts Git et filestore existants intacts jusqu’à attribution indépendante.

# Rapport de validation — module État civil

**Date : 5 novembre 2026 (UTC), mise à jour 14:05**  
**Statut global : B — Partiellement validé**

## 1. Résumé exécutif

Trois rapports PDF ont été produits en lecture seule depuis la base de revue et inspectés par extraction de texte et aperçu raster. Les rendus finaux `*-live.pdf` sont A4 portrait, une page chacun, et leurs ressources PDF ont répondu 200 via un relais local temporaire vers l’URL de base déjà configurée. Les zones de signature physique sont vierges et l’emplacement du logo reste vide. Il n’y a aucune mention marginale dans les données de revue, et aucun acte à texte long pour éprouver les retours à la ligne ou la pagination.

La suite automatisée disponible est passée, mais elle a été exécutée sur `etat_civil_admin_roles_validation_20261104`, pas sur la base de revue. Le serveur de revue était arrêté au début du contrôle. Son journal s’interrompait sans fermeture Odoo. Après vérification de l’ancien lancement détaché et de l’absence du PID, le serveur a été relancé dans une session d’exécution attachée. Il répond maintenant sur les deux ports isolés. Le service actif sur 8071 n’a pas été touché.

Les authentifiants autorisés ne sont pas disponibles. Aucun scénario Agent, Officier ou Administrateur authentifié n’a été joué dans Chromium. Aucun compte ou mot de passe n’a été modifié.

La phase 3 bis a confirmé par lecture ORM que `account` et `point_of_sale` sont désinstallés. Le suivi « reçu/vérifié » du module porte sur les pièces justificatives, pas sur les reçus financiers. Aucun rôle Régisseur, caisse, facturation ou tableau de bord des ventes n’est implémenté dans ce déploiement. La visionneuse de pièces existe dans les formulaires des trois actes, mais ses interactions complètes n’ont pas été vérifiées en Chromium. Le détail et la matrice IMG/REC/FAC/POS/REG/TDB/INT figurent dans [audit-fonctionnel-phase-3bis.md](audit-fonctionnel-phase-3bis.md).

## 2. Environnement testé

| Contrôle | Statut | Résultat / preuve |
|---|---|---|
| Base de revue | VALIDÉ | `etat_civil_final_review_20261105_1304`; modules `base`, `web`, `mail`, `etat_civil` installés; 1 acte de naissance, 1 mariage, 1 décès, 0 mention marginale. |
| Filestore | VALIDÉ | `/home/ulrich/tous_les_projet/stage_l3_odoo/data/filestore/etat_civil_final_review_20261105_1304`, répertoire présent, 58 fichiers. |
| HTTP 18071 à la clôture | VALIDÉ | Répond 200 à `/web/login`; unité systemd utilisateur `odoo-etat-civil-review-mp-18071.service` active, PID maître 428338. |
| Gevent 18072 à la clôture | VALIDÉ | Port lié par le processus evented 428373; le précédent GET `/longpolling/poll` renvoyait 404 pendant que le service écoutait. |
| Processus de revue 18071/18072 | VALIDÉ | Unité systemd utilisateur persistante active, deux workers HTTP, gevent distinct, `--max-cron-threads=0`. Les 24 modules chargent sur la base attendue. |
| Arrêt de l’instance précédente | PARTIEL | Aucun message Odoo de shutdown. Le lancement précédent utilisait `nohup` depuis un shell détaché; cette cause probable n’est pas confirmée par le journal. |
| Service actif | VALIDÉ | Processus distinct observé sur 8071; aucun redémarrage ni arrêt. |
| Addons lors du dernier démarrage réussi | VALIDÉ | Journal isolé : addons du cœur local, cache `data/addons/17.0` et `custom_addons`; aucun `/usr/lib/python3/dist-packages/odoo/addons`. Démarrage avec `PYTHONPATH` retiré; 24 modules chargés. |
| URL/filestore configurés | VALIDÉ | Base revue explicitement sélectionnée; filestore correspondant existe avec 58 fichiers. Le `web.base.url` stocké est `http://localhost:18201`; relais temporaire local arrêté après le rendu PDF. |

Le processus précédent avait disparu et aucun port de revue n’écoutait. Après vérification du PID, des ports et du journal (sans cause confirmée dans Odoo), le démarrage a été repris sous une session attachée afin qu’il reste suivi. L’instance active sur 8071 est restée intacte.

## 3. Preuves de démarrage isolé

Le démarrage courant utilise la base et le filestore ci-dessus, deux workers, `max_cron_threads=0`, HTTP 18071 et gevent 18072. HTTP répond 200, le port gevent est lié, et les 24 modules se chargent. Le GET `/longpolling/poll` renvoie 404, tandis que le journal confirme le service evented à l’écoute. Voir `isolated-server-live.log`, `isolated-server-last-known.log` et `browser-login-live.png`.

Le premier processus attaché s’est arrêté gracieusement à 13:30:09 UTC à la fin de la session d’exécution; aucune erreur applicative n’apparaît. Après ce diagnostic, il a été relancé sous unité systemd utilisateur persistante avec les mêmes ports/base/filtrage, deux workers et cron désactivé. Le serveur est disponible à la clôture. Le service actif sur 8071 n’a pas été touché. Une autre instance préexistante a été observée sur 18205 (PID 307678), configurée pour cette même base; elle n’a pas été utilisée ni modifiée et son propriétaire fonctionnel reste inconnu.

## 4. Résultats des rapports PDF

Les PDF et les fichiers dérivés sont dans ce répertoire de preuves :

| Rapport | Statut | Contrôles |
|---|---|---|
| Naissance | PARTIEL | `naissance-live.pdf`, record 109, no `BROWSER-N-1`, A4 portrait (595×842 pt), 1 page. Texte extrait en UTF-8 avec accents, dates, données et empreinte/QR. Aperçu inspecté; zone de signature visible et vierge. |
| Mariage | PARTIEL | `mariage-live.pdf`, record 23, no `MAR/2026/00001`, A4 portrait (595×842 pt), 1 page. Champs témoins/régime extraits; « NON VALIDÉ » présent. Aperçu inspecté; signature physique vierge. |
| Décès | PARTIEL | `deces-live.pdf`, record 15, no `DEC/2026/00001`, A4 portrait (595×842 pt), 1 page. Date, défunt, déclarant et « NON VALIDÉ » extraits. Aperçu inspecté; signature physique vierge. |
| Mention marginale | EN ATTENTE | Aucun enregistrement dans la base; aucun PDF généré. |
| Textes longs / débordement / pagination multi-page | NON TESTÉ | Textes intégraux présents dans les trois actes : 42, 21 et 19 caractères. |
| Plusieurs mentions | NON TESTÉ | Aucun acte ne porte de mention marginale. |
| Marges / aspect visuel | PARTIEL | Paramètres papier : A4 portrait, marges 35/20/15/15 mm. Les trois nouveaux aperçus raster ont été inspectés; aucune ressource PDF ne signale d’erreur lors du rendu final. Les anciens fichiers sans suffixe `-live` gardent leur avertissement car générés serveur arrêté. |

`pdfinfo`, `pdftotext -layout`, validation UTF-8 et `pdftoppm` ont été utilisés. Les rendus finaux sont `naissance-live.pdf`, `mariage-live.pdf`, `deces-live.pdf`; les empreintes et détails figurent dans `pdf-render-summary-live.txt` et `SHA256SUMS.txt`. Le rendu a utilisé un relais TCP temporaire sur 127.0.0.1:18201 vers HTTP 18071, conforme à `web.base.url` existant; aucun paramètre de base n’a été modifié. Le logo reste vide; aucun cachet, signature manuscrite ou image de signature n’a été ajouté.

## 5. Tests automatisés existants

**Aucun test automatisé n’a été exécuté sur la base de revue dans cette intervention.** Aucun résultat d’une autre base n’est attribué à celle-ci.

Résultats lus dans `logs/session_validation_20261105/` :

| Journal | Base | Heure UTC | Résultat |
|---|---|---:|---|
| `post_redesign_full_suite.log` | `etat_civil_admin_roles_validation_20261104` | 11:14:55 | 91 tests post, 105 tests module, 9 échecs, 0 erreur, code sortie 1. |
| `post_redesign_full_suite_2.log` | même base | 11:18:02 | 91 tests post, 105 tests module, 3 échecs, 0 erreur, code sortie 1. |
| `post_redesign_full_suite_3.log` | même base | 11:19:55 | 91 tests post, 105 tests module, 0 échec, 0 erreur, code sortie 0. |
| `final_full_suite.log` | même base | 10:55:30 | 91 tests post, 105 tests module, 0 échec, 0 erreur, code sortie 0. |
| `final_full_suite_unicode.log` | même base | 11:29:06 | 91 tests post, 105 tests module, 0 échec, 0 erreur, code sortie 0. |
| `encoding_fix_full_suite.log` | même base | 11:54:33 | 91 tests post, 105 tests module, 0 échec, 0 erreur, code sortie 0. |

Les trois journaux sans échec les plus récents incluent les tests de rapports naissance/mariage/décès, champs optionnels et témoins historiques absents, impression physique, QR/hash, aperçu de pièces jointes, accès entre centres et validations réservées à l’officier affecté. Le journal du 11:54:33 UTC rapporte zéro échec/erreur. Les journaux ne donnent pas de total de tests ignorés; trois avertissements de graphe concernent le module `html_editor` non installable, ce qui n’est pas un décompte de tests ignorés.

Les deux suites intermédiaires en échec ont des assertions de rapport; leurs détails figurent dans les fichiers correspondants. Les exécutions suivantes sont passées sur la base de validation nommée ci-dessus.

## 6. Sécurité — statique et preuves de tests

| Contrôle | Statut | Résultat / limite |
|---|---|---|
| ACL et règles de centres | PARTIEL | Inspection statique : les actes sont filtrés par centre de registre; les pièces/mentions suivent les relations d’actes; groupes Agent/Officier/Admin séparés. Aucun nouveau test en direct. |
| Actions workflow et champs protégés | PARTIEL | Inspection statique : `statut`, empreinte et champs de transmission/validation refusent une écriture directe hors transition interne; les méthodes d’action font les contrôles métier. La suite réussie a des tests correspondants sur une autre base. |
| Rôles Agent/Officier/Admin | PARTIEL | ACL/XML et tests automatisés historiques disponibles; parcours authentifiés dans la base de revue non effectués. |
| Accès aux pièces/aperçus | PARTIEL | Le test `test_attachment_preview_route_respects_civil_centre_access` passe dans la suite historique; pas de tentative URL directe Chromium dans cette intervention. |
| Routes API/RPC | PARTIEL | Les routes métier sont principalement `auth='user'`, utilisent `request.env` et les actions modèle. Les tests HTTP API de la suite historique ont passé; aucun nouvel appel authentifié/RPC sur la revue. |
| `csrf=False` | PARTIEL | Présent sur l’API JSON. Les routes mutantes vérifient `application/json`; cela ne remplace pas un contrôle dynamique CORS/CSRF. Tests de navigateur/API authentifiés à faire. |
| `sudo()` | PARTIEL | Recherche statique : utilisations modèle pour séquences/fallback et une utilisation contrôleur dans la vérification QR publique. Cette dernière limite la recherche aux modèles d’actes autorisés, vérifie empreinte calculée et statut, puis ne renvoie que l’identifiant/type/numéro. Comportement HTTP non testé dans cette intervention. |
| Base choisie par le login API | EN ATTENTE | Le contrôleur peut prendre le champ `db` de la requête JSON pour `session.authenticate`; l’isolement effectif par `dbfilter` doit être éprouvé avant d’exposer l’API. Aucun essai vers une autre base n’a été effectué. |
| URL directe, téléchargements, changements d’identifiants, QR/hash | EN ATTENTE | Nécessite le serveur isolé disponible et des identifiants de test autorisés; aucune tentative inter-centres dynamique nouvelle. |

La revue statique et les tests historiques ne constituent pas une certification de sécurité. Aucun correctif de sécurité n’a été apporté dans cette intervention.

## 7. Parcours Chromium

La page `/web/login` a été ouverte dans Chromium après le démarrage courant. La capture est `browser-login-live.png` (la capture initiale est `browser-login.png`). Les probes HTTP anonymes sont enregistrés dans `api-anonymous-probes.txt` : `/api/v1/health` renvoie 200 et identifie la base de revue; les routes actes et profil redirigent vers le login (303); QR malformé renvoie 400. Aucun compte n’a été authentifié.

Pour les trois rôles, les scénarios ci-dessous sont **EN ATTENTE d’identifiants autorisés et du serveur de revue disponible** :

- Agent : connexion, création, brouillon, transmission, pièces autorisées.
- Officier : connexion, file d’attente, contrôle, validation, génération et restrictions d’accès.
- Administrateur : connexion, gestion des utilisateurs, centres, droits et menus d’administration.

Aucun mot de passe n’a été deviné, exposé ou réinitialisé.

## 8. Préproduction

La base `etat_civil_preproduction_20261105` n’existe pas d’après la requête de catalogue PostgreSQL. Aucune base n’a été créée ou restaurée. Aucun backup n’a été lancé. La procédure proposée, avec chemins prévus et commandes non exécutées, est dans `preparation-preproduction.md`.

## 9. Actions nécessaires

1. Conserver l’unité `odoo-etat-civil-review-mp-18071.service` en fonctionnement pour les parcours ultérieurs; ne pas toucher aux instances 8071 ni 18205.
2. Fournir des comptes de test et mots de passe autorisés, ou les saisir directement dans Chromium sans les transmettre au rapport.
3. Répéter les tests API/URL authentifiés et les scénarios des trois rôles sur la seule base de revue.
4. Vérifier les ressources PDF dans un serveur isolé en état, ajouter des cas longs via mécanismes de test transactionnels, contrôler plusieurs pages et générer un rapport de mentions si des données de test existent.
5. Choisir la base source et la destination de sauvegarde; demander une autorisation explicite avant toute création/restauration de préproduction.

Aucun fichier source, compte, base active, filestore, commit ou push n’a été modifié dans cette intervention. Les ajouts se limitent aux PDF, aperçus, extractions et documents de preuve dans ce répertoire.

## 10. Phase 3 bis — résultats de l’audit fonctionnel approfondi

Le rapport détaillé est [audit-fonctionnel-phase-3bis.md](audit-fonctionnel-phase-3bis.md). Contrôles effectués en lecture seule sur la base de revue, sans écriture métier.

| Domaine | Statut | Résultat principal |
|---|---|---|
| Images / justificatifs | PARTIEL | Widget intégré et test historique `/web/content` centre autorisé 200 / outsider 404; pas de fichier image documentaire réel dans la base et pas de parcours visuel authentifié. |
| Reçus | ÉCHEC pour reçus financiers | « Reçu/vérifié » désigne les pièces justificatives; trois états seulement, aucun montant ou reçu de caisse. |
| Facturation | ÉCHEC — absente | `account` désinstallé, aucune intégration `account.move` dans le module. |
| POS | ÉCHEC — absent | `point_of_sale` désinstallé, aucune caisse ou commande POS. |
| Régisseur | ÉCHEC — rôle absent | Aucun groupe, menu ou modèle régisseur/caissier. |
| Tableau de bord des ventes | ÉCHEC — absent | Ancien dashboard retiré; API statistiques disponible pour les compteurs d’état civil seulement. |
| Interconnexions financières | ÉCHEC — non implémentées | Aucun lien acte-prestation-facture-paiement-reçu-POS dans le schéma audité. |
| Autres fonctions | PARTIEL | Actes, personnes, registres, mentions, guichet, workflows, import/export et rapports sont définis; les parcours UI authentifiés n’ont pas été exécutés ici. |

Note de traçabilité des tests : un journal supplémentaire de la base de revue a été retrouvé. `etat_civil_full.log` (10:33–10:34 UTC) rapporte 13 échecs; `etat_civil_full_http.log` (10:35:51–10:37:02 UTC) rapporte ensuite 91 post-tests, 105 tests module, 0 échec/0 erreur. Ce dernier contient le test ciblé de pièce jointe (200 pour l’Agent, 404 pour l’utilisateur d’un autre centre). Les suites plus tardives précédemment citées sont bien sur `etat_civil_admin_roles_validation_20261104`. Aucun de ces tests historiques n’est une navigation Chromium.

## 11. Phase 4 — pré-audit délivrance de copies et finances

Étapes 1–3 réalisées, sans modification du code ni de la base. Le dépôt consulté ne contient qu’un module personnalisé (`etat_civil`) et aucune branche financière métier; les addons Odoo `account`, `account_payment` et POS existent dans le checkout, mais sont désinstallés dans la revue. Le ticket guichet permet de sélectionner les types « copie intégrale » et « extrait », mais ne référence pas d’acte ni de tarif/paiement/régisseur/délivrance. Les rapports actuels sont des documents d’actes de contrôle/signature physique, imprimables avant validation; ils ne représentent pas une copie payée. Voir [preaudit-phase4-copies-finance.md](preaudit-phase4-copies-finance.md) pour architecture, anomalies, risques et décisions requises.

| Domaine | Statut | Constat |
|---|---|---|
| Modèle existant de demande de copie | ÉCHEC — absent | `demande_guichet` est un ticket de file sans lien à l’acte ni statut de délivrance. |
| Première copie gratuite / duplicata | NON DISPONIBLE | Aucun historique de délivrance ni règle anti-doublon; la définition métier reste à confirmer. |
| Tarif / paiement / régisseur | NON DISPONIBLE | Aucun module financier personnalisé trouvé; `account`, `account_payment`, `sale` et `point_of_sale` sont désinstallés. |
| Garde de délivrance avant paiement | NON DISPONIBLE | Aucun objet de copie payante; les rapports actuels servent au workflow d’acte et doivent rester séparés. |
| Droits administrateur sur les pièces | PARTIEL | L’admin peut vérifier/valider par contrôles explicites, mais l’ACL ne permet pas le `unlink` métier et le code verrouille des pièces selon l’état. Une politique de conservation doit guider toute extension. |
| Prochaines étapes | EN ATTENTE | Confirmer le module financier cible, la règle de gratuité, le tarif/fiscalité, le rôle régisseur, la politique de conservation/rejet et fournir les rôles de test avant les étapes 4–10. |

L’étape 4 (développement) reste suspendue jusqu’à autorisation explicite après examen des décisions et du plan proposés.

`git status --short` montre un workspace déjà non propre avec plusieurs sources `etat_civil` modifiées et des écarts/suppressions sous `data/filestore`; faute d’un relevé préalable, leur origine est inconnue. Aucun de ces écarts n’a été restauré ou supprimé. Voir [preaudit-phase4-copies-finance.md](preaudit-phase4-copies-finance.md) pour cette limite de provenance.

# Audit fonctionnel approfondi — phase 3 bis

**Date : 5 novembre 2026 (UTC)**  
**Base :** `etat_civil_final_review_20261105_1304`  
**Instance :** Odoo local, HTTP `127.0.0.1:18071`, gevent `127.0.0.1:18072`; unité utilisateur `odoo-etat-civil-review-mp-18071.service`.  
**Portée :** revue statique du code, requêtes ORM/SQL en transaction PostgreSQL `READ ONLY`, consultation de journaux historiques de tests et probes HTTP anonymes déjà réalisés. Aucun test avec écriture ni parcours métier authentifié n’a été lancé pendant cette phase.

## 1. Résumé des constats

- La fonctionnalité « reçu / reçu et vérifié » implémentée est le suivi des **pièces justificatives d’un dossier d’acte**. Ce n’est pas un modèle de reçu de paiement.
- L’état d’une pièce comporte exactement trois valeurs : `a_fournir`, `recu`, `verifie`. Les statuts rejeté, annulé, utilisé, sélectionné ou à vérifier ne sont pas définis pour ce modèle.
- La visionneuse intégrée est implémentée dans les formulaires de naissance, mariage et décès avec le widget Owl `etat_civil_piece_attachments`. Le bouton « Consulter » ouvre le `FileViewer` Odoo; « Télécharger » est une action séparée. Les MIME previewables sont JPEG, PNG, WebP et PDF. Les autres pièces peuvent être téléchargées.
- Aucun champ `image_1920` ni image documentaire métier de type `fields.Image` n’a été trouvé. `qr_code_image` est un champ binaire de QR code (image standard Odoo dans les formulaires), pas une pièce justificative. Les assistants import/export ont aussi des champs binaires de fichiers.
- La base contient 1 acte de naissance, 1 mariage, 1 décès, 0 mention, 13 pièces (10 `a_fournir`, 3 `verifie`), et 1 pièce jointe liée de type PDF (8 772 octets). Une image QR existe sur l’acte de naissance; les actes de mariage et décès n’en ont pas dans leurs champs. Aucun échantillon justificatif JPG/PNG n’est présent.
- La lecture ORM de `ir_module_module` confirme `account=uninstalled`, `point_of_sale=uninstalled`, `pos_restaurant=uninstalled`; `etat_civil`, `base`, `web`, `mail` sont installés. Aucun modèle personnalisé de facturation, paiement, caisse, vente, reçus financiers ou régisseur n’existe dans le module.
- Le menu et les migrations indiquent que l’ancien tableau de bord client a été retiré. Une route authentifiée `/api/v1/statistiques` rend des compteurs d’actes, citoyens, registres et demandes guichet, pas des ventes ou indicateurs financiers.
- Le journal historique `etat_civil_full_http.log` atteste sur **la base de revue** qu’un test automatique du téléchargement inline `/web/content` a reçu 200 pour l’Agent et 404 pour un utilisateur d’un autre centre. Ce n’est pas une nouvelle session Chromium et ne valide pas les autres formats ou le viewer visuel.
- Les identifiants de test autorisés restent indisponibles pour la navigation interactive. Aucun formulaire authentifié, zoom, plein écran, facture, vente ou paiement n’a été exécuté en interface.

## 2. Méthode et état de l’instance

À la clôture de l’audit, systemd utilisateur indiquait l’unité active, `/web/login` répondait 200, et les ports 18071 et 18072 étaient liés. Le port actif 8071 est distinct et n’a pas été touché. Les requêtes inventaire ont été exécutées par le shell Odoo avec `SET TRANSACTION READ ONLY`, puis `ROLLBACK`; elles n’ont créé ni modifié aucun enregistrement.

La base et les comptes n’ont pas été modifiés par les vérifications de cette phase. L’interface n’a été consultée qu’anonymement; les scénarios qui nécessitent un rôle sont signalés comme non testés ou en attente.

## 3. 3.B.1 — Images et pièces justificatives

### Implémentation repérée

- `etat.civil.piece.justificative.attachment_ids` est un Many2many vers `ir.attachment`.
- Naissance, mariage et décès utilisent le widget `etat_civil_piece_attachments`; il montre le nom, la date/auteur de dépôt, une action de consultation pour les MIME pris en charge et une action distincte de téléchargement.
- Le composant appelle `useFileViewer()`/`FileModel` Odoo. Le ratio d’affichage, le zoom, le plein écran et la fermeture dépendent du viewer standard et n’ont pas été exercés en navigateur dans cette phase.
- Les mentions marginales utilisent encore le widget standard `many2many_binary`; le même contrôle de preview intégré n’est donc pas visible dans leur formulaire XML.
- Les images envoyées par l’API sont décodées et vérifiées; formats identifiés dans le code : JPEG, PNG, WebP. Le README annonce 5 Mo et 50 mégapixels. Les tests source vérifient une image PNG valide, le rejet de contenu invalide et de MIME falsifié. Les formats GIF/TIFF/SVG ne figurent pas parmi les formats acceptés par l’API.
- L’extension JPG/JPEG est représentée au MIME `image/jpeg`. La visionneuse accepte MIME, pas des extensions de fichier. PDF est previewable mais n’est pas une image.
- Les routes `/web/image` et `/web/content` sont celles d’Odoo; aucune route publique de fichiers personnalisée n’a été trouvée. L’attachement est créé privé (`public=False` dans le test automatisé); le test de route du module vérifie le chemin standard `/web/content/<id>?download=false`.

### Matrice IMG

| ID | Test / résultat attendu | Résultat observé et preuve | Statut |
|---|---|---|---|
| IMG01 | Image directement visible dans un formulaire | Widget de consultation déclaré dans les vues des trois actes; aucun formulaire authentifié ouvert pendant cette phase. Pas d’image justificative réelle en base. | PARTIEL |
| IMG02 | Image agrandie dans une prévisualisation | Le bouton appelle le viewer Odoo; zoom, plein écran et fermeture non exercés visuellement. | PARTIEL |
| IMG03 | Pièce justificative consultable sans téléchargement obligatoire | Le composant sépare « Consulter » et « Télécharger ». Test historique sur la base revue : réponse inline `image/png`, HTTP 200. La seule pièce actuelle en base est un PDF. | PARTIEL |
| IMG04 | Image JPG/JPEG | MIME JPEG autorisé par validation et visionneuse; aucun fichier JPEG réel et aucun parcours navigateur sur cette base. Test automatique historique ne démontre pas ici le rendu JPEG. | PARTIEL |
| IMG05 | Image PNG | Test source crée une PNG décodable et vérifie l’enregistrement/MIME PNG; le test route historique vérifie `Content-Type: image/png` en inline. Aucun aperçu Chromium sur cette phase. | PARTIEL |
| IMG06 | Image inexistante | L’état vide de l’interface n’a pas été exercé; aucun message dédié établi par les preuves consultées. | NON TESTÉ |
| IMG07 | URL d’image sans permission | Test historique sur base revue : l’utilisateur outsider reçoit 404 par règle d’accès `ir.attachment`; aucun nouvel appel URL n’a été fait. | VALIDÉ (preuve automatisée historique, périmètre limité) |
| IMG08 | URL d’image d’un autre centre | Même test : agent du centre autorisé 200, utilisateur outsider 404. Pas de test inter-centre en Chromium actuel. | VALIDÉ (preuve automatisée historique, périmètre limité) |
| IMG09 | Actualiser le formulaire et conserver l’accès | Pas de formulaire authentifié ni actualisation vérifiée. | NON TESTÉ |
| IMG10 | Image volumineuse chargée avec maîtrise | Limites déclarées côté API : 5 Mo / 50 MP; aucun gros fichier de test n’a été envoyé. Limite du chemin upload UI non mesurée. | PARTIEL |
| IMG11 | Proportions sur plusieurs résolutions d’écran | Viewer Odoo standard utilisé; aucun viewport mobile/tablette/desktop comparatif ni inspection visuelle de proportions dans ce test. | NON TESTÉ |
| IMG12 | Images attachées aux naissances, mariages et décès | Les trois formulaires incluent le widget. La base de revue ne contient qu’une pièce PDF; aucun JPG/PNG de dossier réel pour comparer les trois types. | PARTIEL |
| IMG13 | QR et champs binaires | `qr_code_image` est `fields.Binary(attachment=False)` avec widget image; une seule image QR existe dans les données de revue. Pas un champ image de justificatif. | PARTIEL |
| IMG14 | `/web/image` et `/web/content` | Test automatisé historique seulement pour `/web/content`; aucun test direct de `/web/image` dans cette phase. Aucun résultat attribué à une inspection UI. | PARTIEL |

**Résultat de données :** la requête de comptage read-only a renvoyé `application/pdf: 1 attachement, 8 772 octets`, sans lien orphelin; aucun MIME image justificative n’était lié à une pièce de la base. Cela interdit de conclure au rendu d’images réelles à partir du PDF déjà présent.

## 4. 3.B.2 — Reçus et vérification

Dans le code, `recu` signifie document remis à l’Agent et `verifie` signifie pièce contrôlée par l’officier ou l’administrateur métier. Les actions enregistrent l’utilisateur et l’horodatage et postent une trace dans le chatter de l’acte. Une pièce doit appartenir à exactement un acte/mention; un doublon du même type au sein d’un même dossier est rejeté. La validation d’un acte requiert la réception/vérification des pièces obligatoires selon la procédure.

Ce workflow ne représente pas les reçus d’encaissement. Il n’y a ni sélection/recherche par numéro de reçu de caisse, ni montant, facture, paiement, statut rejeté/annulé/utilisé, ni lien à une commande POS. Le champ `name` des pièces est une sélection de justificatifs (CIN, certificat, livret, etc.), pas un numéro de reçu.

| ID | Test / attendu | Résultat observé et preuve | Statut |
|---|---|---|---|
| REC01 | Liste de reçus de paiement disponible | Aucun modèle/menus de reçu financier; le modèle présent est `etat.civil.piece.justificative`. | ÉCHEC (fonctionnalité financière absente) |
| REC02 | Rechercher par numéro de reçu | Aucun champ/route de numéro de reçu financier. | ÉCHEC |
| REC03 | Sélectionner et rattacher un reçu à une opération | Aucun reçu financier ni relation paiement/opération. | ÉCHEC |
| REC04 | Consulter les données du reçu | Les pièces justificatives affichent leur type et état, pas montant/date/référence de paiement. | ÉCHEC |
| REC05 | Preview du document de reçu financier | Pas de document de reçu d’encaissement. Preview justificatif traité dans IMG01–IMG05. | ÉCHEC |
| REC06 | Vérifier un reçu financier et tracer l’agent | L’action « Reçu et vérifier » concerne une pièce d’acte; elle trace utilisateur/date dans le chatter. Aucun contrôle financier. | PARTIEL (autre sémantique) |
| REC07 | Bloquer la réutilisation d’un reçu déjà consommé | Aucune notion d’utilisation ou d’unicité de reçu de caisse; la contrainte d’unicité porte sur le type de pièce dans un dossier seulement. | ÉCHEC |
| REC08 | Reçu inexistant refusé | Route/modèle de reçu financier absent. | ÉCHEC |
| REC09 | Reçu rejeté refusé | `rejeté` n’est pas un état du modèle de pièce et aucun reçu financier n’existe. | ÉCHEC |
| REC10 | Historique de reçu financier | Chatter trace réception/vérification de pièces justificatives; aucun historique financier. | PARTIEL (journal de pièces seulement) |

États réellement implémentés sur la pièce : `À fournir`, `Reçu`, `Reçu et vérifié`. Les états « sélectionné », « à vérifier », « rejeté », « annulé », « utilisé » demandés ne sont pas implémentés sur cette entité.

## 5. 3.B.3 à 3.B.6 — Facturation, POS, régisseur, indicateurs de vente

Le contrôle du catalogue ORM sur la base revue donne `account=uninstalled`, `point_of_sale=uninstalled`, `pos_restaurant=uninstalled`. Le manifeste de `etat_civil` dépend seulement de `base`, `mail`, `web`. Aucun modèle `account.move`, `account.move.line`, `pos.config`, `pos.session`, `pos.order` ou `pos.payment` n’est utilisé dans les sources du module. Aucun rôle/groupe « Régisseur » ou « Caissier » n’est défini. Aucun tarif, facture, taxe, paiement ou compte de caisse n’est dans les modèles examinés.

| ID | Contrôle | Résultat observé | Statut |
|---|---|---|---|
| FAC01 | Menu/fonctions de facturation | Absents du menu, du manifeste et des sources du module; `account` désinstallé dans la base revue. | ÉCHEC (intégration absente) |
| FAC02 | Création/consultation/numérotation de facture | Aucun appel `account.move`, modèle ou action de facture. Aucun enregistrement financier à confronter. | ÉCHEC |
| FAC03 | PDF de facture liée à un acte | Seuls les rapports de naissance, mariage, décès et mention sont définis. Pas de facture PDF. | ÉCHEC |
| FAC04 | Montants, taxes, réductions, payé/impayé, verrouillage | Pas de champs ou modèles pour vérifier ces règles. | ÉCHEC |
| POS01 | Point de vente et session | `point_of_sale` non installé, aucune dépendance/intégration dans le module. Aucune session ouverte. | ÉCHEC (intégration absente) |
| POS02 | Commande, prestation, tarif et paiement | Modèles POS absents/non installés; aucun produit de prestation configuré par le module. | ÉCHEC |
| POS03 | Reçu, impression, annulation, clôture, ventes | Aucun flux POS disponible; aucune transaction touchée. | ÉCHEC |
| REG01 | Rôle Régisseur | Aucun groupe ou rôle Régisseur dans `security.xml`, les sources de rôles, ou les menus. | ÉCHEC (rôle absent) |
| REG02 | Espace financier et droits du régisseur | Aucun écran de caisse, reçus financiers, paiements ou rapports financiers. | ÉCHEC |
| REG03 | Séparation Agent/Officier/Régisseur/Caissier/Admin | Agent, Officier, Administrateur d’état civil existent; aucun rôle Régisseur/Caissier. La séparation métier finance n’est donc pas implémentée. | PARTIEL |
| TDB01 | Tableau de bord des ventes | Menu/action client retirés dans migrations 2.1.1/2.1.2 et absence de vues dashboard actuelles. | ÉCHEC (tableau de ventes absent) |
| TDB02 | Compteurs de vente/CA/encaissements/factures/reçus | Aucun indicateur financier ou de vente. | ÉCHEC |
| TDB03 | Route statistiques | `/api/v1/statistiques` calcule compteurs actes par type/date/état, citoyens, registres et demandes guichet; pas de ventes, périodes configurables, ventilation centre/utilisateur ou montants. Route `auth='user'`. Aucun appel authentifié de cette route effectué. | PARTIEL (statistiques d’état civil uniquement) |
| TDB04 | Cohérence tableau de ventes avec des données réelles | Aucun POS, facture ou paiement installé pour produire ces données. | NON TESTÉ (données/fonctionnalité absentes) |

« ÉCHEC » signifie ici que l’intégration demandée n’est pas présente dans ce déploiement, non qu’une action financière exécutée a échoué. Aucun document financier n’a été créé, modifié, annulé ou validé.

## 6. 3.B.7 — Interconnexions

| Parcours | Modèles attendus | Ce qui existe | Lacunes / statut |
|---|---|---|---|
| A — Acte et paiement | Acte → prestation → facture → paiement → reçu → vérification → document final | Actes naissance/mariage/décès, personne, registre, pièces, états de workflow et rapports d’actes. | Aucun produit/tarif, `account.move`, paiement, reçu financier ni étape de règlement. **ÉCHEC** pour parcours financier complet; génération d’actes est partiellement implémentée séparément. |
| B — POS | Caisse → commande → paiement → reçu → historique → dashboard ventes | Aucun modèle POS installé; pas de rôle caisse ou dashboard vente. | Parcours absent. **ÉCHEC**. |
| C — Vérification financière | Reçu → montant → vérification → trace → indicateurs | Workflow de réception/vérification des documents justificatifs seulement, avec date/auteur/chatter. | Pas de montant, opération financière, facture ou indicateur de vente. **ÉCHEC** comme parcours financier; **PARTIEL** pour la vérification documentaire. |
| Documents d’état civil | Acte validé → QR/hash → rapport imprimable | Trois rapports d’actes; mention marginale dispose également d’une action rapport. QR/hash séparés de la signature manuscrite. Les trois PDF d’actes ont déjà été rendus dans la preuve précédente. | Mention non générable dans cette base car 0 enregistrement. Pas de PDF de paiement. **PARTIEL**. |

Contrôle cohérence read-only de la base : 1 acte par type, 0 mention, 13 pièces, 1 lien de fichier, aucune relation orpheline dans `etat_civil_piece_attachment_rel`; aucun module financier/POS installé. Aucun montant n’existe dans ce schéma pour rapprochement de factures/paiements. Les trois actes ne permettent pas de vérifier les doublons d’émission de facture, soldes, annulation ou caisse.

## 7. 3.B.8 — Inventaire des fonctions repérées

| Fonctionnalité | Modèles / interface / action | Accès et preuve | Statut |
|---|---|---|---|
| Personnes/citoyens | `etat.civil.individu`; liste, recherche, fiche, formulaire nouveau-né | ACL/groupes et règles selon sources; vues déclarées, pas de session rôle dans cette phase | PARTIEL |
| Naissance, mariage, décès | Modèles `etat.civil.acte.*`; listes, kanban, formulaires, filtres, actions workflow | Règles centre côté serveur, actions avec contrôles rôle/affectation; test historique de workflow sur la base de revue | PARTIEL |
| Mentions marginales | `etat.civil.mention.marginale`; liste, formulaire, validation, pièces, rapport | zéro donnée dans la base; widget de fichiers standard pour pièces; pas d’image viewer personnalisé | PARTIEL |
| Centre et registres | `etat.civil.centre`, `etat.civil.registre`; listes/formulaires, clôturer/rouvrir | Administration métier et groupes système selon XML | PARTIEL |
| Guichet / tickets | `etat.civil.demande.guichet`; file de liste, formulaire, appels et statuts | Routes API authentifiées et actions serveur; aucun parcours navigateur cette phase | PARTIEL |
| Pièces justificatives | `etat.civil.piece.justificative`; rattachement acte, upload/preview, réception/vérification | ACL/règles de centre; test automatique historique image inline + refus outsider | PARTIEL |
| Gestion comptes/rôles | `res.users` et wizard `etat.civil.gestion.utilisateur`; liste lecture seule, création/gestion par wizard admin | Groupe administrateur; aucun compte modifié ou connecté cette phase | PARTIEL |
| Transmission, correction, annulation | Wizards `etat.civil.transmission.acte.wizard`, `etat.civil.retour.correction.wizard`, `etat.civil.annulation.acte.wizard` | Actions de workflow contrôlées serveur; test automatisé historique | PARTIEL |
| Import/export citoyens | Wizards `etat.civil.import.wizard` / `etat.civil.export.wizard`; détection colonnes, prévisualisation, import/export | Formats et dépendances documentés dans wizard; aucune opération import/export lancée | PARTIEL |
| Journal import/export | `etat.civil.exchange.log`; liste et formulaire sans édition | ACL admin/système | PARTIEL |
| Rapports PDF | Naissance, mariage, décès, mention | `ir.actions.report`; trois actes produits précédemment, mention sans enregistrement en base | PARTIEL |
| API HTTP | Health, login/logout/me, personnes, registres, actes, mentions, validation, vérification QR/hash, tickets guichet, statistiques | Routes majoritairement `auth='user'`, `csrf=False` sur JSON avec vérification Content-Type; probes anonymes précédents, pas de test API authentifié courant | PARTIEL |
| Notifications / chatter | `mail.thread`, `mail.activity.mixin`, journal d’états | Dépendance `mail`; historique tests workflow; pas d’inspection UI | PARTIEL |
| Image QR | `qr_code_image` binaire sur actes, widget `image` | Une seule QR non vide sur acte naissance de revue | PARTIEL |
| Recherche/filtres | vues search pour actes, personnes, mentions, guichet, utilisateurs | XML statique | PARTIEL |
| Kanban | Actes naissance/mariage/décès | XML statique; aucune navigation authentifiée | PARTIEL |
| Calendrier/graph/pivot | Aucun `<calendar>`, `<graph>` ou `<pivot>` trouvé dans les vues du module | Revue statique du dépôt | VALIDÉ (absence dans les vues du module) |
| Tableau de bord Odoo | Ancienne action/menu dashboard supprimés dans migrations; aucune vue dashboard actuelle | Revue statique + migrations | VALIDÉ (absence actuelle dans le module) |
| Planificateurs cron | Aucun `ir.cron` déclaré dans les sources/data du module | Revue statique; cron de l’instance isolée reste désactivé | VALIDÉ (absence déclarée par le module) |
| Facturation/POS/finance | Aucun modèle, menu, route, action ou dépendance métier du module; account/POS désinstallés dans revue | Catalogue ORM + recherche sources | VALIDÉ (fonctionnalités absentes du déploiement audité) |

La revue d’interface réelle est incomplète : l’accès anonyme confirme le login uniquement. L’existence d’une vue XML ou d’un bouton n’est pas assimilée à la preuve qu’un rôle peut terminer le parcours.

## 8. 3.B.9 — Historique des tests et limites

- `logs/session_validation_20261105/etat_civil_full.log` concerne la base de revue et termine à 10:34 UTC avec 13 échecs/0 erreur lors d’un lancement antérieur.
- `logs/session_validation_20261105/etat_civil_full_http.log` concerne aussi la base de revue, débute à 10:35:51 et termine à 10:37:02 UTC : 91 post-tests, 105 tests module, 0 échec/0 erreur. Le test de route pièce jointe y renvoie 200 à l’Agent et 404 à l’outsider. Il y a plusieurs exécutions historiques de tests sur la base revue; ce rapport ne les a pas relancées.
- Les suites `encoding_fix_full_suite.log`, `final_full_suite_unicode.log` et autres suites postérieures qui avaient été présentées dans le rapport principal sont sur `etat_civil_admin_roles_validation_20261104`, non sur la revue.
- Aucun décompte d’ignorés n’est donné dans les lignes de résultat examinées.
- Les tests automatisés de contrôleur utilisent utilisateurs/données temporaires; cette phase n’a lancé aucun test comportant des écritures. Le test historique reste de la preuve test, pas preuve d’une session navigateur réelle.

### Matrice synthétique de traçabilité exigée

| ID | Fonctionnalité | Modèle | Interface | Action serveur | Droits | Test | Statut |
|---|---|---|---|---|---|---|---|
| IMG01–14 | Images / justificatifs | `etat.civil.piece.justificative`, `ir.attachment`, actes | Viewer widget dans actes; standard dans mentions | `/web/content` standard; upload API valide MIME | Règles centre et ACL attachment; preuve automatisée pour fixture | Test historique ciblé + revue statique; pas navigateur | PARTIEL |
| REC01–10 | Reçus financiers | Aucun; pièce justificative seulement | Aucun écran reçu de caisse | Aucune action financière | Aucun rôle financier | Contrôle ORM/sources | ÉCHEC (absent) |
| FAC01–04 | Facturation | Aucun modèle utilisé; account désinstallé | Aucun menu/action | Aucune | Non applicable | Contrôle ORM/sources | ÉCHEC (absent) |
| POS01–03 | POS | POS désinstallé | Aucun écran caisse | Aucune | Aucun rôle caisse | Contrôle ORM/sources | ÉCHEC (absent) |
| REG01–03 | Régisseur | Aucun rôle/modèle financier | Aucun espace dédié | Aucune | Aucun droit régisseur à tester | Contrôle XML/ACL | ÉCHEC (absent), séparation globale PARTIEL |
| TDB01–04 | Tableau de ventes | Pas de modèle vente | Dashboard client retiré; API statistiques d’actes seulement | `/api/v1/statistiques` authentifié | ACL/règles de modèles, route non testée en session | Revue code/migrations | ÉCHEC (dashboard financier absent), stats civils PARTIEL |
| INT-A | Acte → paiement → facture → reçu | Actes présents, modèles finance absents | Acte et PDF visibles selon droits | Workflow acte, pas finance | Contrôles état civil | Tracé statiquement | ÉCHEC (parcours incomplet) |
| INT-B | POS → paiement → reçu → dashboard | POS absent | Aucun écran | Aucune | N/A | Tracé statiquement | ÉCHEC |
| INT-C | Reçu → vérification montant → statistiques | Pièce documentaire seulement | Sous-formulaire pièces | Action reçu/vérifié documentaire | Agent/officier contrôlés par modèle | Sources et tests historiques | PARTIEL; parcours financier ÉCHEC |

## 9. Anomalies et gravité

| Gravité | Constat | Conséquence |
|---|---|---|
| ÉLEVÉE | Facturation, paiement, POS, reçu financier et rôle Régisseur sont absents; modules account/POS sont désinstallés. | Les parcours de perception, rapprochement, caisse et contrôle financier demandés ne sont pas réalisables dans la base actuelle. |
| ÉLEVÉE | Aucun test authentifié UI/API réalisé par rôle pendant cette phase. | Les droits effectifs et le flux complet ne sont pas certifiés en Chromium. |
| MOYENNE | Aucune image justificative JPG/PNG réelle dans la base; une pièce liée est un PDF. | Les promesses d’affichage d’images restent étayées par le code et un ancien test ciblé seulement. |
| MOYENNE | Widget de visionneuse personnalisé absent de la vue des pièces de mention marginale, qui emploie `many2many_binary`. | Comportement distinct des formulaires d’actes; preview sans téléchargement de ces pièces non établi. |
| MOYENNE | L’ancien run de tests sur la base revue a échoué 13 tests avant qu’un run ultérieur réussisse 105 tests. | Historique instable, à considérer avec les dates/configurations de logs; aucun de ces résultats n’est une validation UI. |
| FAIBLE | L’API statistiques ne fournit pas de période/centre explicites ni indicateurs financiers. | Ne répond pas au besoin de reporting ventes; aucun chiffre financier à comparer. |

## 10. Intervention nécessaire et statut

À fournir pour étendre la validation : comptes de test autorisés Agent/Officier/Admin et, si les fonctionnalités financières sont attendues, décision sur les modules/dépendances et comptes de rôle correspondants. Pour IMG06/IMG09/IMG11 et prévisualisation réelle, fournir une image de test autorisée ou autoriser l’utilisation de fixtures via un test isolé transactionnel. Pour toute création de données financières ou simulation d’écriture, obtenir une autorisation distincte.

**Statut de phase 3 bis : B — PARTIEL.** L’inventaire établit l’absence des fonctionnalités financières/POS/régisseur dans le déploiement actuel. La visionneuse et les protections d’accès ont des preuves statiques et une preuve automatisée historique ciblée, mais leurs parcours UI complets ne sont pas testés.

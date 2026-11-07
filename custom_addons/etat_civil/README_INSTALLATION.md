# État Civil — Odoo Web et application mobile

Odoo Web et l'application Flutter sont deux interfaces du même module serveur. PostgreSQL géré par Odoo est la source centrale des données ; le mobile utilise l'API Odoo et un cache SQLite local pour les consultations et brouillons hors connexion.

## Ce qui est intégré

- Menus réduits aux tâches d’état civil ; pas de tableau de bord statistique.
- Gestion des actes de naissance, mariage et décès.
- Numérotation des actes à l'enregistrement avec séquences séparées par type d'acte.
- Références automatiques distinctes pour les mentions de reconnaissance,
  adoption, divorce, changement de nom et autres mentions.
- Gestion des citoyens / individus.
- Import des citoyens depuis CSV, XLSX, XLS, JSON, XML, ODS et ZIP ; export en CSV, XLSX, JSON, XML et ODS.
- Journal des échanges accessible à l'administrateur d'état civil.
- Suivi des pièces requises par procédure ; photos ou scans facultatifs et vérification réservée à l’officier.
- Mentions marginales avec reconnaissance, adoption simple, mariage, divorce, décès, veuvage et changement de nom.
- Notifications de mariage à suivre vers les communes de naissance.
- File d'attente guichet partagée entre Odoo Web et l'application mobile.
- Recherche, filtres, regroupements et vues liste/kanban.
- Workflow : brouillon → validation → annulation → archivage.
- Annulation avec motif obligatoire dans une fenêtre de confirmation.
- Historique via le chatter Odoo.
- Empreinte SHA-256 et QR de vérification lors de la validation.
- Impression PDF des actes.
- Rôles : Agent, Officier, Administrateur d’état civil.
- Gestion des utilisateurs par l'administrateur État Civil, sans donner les droits techniques Odoo.

## Rôles et autorisations

- **Agent** : gère les citoyens, les brouillons d'actes et les tickets du guichet. Il peut consulter les mentions marginales, mais ne peut pas les créer ni les modifier. Il transmet les dossiers à un officier et ne peut pas valider, refuser ou annuler un acte.
- **Officier** : consulte et traite les dossiers transmis dans ses centres d'affectation. Il vérifie les pièces, valide ou refuse les actes, les renvoie pour correction et peut annuler, rectifier ou archiver un acte selon son état. Il ne reçoit pas les droits de saisie réservés à l'agent.
- **Administrateur d'état civil** : dispose des actions fonctionnelles de l'agent et de l'officier sans devoir appartenir à ces deux groupes. Il peut intervenir sur tous les centres et registres, gérer les comptes et référentiels, et effectuer les actions de workflow sous réserve des validations d'état, motifs et règles de conservation. Depuis **État Civil → Administration → Utilisateurs**, il peut créer un compte avec l'un des trois rôles ou modifier le rôle, les coordonnées, le mot de passe, les centres d'affectation et l'état actif. Les comptes sont désactivés plutôt que supprimés, afin de conserver la traçabilité. Cet accès ne confère pas les paramètres techniques d'administration Odoo.

Lorsqu'un administrateur valide un dossier, l'officier désigné lors de la transmission reste enregistré séparément de l'utilisateur ayant réellement effectué la validation. Le journal du chatter conserve également l'identité de l'auteur des décisions.

L'import XLS/XLSX et ODS requiert les bibliothèques Python `xlrd`, `openpyxl`
et `odfpy` dans l'environnement Python utilisé par Odoo. Les opérations
d'import/export sont consultables dans **État Civil → Administration → Journal
des échanges de citoyens** ; le journal enregistre les résultats et compteurs,
pas le contenu personnel des fichiers.
Les valeurs commençant par un marqueur de formule sont neutralisées dans les
exports CSV ; les cellules des exports XLSX sont écrites comme du texte.

Seul l'administrateur d'état civil hérite du groupe Agent ; les rôles Agent et Officier restent distincts et l'administrateur ne reçoit pas le groupe Officier ni le groupe technique `base.group_system`. Le statut d'un acte ne peut pas être modifié directement : il doit passer par les actions autorisées. Les contrôles d'état, les motifs et les pièces restent vérifiés y compris pour l'administrateur.

Les utilisateurs `base.group_system` disposent directement des droits du
module, des menus et actions d'administration et de validation, sans être
ajoutés aux rôles Agent, Officier ou Administrateur d'état civil. Ils ne sont
donc pas soumis aux règles territoriales d'un agent. Les contrôles métier
(motifs obligatoires, pièces justificatives, transitions et validations) restent
actifs. Les numéros d'actes sont attribués à la création avec les séquences
existantes ; les références des mentions suivent des séquences `no_gap`
distinctes par type. Les données de séquence sont déclarées sans réinitialisation
lors des mises à jour du module.

## File d'attente et API mobile

Les tickets sont stockés dans le modèle `etat.civil.demande.guichet`, avec un numéro attribué par une séquence Odoo. L'écran **État Civil → File d'attente** et l'application mobile utilisent les mêmes tickets via les routes authentifiées :

- `GET /api/v1/demandes-guichet`
- `POST /api/v1/demandes-guichet`
- `POST /api/v1/demandes-guichet/<id>/statut`

Créer un ticket ou changer son statut nécessite un compte Odoo membre du groupe Agent d'état civil. Les tickets définitivement traités ou annulés ne peuvent plus être modifiés.

Toute requête API `POST` ou `PUT`, y compris les actions sans corps, doit
utiliser `Content-Type: application/json`. Les corps envoyés comme formulaire
ou `text/plain` sont refusés (HTTP 415) ; les clients mobiles et intégrations
doivent conserver l'en-tête JSON pour les opérations de création, de mise à
jour et de workflow.

Les photos des pièces justificatives envoyées par l'API doivent être des
images JPEG, PNG ou WebP décodables, de 5 Mo maximum et de 50 mégapixels
maximum. Le MIME déclaré, lorsqu'il est fourni, doit correspondre au format
réel ; sinon, le MIME est déduit du contenu. Un fichier invalide est refusé
sans enregistrer partiellement l'acte ou ses pièces.

Dans les formulaires d'actes, la visionneuse Odoo affiche directement les
images JPEG/PNG/WebP et les PDF. Les autres types restent disponibles au
téléchargement manuel seulement. Les aperçus passent par les routes privées
`/web/image` et `/web/content` d'Odoo : les ACL et règles d'accès au dossier
continuent de s'appliquer, et les pièces ne sont pas rendues publiques.

La réception (« Reçu ») et la vérification (« Reçu et vérifier ») sont des
actions distinctes selon le rôle. L'état, l'utilisateur et la date sont
enregistrés; les changements apparaissent dans le chatter de l'acte avec
l'état précédent et l'état suivant. Les rapports d'actes sont imprimables
avant validation et n'effectuent aucune transition du workflow. Un document
non validé porte un avertissement explicite et des emplacements de signature
physique; le QR code et le hash existants restent distincts d'une signature
électronique.

## Installation

Copier `etat_civil` dans le dossier `custom_addons` indiqué dans `odoo.conf`, redémarrer Odoo, puis mettre à jour la liste des applications et installer/mettre à jour **Gestion d’État Civil**.

Après avoir restauré une copie de préproduction et vérifié son nom, la mise à
jour du module peut être exécutée sur cette copie :

```bash
./odoo-bin -c /chemin/odoo.conf -d BASE_PREPRODUCTION -u etat_civil --stop-after-init
```

Ne remplacez `BASE_PREPRODUCTION` par le nom d'une base active qu'après
autorisation explicite, sauvegarde vérifiée de la base et du filestore, et
planification d'une fenêtre de maintenance.

La mise à jour vers la version 2.1.6 remplace les champs CIN à l'écran tout en
conservant les données des anciennes colonnes NIN dans les colonnes CIN.
L'API continue de lire les anciennes clés pendant la transition vers les
clients mobiles mis à jour. Elle supprime également de la base l'ancien menu
« Tableau de bord » et son action client, qui ne sont plus utilisés.
Elle active aussi la langue malagasy dans Odoo ; le fichier de traduction du
module couvre les menus et les principaux champs, et sera enrichi avec les
autres écrans au fur et à mesure. Les libellés de filiation sont neutres. Les
pièces des conjoints étrangers marquées « requises » sont déterminées dossier
par dossier ; les CIN des témoins restent requises, mais aucun certificat de
résidence témoin n'est imposé par défaut. Cette version corrige aussi la
compatibilité des anciennes clés CIN lors de la modification d'un ticket
guichet et traduit l'écran mobile du guichet en malagasy et en français. Les
changements de statut restent limités aux actions de workflow prévues.
Le script du dépôt accepte une base explicite :
`./odoo17.sh update BASE_PREPRODUCTION etat_civil`. Il refuse toute mise à jour
si le service Odoo configuré est en cours d'exécution ; il ne l'arrête ni ne le
redémarre automatiquement.

## Gestion des utilisateurs d'état civil

Le menu **État Civil > Administration > Utilisateurs > Liste des utilisateurs**
affiche les comptes internes Odoo, leur rôle métier, leurs centres affectés,
leur état et leur dernière connexion. Cette liste est en lecture seule et
réservée aux administrateurs d'état civil et aux administrateurs techniques
Odoo. La création et la gestion des rôles continuent d'utiliser les assistants
existants adossés à `res.users` ; aucun modèle utilisateur parallèle n'est créé.

Après déploiement des fichiers du module, une mise à jour planifiée du module
est nécessaire pour charger le nouveau champ de rôle et les vues. Ne lancez pas
cette mise à jour sans sauvegarde vérifiée et procédure de déploiement approuvée.

## Connexion Odoo

Le login utilisateur se fait via `/web/login`. Le paramètre `admin_passwd` de `odoo.conf` est le **mot de passe maître** de gestion des bases et n’est pas le mot de passe de connexion de l’utilisateur Odoo.

Pour réinitialiser l’utilisateur administrateur :

```bash
./odoo-bin shell -c /chemin/odoo.conf -d gestion_detat_civil
```

Puis :

```python
user = env.ref('base.user_admin')
user.write({'password': 'CHOISIR_UN_MOT_DE_PASSE_FORT'})
```

## Modules Odoo

Obligatoires : `base`, `web`, `mail`.

Optionnels selon le périmètre : `contacts`, `documents`, `auth_signup`, `l10n_mg` lorsqu’ils sont disponibles et nécessaires.

## Remarque sécurité

Les modifications CORS globales de `ir.http` ont été supprimées : comme l’interface est désormais Odoo native, modifier toutes les routes Odoo n’apporte aucun bénéfice et augmente le risque de régression. L’API existante peut rester disponible pour de futures intégrations externes.

## Changelog 2.0.1

- **Correctif critique** : le formulaire "Acte de naissance" référençait un champ `date_naissance` inexistant sur le modèle (attribut `related=` invalide en vue XML). Odoo rejetait cette vue et affichait à la place le formulaire générique par défaut (les tableaux bruts "Nom de modèle de document associé / ID / Partenaire", "Nom du document / Type d'activité…", "Date / Sujet / Auteur…" que l'on voit à l'écran viennent des champs techniques `message_follower_ids`, `activity_ids`, `message_ids` hérités de `mail.thread`). Un vrai champ `date_naissance_enfant` (related) a été ajouté au modèle et la vue corrigée.
- Suppression des fichiers morts/doublons jamais chargés par le manifest, qui rendaient le code confus : `wizard/` (doublon de `wizards/`), `security/groups.xml` (doublon de `security.xml`), `views/dashboard.xml` et `views/search_views.xml` (doublons non utilisés), `static/src/scss/etat_civil.scss` (obsolète, classes CSS ne correspondant plus au template), `models/ir_http.py` (fichier vide jamais importé).
- `views/registry_actions.xml` corrigé (il pointait vers un assistant d'annulation inexistant) et réintégré dans `__manifest__.py` : clôturer/rouvrir un registre est maintenant aussi possible en masse depuis le menu Actions de la vue liste.
- Ajout de confirmations (`confirm=`) sur les actions sensibles : archivage d'un acte, clôture/réouverture d'un registre.

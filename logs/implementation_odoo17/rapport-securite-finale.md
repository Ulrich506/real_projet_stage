# Audit de sécurité final

Base d’analyse : sources présentes du checkout Odoo 17 et addons locaux. Aucun test n’a ciblé la base active ou de revue.

## Contrôles vérifiés

- La passerelle protège les transitions de statut par des méthodes serveur; `write()` rejette les écritures directes aux champs financiers et d’état sans jeton objet privé créé par le code serveur.
- Les actions de paiement vérifient le groupe Régisseur/Admin, le centre, l’état et les données Account. Le rapport copie vérifie les droits d’accès à la demande, le centre, l’autorisation et la condition financière lors du rendu.
- ACL et record rules limitent demandes, tarifs et événements par groupes/centres; l’administrateur civil dispose d’une règle globale. Le Régisseur lit les demandes et événements, sans ACL de création/édition de demande.
- Les `sudo()` du nouvel addon sont localisés à l’écriture de l’historique, aux champs de transition construits côté serveur, et à la lecture financière étroite retournant un booléen. Ces chemins ne sont pas exposés par une méthode RPC publique (préfixe privé).
- L’API login est `auth='none'`, JSON requis, base choisie uniquement par `request.db`; un nom de DB fourni par l’appelant différent est refusé. Les erreurs d’identifiants et de base divergent vers le même 401.
- Les logins passent par `res.users.login`; `email` de contact reste séparé. Les overrides `create/write` couvrent ORM, RPC ORM et imports ORM; `_login` couvre l’authentification web et API. Le domaine seul est mis en minuscules, les espaces externes sont retirés, le local-part est préservé; index unique `lower(login)` installé.
- Une connexion HTTP/API réelle avec comptes synthétiques Agent, Officier, Admin et Régisseur a réussi (login 200 puis `/api/v1/auth/me` 200 et uid concordant). Les comptes sont dans une base synthétique restaurée uniquement.

## Défauts / risques non résolus

| Gravité | Constat | Conséquence / preuve |
|---|---|---|
| ÉLEVÉE | `post_init_hook` ne refuse pas une base contenant des logins non e-mail. | `_login` les rejette dès activation. Risque de perdre l’accès admin/technique. La DB neuve examinée contenait des comptes Odoo par défaut non e-mail. Aucune vraie migration n’a été exécutée. |
| ÉLEVÉE | Rapports directs `action_report_acte_naissance`, mariage et décès restent liés aux modèles civils et accessibles par URL aux groupes agent/officier/admin, indépendamment d’une demande et d’un paiement. | Contournement potentiel si leur PDF est le même document délivrable; distinction « impression registre/signature » vs « copie au citoyen » à valider. La route du rapport passerelle seule ne suffit pas à protéger tous les PDF. |
| ÉLEVÉE | Aucune égalité serveur explicite entre montant/devise/partenaire de la demande et facture associée. | Taxes, devise ou édition de facture brouillon peuvent produire un total différent du tarif affiché; scénario de paiement réel non exécuté. |
| MOYENNE | L’API renvoie `session_id` dans le JSON de succès. | Exposition d’un identifiant de session au code client; confirmer le besoin ou supprimer de la réponse. |
| MOYENNE | Health public renvoie le nom de base. | Divulgation d’un détail d’infrastructure, sans donnée personnelle. |
| MOYENNE | Verrouillage corrigé pour soumission/délivrance, mais aucune simulation de deux transactions concurrentes n’a été exécutée. | Correctif revu statiquement et suite générale verte; preuve de course manquante. |
| MOYENNE | Reçu, avoir, remboursement et annulation après encaissement n’ont pas de workflow métier complet dans la passerelle. | La facture postée ne peut pas être annulée par `action_cancel`; le flux standard de note de crédit/remboursement reste manuel et non relié à l’autorisation de délivrance. |

## Points positifs avec portée limitée

- Le cœur Odoo 17 du checkout définit `account.payment` par héritage de `account.move`; le champ `state='posted'` utilisé par la passerelle est cohérent avec ce checkout. Une autre installation système expose une sélection différente : ne pas confondre les deux environnements.
- Les tests civils automatisés couvrent entre autres le cloisonnement territorial, les rôles, les transitions et les rapports. Ce sont des tests ORM, pas des tests HTTP authentifiés de l’ensemble des routes.
- Les routes civiles `auth='user'` utilisent souvent `csrf=False`; les mutations inspectées exigent JSON, mais une revue dynamique exhaustive du CSRF, des cookies, CORS, limitation de débit et de chaque endpoint reste à faire.
- Le vérificateur QR public utilise `sudo()` et divulgue seulement type, numéro, statut et résultat d’empreinte, sans identité dans la réponse examinée. Sa politique de confidentialité et la résistance à l’énumération restent à confirmer.

## Décision

Pas de validation production. Migrer/valider les comptes avant activation, clarifier les rapports directs, contrôler montant/facture, limiter la réponse de session et exécuter les tests d’API/report authentifiés sont des prérequis.

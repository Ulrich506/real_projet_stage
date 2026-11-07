# Audit et implémentation du login e-mail

Périmètre : checkout Odoo 17, addon isolé `etat_civil_auth_email`, et contrôleur API existant. Aucune donnée ni identité de la base active/revue n'a été lue ou modifiée.

## Constat réel

- `/web/login` transmet `res.users.login`; le champ standard `res.users.email` reste séparé.
- Le template standard utilisait un champ texte. Le nouvel héritage QWeb affiche « Adresse e-mail » et `type=email`.
- Le module `etat_civil` possède un wizard de gestion utilisateur et une route `/api/v1/auth/login`. Le wizard conserve les champs `login` et e-mail de contact distincts.
- La route API utilisait un fallback de base codé en dur et acceptait un nom de base fourni par l'appelant. La route a été corrigée pour n'utiliser que `request.db` déjà filtrée par Odoo; une valeur différente est refusée. La route conserve son message générique d'échec.

## Code livré

Nouvel addon `custom_addons/etat_civil_auth_email/` : validation serveur sur `res.users.create/write`, trim périphérique, normalisation du domaine seulement, local-part conservée, unicité insensible à la casse avec contrôle transactionnel et index unique PostgreSQL `lower(login)`, et rejet authentification des logins mal formés par `AccessDenied`. Le champ de contact n'est pas synchronisé. Le formulaire Web reçoit validation native du navigateur, qui reste une aide UX; la validation serveur est normative.

Un snapshot exact du contrôleur avant la correction API est conservé dans `backups/source-before-auth-api/main.py`, mode 600, SHA-256 `85bd47f836b58c1a8f8d29ead98557ba7844dc343954185b3ee60700530c17ec`. Seul le choix de DB de la route login a été modifié dans le contrôleur; les différences préexistantes ont été préservées.

## Résultats synthétiques

- Compte de test Odoo neuf : 5 comptes fournis par l'installation Odoo, 1 actif, 4 archivés; aucun login e-mail valide dans cette base vierge, 2 avec contact qui passe la vérification syntaxique et 3 sans contact syntaxiquement valide. Ils ne représentent pas l'annuaire réel du projet. Aucun compte ni mot de passe n'a été modifié.
- Collisions de logins normalisés dans la base vierge : 0; index PostgreSQL fonctionnel présent.
- Tests automatisés finaux : module email 9 au compteur Odoo, 0 échec/erreur; rejet d'une syntaxe invalide au point d'authentification testé. Dernier log : `odoo-latest.log`.
- HTTP `/web/login`: 200. Vérification DOM et capture Chromium 153.0.8010.52: le label Adresse e-mail et le champ `type=email` sont visibles.
- API `/api/v1/health`: 200 sur la DB synthétique exacte.
- API `/api/v1/auth/login`: e-mail invalide et tentative de DB caller-supplied renvoient toutes deux HTTP 401 avec réponse générique identique.

## Limites / migration

Aucune authentification réussie d'un humain réel ou d'un compte synthétique persistant n'a été faite. Pas d'identifiants autorisés disponibles; aucun mot de passe n'a été deviné ou modifié. La récupération de mot de passe, OAuth/SSO, comptes techniques et flux de reset ne sont pas validés.

La règle ORM stricte rend les logins non e-mail non créables/modifiables et l'authentification de ces logins refusée après installation. Il faut donc inventorier et migrer les vrais comptes avant déploiement; un administrateur sans login e-mail risque de perdre l'accès interactif. Les comptes techniques doivent être identifiés et leur mode d'accès confirmé avant installation globale. Aucun mécanisme d'exemption technique n'a été ajouté.

Conséquence observée pour la DB vide de test : ses comptes Odoo par défaut n'ont pas de login e-mail valide, donc aucun login interactif réussi n'est possible avec ces identifiants tant qu'une adresse réelle et autorisée n'a pas été associée/migrée. Cela n'affecte que les DB synthétiques créées ici; ne pas installer globalement avant le plan de migration.

Anomalie du premier essai : `email_normalize` seul acceptait `@example.org`; le module vérifie désormais qu'il existe exactement une séparation `@` et que la partie locale et le domaine ne sont pas vides. Le test final de ce cas est passé.

**Statut : TERMINÉ ET TESTÉ** pour le code sur DB synthétique et l'affichage de connexion. **EN ATTENTE** pour l'authentification réelle, les comptes techniques et la migration d'utilisateurs.

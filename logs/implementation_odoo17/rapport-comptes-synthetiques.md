# Rapport — comptes synthétiques Odoo

**Relevé :** 2026-11-06 09:20 EAT (+03:00).  
**Base :** `etat_civil_validation_20261106_0100`; Odoo 17.0; Python 3.14.4.  
**PostgreSQL / instance :** 18.6 sur 127.0.0.1:5432; HTTP/gevent 18391/18392, loopback.  
**Modules concernés :** `etat_civil`, `etat_civil_auth_email`, `etat_civil_account`, `account`.  
**Statut :** TERMINÉ ET TESTÉ pour l'authentification navigateur et les droits des demandes.

## Inventaire sans données d'identification

Quatre comptes métier fictifs ont été préparés : Agent, Officier, Régisseur et Administrateur d'état civil. Ils utilisent des identifiants de test du domaine réservé `.test`; les adresses exactes et mots de passe ne figurent pas dans les rapports ou les journaux. Les éléments d'accès restent hors dépôt et protégés.

La base contient neuf enregistrements `res.users` : cinq actifs (les quatre rôles synthétiques et le compte initial de la base synthétique) et quatre comptes de base inactifs conservés. Les cinq logins actifs respectent le format e-mail; aucun login actif incompatible n'est présent. Les comptes inactifs n'ont pas été réécrits. Aucun utilisateur réel, mot de passe réel ou hash réel n'a été importé.

Chaque rôle de test est associé à un centre synthétique. Le compte Administrateur de ce banc est un rôle de test, distinct d'une migration d'administrateur réel.

## Authentification et droits constatés

Les quatre rôles ont réussi l'authentification HTTP antérieure et une connexion dans Chromium en soumettant le formulaire Odoo. Ils ont atteint `/web`; le menu utilisateur est visible, sans alerte de connexion. Le service de menus répond HTTP 200.

Contrôle ORM sur `etat.civil.copy.request` et contrôle de lecture navigateur (les trois demandes sont des brouillons) :

| Rôle | Menus d'état civil vus dans le navigateur | Lire | Écrire | Créer | Supprimer | Demandes lisibles |
|---|---|---:|---:|---:|---:|---:|
| Agent | File d'attente, Citoyens / Individus, Demandes de copies | Oui | Oui | Oui | Non | 3 |
| Officier | Dossiers à examiner, Citoyens / Individus, Demandes de copies | Oui | Oui | Oui | Non | 3 |
| Régisseur | Demandes de copies | Oui | Non | Non | Non | 3 |
| Administrateur | File d'attente, Dossiers à examiner, Administration, Registres, Demandes de copies, Tarifs des copies | Oui | Oui | Oui | Non | 3 |

Le nombre de demandes visibles confirme également l'application de la règle de centre pour ces comptes; il ne constitue pas un test inter-centres. Les permissions des rapports PDF et les contrôles de délivrance directe n'ont pas été exercés dans le navigateur.

## Limites et preuves

La navigation a été automatisée avec Google Chrome headless via CDP; les profils temporaires ont été supprimés après les essais et aucune capture n'a été conservée. Ce sont des tests navigateur, pas une simple authentification API. Le canal WebSocket n'est pas correctement routé sur l'instance directe; les erreurs `KeyError: 'socket'` sont décrites dans le rapport de configuration.

Commandes/outils : formulaire `/web/login`; route Odoo `/web/webclient/load_menus/...`; lecture de `etat.civil.copy.request` dans la session navigateur; vérification ORM `check_access_rights` et `search_count` par compte. Aucun mot de passe, cookie, session ID ou login exact n'est enregistré ici.

**Fichiers modifiés :** aucun fichier source et aucun compte préexistant. Les comptes sont uniquement dans la base neuve; sauvegarde des identifiants hors dépôt. Aucun compte réel migré.

**Commandes/outils exécutés :** `git status --short`; contrôle PostgreSQL agrégé; tests Chromium headless via CDP; lecture de `/web/webclient/load_menus/...`; `search_count` en session navigateur; vérification des ACL et règles de centre via ORM en lecture seule. Les identifiants exacts et cookies ne sont pas inclus dans les preuves.
**Sauvegarde :** la base contenant les comptes synthétiques et son filestore figurent dans les archives SHA-256 documentées dans `rapport-sauvegarde-validation.md`.

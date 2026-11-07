# Rapport de création — base Odoo de validation

**Relevé :** 2026-11-06 09:20 EAT (+03:00).  
**Base :** `etat_civil_validation_20261106_0100`; PostgreSQL 18.6 sur `127.0.0.1:5432`.  
**Instance :** HTTP `127.0.0.1:18391`, gevent `127.0.0.1:18392`.  
**Odoo / Python :** 17.0 / 3.14.4 (`venv`).  
**Statut :** TERMINÉ ET TESTÉ pour la création et le chargement de la base synthétique.

## Résultat

La base a été créée neuve après contrôle de disponibilité du nom. Elle contient uniquement les données synthétiques décrites dans `rapport-donnees-synthetiques.md`; aucune sauvegarde de données réelles n'a été importée et aucun compte réel n'a été migré.

Les modules attendus sont installés : `base`, `web`, `mail`, `account`, `etat_civil`, `etat_civil_account` et `etat_civil_auth_email`. Vérification PostgreSQL : les sept états sont `installed`. Les tables des centres, registres, actes et demandes existent; le registre Odoo a été chargé avec succès sur la base de restauration distincte.

| Vérification | Résultat |
|---|---|
| Base source | Présente; taille PostgreSQL 44 054 207 octets au moment de la sauvegarde. |
| `/web/login` | HTTP 200; dernière mesure 0,107 s. |
| `/api/v1/health` | HTTP 200; dernière mesure 0,091 s. |
| Base restaurée par Odoo ORM | Registre chargé; trois demandes synthétiques visibles; zéro facture et zéro paiement. |
| Instance restaurée | Aucun serveur HTTP n'a été démarré pour la restauration; celle-ci a été vérifiée par chargement du registre, pas par un second navigateur. |

Le journal d'installation est `logs/implementation_odoo17/etat_civil_validation_20261106_0100.log`. Il montre l'initialisation Odoo et le chargement des modules. La ligne de commande initiale exacte de création n'est pas conservée dans les preuves disponibles; elle n'est pas reconstruite comme si elle était certaine.

Une première création de demandes depuis le rôle inadéquat a été rejetée par les droits métier; la transaction a été abandonnée. La reprise a créé les trois demandes synthétiques avec le compte Administrateur de la base de test. Aucune donnée partielle de cette tentative n'a été conservée.

## Portée et limites

La base fournit le banc de tests et répond sur ses ports dédiés. Elle ne valide pas les parcours de facturation, de paiement, de remboursement, de délivrance PDF ni de concurrence. Les tarifs de fixture sont inactifs et ne représentent pas une règle juridique.

Le journal contient un timeout de worker Odoo de 120 secondes dont la cause n'est pas établie, ainsi que des erreurs `KeyError: 'socket'` lorsque le navigateur tente `/websocket` directement sur le port HTTP. Le formulaire de connexion et les menus restent utilisables; le routage WebSocket via proxy manque. Aucun timeout n'a été augmenté et aucune instance n'a été redémarrée.

## Commandes / fichiers

Contrôles exécutés : vérification des noms et ports avant écriture; installation Odoo dans la configuration privée dédiée; requêtes PostgreSQL de contrôle en lecture seule; `GET /web/login` et `GET /api/v1/health`; tests Chromium authentifiés décrits dans `rapport-tests-navigateur.md`.

Fichiers et ressources dédiés : configuration source existante en mode 600; journal d'instance; base et filestore synthétiques; quatre comptes fictifs; rapports de cette phase; sauvegarde et restauration distinctes. Aucun fichier source de module n'a été modifié pendant cette validation. Les changements préexistants du dépôt ont été préservés.

La sauvegarde et la restauration créées pour cette base sont vérifiées dans `rapport-sauvegarde-validation.md`; les commandes d'archivage, de restauration et leurs empreintes y figurent.

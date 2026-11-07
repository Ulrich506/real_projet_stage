# Rapport de configuration — instance Odoo de validation

**Relevé :** 2026-11-06 09:20 EAT (+03:00).  
**Odoo / Python / PostgreSQL :** 17.0 / 3.14.4 / 18.6.  
**Statut :** TERMINÉ ET TESTÉ pour la configuration dédiée et les réponses HTTP de base.

## Configuration et isolation

Fichier privé : `logs/implementation_odoo17/etat_civil_validation_20261106_0100.conf`, mode 600. Paramètres non secrets vérifiés : base et `dbfilter` exacts `etat_civil_validation_20261106_0100`; hôte PostgreSQL loopback, port 5432, rôle `odoo17`; `data_dir` dédié `data/validation_20261106_0100`; interface HTTP loopback; HTTP 18391; gevent 18392; deux workers; cron désactivé; `without_demo=all`; `list_db=False`; `proxy_mode=False`. Les secrets de connexion et le mot de passe maître ne sont pas reproduits.

La configuration de restauration est distincte, épinglée à `etat_civil_validation_restore_20261106_0100`, son propre `data_dir` et son propre journal; elle est également en mode 600. Ses valeurs de ports HTTP/gevent sont réservées dans le fichier, mais aucun listener ni serveur de restauration n'a été démarré.

Le port 18390 était libre au contrôle et n'a pas été utilisé. Les ports protégés ne sont pas configurés dans ces fichiers. Aucun fichier de configuration préexistant n'a été écrasé.

## Vérifications d'exécution

- `venv/bin/python --version` : Python 3.14.4.
- `venv/bin/python odoo/odoo-bin --version` : Odoo Server 17.0.
- Les ports 18391 et 18392 répondent sur loopback; aucun listener sur 18390.
- `GET http://127.0.0.1:18391/web/login` : HTTP 200.
- `GET http://127.0.0.1:18391/api/v1/health` : HTTP 200.
- Chromium authentifié : formulaire, menus et lecture des demandes testés pour les quatre rôles; détails dans `rapport-tests-navigateur.md`.
- Base restaurée : chargement du registre Odoo sans HTTP réussi dans une seconde base neuve.

## Anomalies non masquées

Le journal contient une erreur `WorkerHTTP timeout after 120s` à 05:44, sans identifiant de requête permettant de la corréler. Sa cause reste inconnue; le délai n'a pas été augmenté.

Des requêtes navigateur vers `/websocket` envoyées directement sur 18391 provoquent `KeyError: 'socket'`. Odoo écoute le service evented séparément sur 18392; aucun reverse proxy isolé n'a été installé. Le test de connexion et les menus réussissent malgré cette fonction temps réel indisponible. Ce point reste à corriger avant de considérer l'interface entièrement validée.

La cause des 13 `ReadTimeout` de la régression HTTP antérieure reste inconnue; la suite complète n'a pas été relancée pour éviter de solliciter davantage les instances avant diagnostic. Les temps HTTP ci-dessus sont des mesures distinctes et ne constituent pas une explication de ces erreurs.

**Fichiers créés ou utilisés :** configuration source privée et journal d'instance; configuration de restauration privée et journal distinct; aucun code applicatif modifié. Les rapports et sauvegardes dédiés sont listés dans leurs rapports respectifs.

**Modules concernés :** `etat_civil`, `etat_civil_auth_email`, `etat_civil_account`, `account`, ainsi que les dépendances `base`, `web` et `mail`.  
**Commandes de contrôle :** `venv/bin/python --version`; `venv/bin/python odoo/odoo-bin --version`; `ss -ltnp`; chargement du registre Odoo en lecture seule; requêtes `GET /web/login` et `GET /api/v1/health`. Les créations de sauvegarde/restauration sont détaillées dans le rapport correspondant.  
**Sauvegardes :** dump PostgreSQL et archive du filestore synthétiques, mode 600, vérifiés SHA-256; aucune sauvegarde de données réelles. Les ports 18393/18394 inscrits dans la configuration de restauration n'ont pas été ouverts.

# Rapport de précontrôle — environnement Odoo de validation

**Relevé :** 2026-11-06 09:20 EAT (+03:00), horloge locale de la machine.  
**Cible :** banc synthétique Odoo 17, base `etat_civil_validation_20261106_0100`.  
**Modules concernés :** `etat_civil`, `etat_civil_auth_email`, `etat_civil_account`, `account`.  
**Statut :** TERMINÉ ET TESTÉ pour les préconditions de l’environnement dédié.

## Contrôles effectués

| Domaine | Résultat |
|---|---|
| Dépôt Git | `git status --short` a révélé un worktree déjà fortement modifié (ajouts indexés, modifications, suppressions et fichiers non suivis, dont du code et des données). Ces changements préexistants ont été conservés; aucun reset, clean, commit ou push. |
| Odoo / Python | Checkout Odoo 17.0; Python 3.14.4 dans `venv`. |
| PostgreSQL | 18.6 sur `127.0.0.1:5432`; rôle applicatif `odoo17`, `CREATEDB=true`, non-superutilisateur selon les relevés précédents. Connexion au catalogue confirmée en utilisant la configuration privée existante. |
| Authentification PostgreSQL | Une commande `psql -w` sans fichier de mot de passe a échoué avec « no password supplied ». Le contrôle suivant a utilisé en mémoire les paramètres de la configuration Odoo déjà autorisée; aucun secret n'a été affiché. La règle HBA exacte demeure inconnue et n'a pas été contournée. |
| Base source / restauration | La base source existait; le nom `etat_civil_validation_restore_20261106_0100` était absent juste avant sa création. Aucune base préexistante n'a été restaurée ou supprimée. |
| Filestore | Le filestore source existe dans `data/validation_20261106_0100/filestore/etat_civil_validation_20261106_0100`. Le répertoire de restauration était absent avant création. |
| Ports | L'instance dédiée écoute sur `127.0.0.1:18391` (HTTP) et `127.0.0.1:18392` (gevent). Le port 18390 était libre au précontrôle et n'a pas été utilisé. Les ports 8071, 18071, 18072, 18181–18184 et 18205 sont restés hors cible; les relevés antérieurs les signalaient utilisés. |
| Ressources | Au contrôle précédant la sauvegarde : environ 51,8 Go libres sur le volume et 11 Go de mémoire disponible; espace suffisant pour la base de 44 Mo et le filestore de 7,9 Mo. |
| Configuration | Configuration Odoo dédiée, `dbfilter` épinglé à la base, interface loopback, liste des bases désactivée, données de démonstration désactivées et cron désactivé. Fichier en mode 600; contenu secret non reproduit dans ce rapport. |

## Commandes et preuves

Contrôles exécutés : `git status --short`; `venv/bin/python --version`; `venv/bin/python odoo/odoo-bin --version`; vérification des sockets avec `ss -ltnp`; contrôle des destinations par `Path.exists()`; contrôles PostgreSQL en lecture seule par psycopg2 chargé depuis la configuration Odoo; vérification de l'espace avec `shutil.disk_usage()` et de la mémoire avec `free -h`.

La première tentative `psql -w` a échoué faute de mot de passe fourni. Le contrôle autorisé suivant a confirmé la version, le rôle et l'absence du nom de restauration, sans afficher ni contourner les secrets. Aucun service existant n'a été arrêté, redémarré ou reconfiguré.

**Fichiers créés pendant le précontrôle :** aucun. Les fichiers de sauvegarde et de restauration créés ensuite sont décrits dans `rapport-sauvegarde-validation.md`. Aucun fichier source n'a été modifié; aucune sauvegarde préalable de code n'était nécessaire.

La sauvegarde synthétique réalisée après validation des préconditions est documentée séparément; le précontrôle lui-même n'a écrit ni base ni filestore.

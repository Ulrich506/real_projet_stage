# Rapport — préparation d'un environnement Odoo isolé

Date/heure du relevé : 2026-11-06 00:52 EAT (+03:00). Odoo 17.0; Python 3.14.4 (`venv`); PostgreSQL 18.6 sur `127.0.0.1:5432`. Cette phase n'a créé ni base, ni filestore, ni configuration, ni service. Aucun module n'a été installé ou mis à jour.

## Inventaire de sécurité

Les ports protégés restent intacts. Le contrôle courant de sockets a observé les ports suivants en écoute : 8071, 18071/18072, 18181/18182, 18183/18184 et 18205. Ils n'ont pas été utilisés ni arrêtés. Les ports 18191/18192 de l'ancien test ne sont plus en écoute. Les ports candidats 18381/18382 ne sont pas en écoute au moment de ce relevé.

Proposition de ressources dédiées, **non réservées et à revalider** avant création :

| Ressource | Candidat | Vérification courante |
|---|---|---|
| Base PostgreSQL | `etat_civil_validation_isolated_20261106_0034` | L'absence a été vérifiée lors d'un contrôle précédent; elle doit être vérifiée de nouveau juste avant création. |
| Data dir / futur filestore | `data/validation_isolated_20261106_0034` | Chemin absent au contrôle courant; répertoire parent `data/` accessible en écriture. |
| Fichier de configuration isolé | `logs/implementation_odoo17/validation_isolated_20261106_0034.conf` | Absent au contrôle courant; répertoire de rapports accessible en écriture. |
| HTTP / gevent | 18381 / 18382 | Aucun listener détecté au contrôle courant; vérifier à nouveau immédiatement avant lancement. |
| Filtre DB | Correspondance exacte `^etat_civil_validation_isolated_20261106_0034$` | À configurer; aucun fichier n'a été créé. |

L'absence actuelle du dossier et du fichier de configuration, ainsi que l'état des ports, a été revérifiée par inspection locale en lecture seule. La disponibilité du nom de base ne l'a pas été à l'instant de rédaction; aucun processus ne peut donc la considérer comme réservée. Le rôle `odoo17` dispose du privilège `CREATEDB` selon le rapport d'accès PostgreSQL, mais le mode d'authentification HBA demeure inconnu.

## Procédure reproductible proposée — non exécutée

1. Recontrôler le nom de base dans le catalogue avec le rôle autorisé, sans afficher la liste des autres bases; arrêter si le nom existe ou si le contrôle échoue.
2. Recontrôler l'absence exacte du `data_dir` et du fichier de configuration, les droits d'écriture du parent, et l'absence de listener sur 18381/18382. Ne jamais réutiliser un chemin ou un port déjà présent.
3. Créer une configuration privée dédiée (permissions minimales), avec `db_host=127.0.0.1`, `db_port=5432`, le rôle d'application autorisé sans imprimer son secret, `dbfilter` épinglé à la base candidate, `data_dir` dédié, `http_port=18381`, `gevent_port=18382`, et planificateur désactivé pour ce banc de test. Vérifier son contenu sans afficher les secrets.
4. Créer uniquement la nouvelle base via l'installation Odoo ciblée (`odoo/odoo-bin -c <config-isolee> -d <base-neuve> --stop-after-init -i <modules-valides>`). Ne pas utiliser de dump ni restaurer une sauvegarde dans une base existante. Pour le module e-mail, préparer uniquement des logins synthétiques compatibles avant installation; ne pas inventer d'adresses pour des personnes réelles.
5. Consigner le résultat, vérifier que le filestore apparaît sous le `data_dir` dédié et que les processus n'écoutent que sur les ports prévus. N'ajouter les tests HTTP/navigateur que dans une étape suivante après contrôle de disponibilité.

Cette procédure est un plan, pas une preuve d'exécution. Aucun service existant n'a été arrêté, redémarré ou modifié. Aucun environnement Odoo neuf n'a été créé durant cette mission. Les contrôles ponctuels ne réservent ni le nom de base ni les ports; refaire toutes les vérifications immédiatement avant une exécution réelle.

## Exécution, preuves et limites

Commandes/actions de diagnostic : inspection locale `git status`; lecture des rapports/logs; vérification courante par `ss -ltn` des ports protégés et candidats; vérification d'absence des chemins candidats par `test -e`; vérification des versions par `venv/bin/python --version` et `venv/bin/python odoo/odoo-bin --version`. Aucun test Odoo/PostgreSQL d'écriture et aucun appel HTTP n'a été lancé dans cette mission.

Fichiers source, bases, filestores et services modifiés : aucun. Sauvegarde : sans objet. Ce rapport est nouveau; aucun document préexistant n'a été écrasé. Les ressources candidates restent à revalider.

**Statut : TERMINÉ MAIS NON TESTÉ** pour la procédure de préparation; l'environnement dédié lui-même n'est pas créé.

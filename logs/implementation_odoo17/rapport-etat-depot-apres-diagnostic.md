# Rapport — état du dépôt après diagnostic

Date/heure : 2026-11-06 00:52 EAT (+03:00). Racine : `/home/ulrich/tous_les_projet/stage_l3_odoo`. Branche : `main`. Odoo 17.0; Python 3.14.4 (`venv`); PostgreSQL 18.6 sur `127.0.0.1:5432`.

## État Git

Le dépôt était déjà fortement modifié avant la création des présents rapports. Le contrôle courant compte 5 entrées staged, 51 changements suivis dans l'arbre de travail et 4 824 entrées non suivies. Le relevé antérieur comptait 4 819 entrées non suivies; l'écart correspond aux cinq rapports créés ici. Ces catégories peuvent se chevaucher pour un même fichier; les modifications préexistantes n'ont pas été nettoyées, restaurées ou réécrites. Aucun commit ni push n'a été réalisé.

Les cinq documents créés pendant cette mission :

- `logs/implementation_odoo17/rapport-diagnostic-readtimeout.md`
- `logs/implementation_odoo17/rapport-acces-postgresql.md`
- `logs/implementation_odoo17/rapport-preparation-environnement-isole.md`
- `logs/implementation_odoo17/plan-tests-financiers-et-concurrence.md`
- `logs/implementation_odoo17/rapport-etat-depot-apres-diagnostic.md`

Les cinq noms ont été recherchés avant création et aucun fichier correspondant n'existait. Pas de sauvegarde nécessaire pour ces nouveaux fichiers. Aucun code, fichier de configuration existant, rapport existant, base, filestore ou service n'a été modifié.

## Activités et résultats

| Type | Vérification / commande | Résultat |
|---|---|---|
| Statique | `git status --short --untracked-files=normal` et statistiques Git | Changements existants conservés; inventaire ci-dessus. |
| Statique | Lecture de `rapport-validation-finale-phase-suivante.md`, rapports financier/concurrence, environnement et journal de régression | Les limites antérieures ont été reprises sans les présenter comme nouveaux tests. |
| Statique | Lecture de `phase-next-regression-http.log` et `custom_addons/etat_civil/tests/test_acte_workflow.py` | 13 ReadTimeout identifiés; 12 s de délai client; détails des routes et rôles, mais pas de request ID ni heure exacte de début d'appel. |
| PostgreSQL | Résultat historique de connexion catalogue en lecture seule et attributs de rôle; revue des limites d'accès HBA | `odoo17` est `CREATEDB`, pas superutilisateur; mode HBA inconnu. Aucune écriture de base dans cette mission. |
| Dynamique locale, lecture seule | `ss -ltn` sur ports protégés/candidats et `test -e` sur chemins candidats | Services existants toujours à l'écoute sur ports protégés; 18381/18382 libres au relevé; data dir et config candidates absents. |
| Environnement | `venv/bin/python --version`; `venv/bin/python odoo/odoo-bin --version` | Python 3.14.4; Odoo Server 17.0. |

Aucun test Odoo, requête HTTP, test navigateur, migration ou parcours comptable n'a été lancé. Aucune charge n'a été envoyée aux services actifs. Les 13 ReadTimeout ne sont pas expliqués; le mode d'authentification PostgreSQL n'est pas identifié. Le nom de base candidat n'est pas actuellement certifié absent et doit être revérifié immédiatement avant toute création.

## État consolidé

- Diagnostic ReadTimeout : **BLOQUÉ** pour la cause racine; aucune relance de régression.
- Accès PostgreSQL : connexion de lecture seule et privilège `CREATEDB` établis selon les contrôles antérieurs; authentification HBA exacte non établie.
- Environnement isolé : procédure prête mais **TERMINÉ MAIS NON TESTÉ**; base, filestore et serveur n'ont pas été créés.
- Tests financiers, navigateur et concurrence : planifiés, **non exécutés**.
- Statut global : **B — PARTIELLEMENT VALIDÉ**; pas de décision de préparation à la production.

## Conservation

Aucun service n'a été arrêté ou redémarré; aucune base existante n'a été modifiée; aucune sauvegarde n'a été restaurée; aucun secret, mot de passe ou cookie n'est reproduit. Les cinq documents listés ci-dessus sont les seuls fichiers créés explicitement par cette mission. Aucune sauvegarde de rapport préexistant n'a été requise puisqu'aucun n'a été édité.

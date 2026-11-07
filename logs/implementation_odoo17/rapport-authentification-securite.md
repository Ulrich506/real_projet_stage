# Rapport — sécurité de l’authentification e-mail

Date/heure : 2026-11-05 22:11 EAT (+03:00). Odoo 17.0, Python 3.14.4, PostgreSQL 18.6. Source : checkout du projet. Tests sur `etat_civil_phase_next_auth_20261105_01`, copie synthétique restaurée; aucun compte réel.

## Contrôles et changements

- `res.users.login` reste l’identifiant; `res.users.email` reste séparé. La normalisation existante supprime les espaces périphériques, préserve la partie locale et met le domaine en minuscules. Les écritures ORM/RPC et `_login` imposent le format e-mail.
- Ajout d’un `pre_init_hook` et d’un contrôle `pre-migrate.py` pour refuser une installation/mise à jour si un login actif est incompatible ou s’il existe une collision sensible à la casse. Le message ne donne ni login ni nom; il donne les nombres actif/inactif/collision. Aucun login n’est transformé.
- Les logins invalides inactifs sont conservés sans modification; leur réactivation exige une valeur compatible. Les comptes techniques actifs ne sont pas identifiables automatiquement : ils bloquent l’activation et doivent être classifiés avec le responsable.
- Version du module portée à `17.0.1.0.1`; migration pré-vérifie et post-migration crée l’index unique `lower(login)`.
- Limite : aucune règle e-mail n’est imposée aux comptes de service externes qui n’utilisent pas `res.users`; OAuth/SSO et récupération de mot de passe n’ont pas été parcourus.

## Preuves reproductibles

| Contrôle | Base/commande | Résultat | Statut |
|---|---|---|---|
| Installation avec login actif incompatible | `etat_civil_phase_next_auth_incompatible_20261105_02`, restauration neuve; `-i etat_civil_auth_email --stop-after-init --no-http` | Hook final refuse; diagnostic 1 actif invalide, 4 inactifs conservés, 0 collision, aucun login modifié. Log `phase-next-auth-final-incompatible.log`. | TERMINÉ ET TESTÉ |
| Installation compatible | Sur la même copie uniquement, compte synthétique admin renommé `synthetic-admin@example.test` par ORM, sans toucher au mot de passe; install avec `--test-enable --test-tags /etat_civil_auth_email` | 7 post-tests; 0 ERROR/FAIL; index posé. Log `phase-next-auth-compatible-install.log`. | TERMINÉ ET TESTÉ |
| Mise à jour | Même DB, `-u etat_civil_auth_email --test-enable --test-tags /etat_civil_auth_email` | 7 post-tests; 0 ERROR/FAIL; pré-migration franchie, log `phase-next-auth-upgrade.log`. | TERMINÉ ET TESTÉ |
| Connexion HTTP positive après mise à jour | Aucun mot de passe synthétique connu n’a été utilisé pour ce test | Non exercée. | BLOQUÉ |
| Connexion invalide HTTP | Base financière synthétique décrite dans le rapport API; login non-e-mail et secret fictif | HTTP 401, réponse générique `Identifiants invalides.` | TERMINÉ ET TESTÉ |
| Comptes humains réels / migration réelle | Aucune base réelle | Suspendue; aucun compte modifié. | EN ATTENTE DE VALIDATION MÉTIER |

Commandes additionnelles : `venv/bin/python odoo/odoo-bin ...` comme indiqué dans les logs; contrôle de syntaxe par `PYTHONPATH=.../odoo venv/bin/python -m compileall -q ...`. Aucun mot de passe, hash, cookie ou jeton n’a été écrit dans le rapport.

## Conclusion

Le garde-fou d’activation est corrigé et deux scénarios installation/mise à jour sont prouvés sur une base synthétique. L’authentification positive n’a pas été reproduite sur cette instance dans cette phase; pas de migration réelle. Statut global de composant : BLOQUÉ pour la connexion positive, TERMINÉ ET TESTÉ pour les hooks et règles ORM.

# Rapport de diagnostic — 13 ReadTimeout HTTP

Date/heure du relevé : 2026-11-06 00:52 EAT (+03:00). Les traces analysées datent du 2026-11-05, entre 18:53 et 18:56 EAT. Instance de test : Odoo 17.0, base synthétique `etat_civil_phase_next_finance_20261105_01`, processus de test PID 560655, client et serveur HTTP temporaires sur `127.0.0.1:18191`; gevent prévu sur 18192. Python 3.14.4 (`venv`). Modules : `etat_civil`, `etat_civil_auth_email`, `etat_civil_account`.

## Constat

La suite HTTP complète rapporte 96 post-tests et 13 exceptions `requests.exceptions.ReadTimeout`; la commande s'est terminée avec le code 1. Chaque exception indique `read timeout=12` sur la boucle locale 127.0.0.1:18191. La requête a donc été envoyée mais aucun en-tête/résultat HTTP n'a été reçu avant le délai de lecture. Le journal ne fournit ni statut HTTP, ni corps de réponse, ni identifiant de requête. Le début exact de chaque appel HTTP n'est pas journalisé. Les heures ci-dessous sont celles de démarrage du test englobant, pas des heures certifiées de début de requête.

| # | Test / heure de début du test (EAT) | Requête concernée | Rôle | Observation |
|---|---|---|---|---|
| 1 | `test_api_accepts_valid_piece_images_and_infers_mimetype`, 18:53:48.169 | POST `/api/v1/actes/naissance/<id>` (image justificative) | Agent | ReadTimeout, 12 s configurées |
| 2 | `test_api_allows_agent_correction_and_rejects_direct_civil_status_changes`, 18:54:00.482 | POST `/api/v1/actes/naissance/<id>` (correction) | Agent | ReadTimeout |
| 3 | `test_api_health_does_not_disclose_the_database_name`, 18:54:13.177 | GET `/api/v1/health` | Anonyme | ReadTimeout |
| 4 | `test_api_logout_requires_json_post`, 18:54:25.198 | GET `/api/v1/auth/logout` | Agent | ReadTimeout |
| 5 | `test_api_mutations_reject_json_sent_as_plain_text`, 18:54:37.237 | POST `/api/v1/personnes` | Agent | ReadTimeout |
| 6–8 | `test_api_rejects_invalid_piece_images_without_partial_updates`, 18:54:49.274 | Deux POST `/api/v1/actes/naissance/<id>` (images invalides), puis POST `/api/v1/actes/naissance` | Agent | Trois ReadTimeouts séquentiels; l'heure de départ de chaque appel n'est pas tracée |
| 9 | `test_attachment_preview_route_respects_civil_centre_access`, 18:55:25.527 | GET `/web/content/<attachment_id>?download=false` | Agent | ReadTimeout |
| 10 | `test_authenticated_api_routes_reject_anonymous_writes`, 18:55:37.797 | POST `/api/v1/auth/logout` | Agent | ReadTimeout |
| 11–13 | `test_specific_api_routes_enforce_the_workflow_for_each_act_type`, 18:55:49.836 | POST `/api/v1/actes/{naissance,mariage,deces}/<id>/valider` | Officier | Une requête par type; trois ReadTimeouts |

Les appels HTTP échoués n'ont produit aucun code HTTP ni corps de réponse. Aucun request ID n'était ajouté par les tests ou retrouvé dans les traces. La réussite de l'authentification synthétique Agent juste avant la première erreur réduit la probabilité d'un échec général d'authentification, sans exclure un problème de session sur une requête donnée. Le health anonyme échoue lui aussi; une cause exclusivement liée au rôle est donc insuffisante.

## Causes évaluées

| Hypothèse | Éléments disponibles | Conclusion |
|---|---|---|
| Saturation serveur / worker bloqué | Port de test à l'écoute dans le relevé antérieur; aucune corrélation requête-worker exploitable dans le journal client. | Cause possible, non démontrée. |
| SQL long / attente de verrou PostgreSQL | Aucun SQLSTATE, deadlock ou lock timeout identifié dans le journal de régression consulté. Aucune trace PostgreSQL horodatée et corrélée aux 13 appels n'est conservée. | Non établi; impossible à exclure. |
| Authentification / session | L'authentification synthétique précédente réussit; des appels anonymes et authentifiés échouent. | Peu probable comme cause unique, non exclu. |
| Délai trop court | Le client a un délai de lecture de 12 secondes; rien ne prouve qu'augmenter ce délai corrigerait le blocage. | Ne pas augmenter avant diagnostic. |
| Réseau local | Destination loopback; le client attend une réponse. | Une panne réseau externe est peu probable; blocage serveur ou chemin local reste possible. |

Un ancien message de timeout worker consigné dans `odoo-regression-server.log` concerne le port 18177 et une autre exécution; il ne peut pas être attribué à cette base ou aux appels sur 18191. Le journal de test n'inclut pas les lignes d'accès Werkzeug corrélées. En conséquence, **la cause racine des 13 erreurs reste inconnue** et aucun nouveau lot de requêtes n'a été lancé.

## Preuves et exécution

- Source principale : `logs/implementation_odoo17/phase-next-regression-http.log`; références de tests dans `custom_addons/etat_civil/tests/test_acte_workflow.py` (lignes 392–705).
- Vérifications de cette mission : lecture du journal et du code de test, extraction des 13 traces `ReadTimeout`, contrôle de l'absence de réponse HTTP et recherche de messages de timeout/erreur associés. Aucun test dynamique ni appel HTTP n'a été relancé.
- Résultat antérieur : les 96 post-tests sont allés jusqu'au résumé, mais le processus a échoué avec 13 erreurs; ils ne constituent pas une suite verte.
- Limite : les journaux Odoo et PostgreSQL côté serveur n'ont pas de marqueur de corrélation permettant d'associer une requête à un worker, une transaction et une requête SQL.
- Fichiers source modifiés : aucun. Sauvegarde : sans objet. Ce rapport est nouveau; aucun fichier antérieur n'a été écrasé.

**Statut : BLOQUÉ** pour l'explication causale et la validation de la régression HTTP.

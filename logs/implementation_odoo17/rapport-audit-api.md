# Rapport — audit des endpoints API

Date/heure : 2026-11-05 22:11 EAT (+03:00). Odoo 17.0, Python 3.14.4. Revue statique du contrôleur `custom_addons/etat_civil/controllers/main.py`; tests HTTP sur la base synthétique restaurée `etat_civil_phase_next_finance_20261105_01`, port 18191, processus temporaire de cette base uniquement.

## Changement et test HTTP

- `/api/v1/health` ne renvoie plus le nom de la base, seulement statut et service.
- `/api/v1/auth/login` n’inclut plus `session_id` dans le JSON; Odoo garde le mécanisme standard de cookie de session. Aucune référence de client dans ce dépôt n’utilisait `session_id`.
- Le login utilise `request.db`, refuse une base caller-supplied différente et retourne une erreur générique en cas d’identifiants invalides.
- Requête anonyme réelle `GET /api/v1/health` sur `http://127.0.0.1:18191`: HTTP 200, JSON `{"status":"ok","service":"etat_civil_api"}` (preuve `proofs/phase-next-health.json`, headers associés).
- Requête réelle `POST /api/v1/auth/login` avec login au format invalide et mot de passe fictif : HTTP 401, `{"error":"Identifiants invalides."}` (preuve `proofs/phase-next-login-reject.json`; les headers ne contiennent pas les valeurs envoyées).
- Réponses enregistrées sans cookies/session et sans données d’identité.

## Analyse statique / limites

Les routes de mutation sont déclarées `auth='user'`, souvent `csrf=False`; les contrôleurs exigent un corps JSON, réduisant le risque de requête HTML cross-site classique, mais ce n’est pas un audit dynamique complet CSRF/CORS/cookies. Endpoint public de vérification QR utilise `sudo()` pour une réponse limitée aux informations de vérification; risque d’énumération et politique confidentialité restent à évaluer. Les routes health/login/logout sont publiques par conception. Les endpoints médias et rapports doivent encore être testés par utilisateur authentifié et accès URL direct.

| Contrôle | Statut |
|---|---|
| Health n’expose plus le nom DB; test HTTP 200 | TERMINÉ ET TESTÉ |
| JSON login n’expose plus le session_id; revue source | TERMINÉ MAIS NON TESTÉ |
| Erreur login invalide générique; test HTTP 401 | TERMINÉ ET TESTÉ |
| Connexion positive API après changement | BLOQUÉ |
| Revue CSRF/CORS/session de toutes routes | NON IMPLÉMENTÉ |
| Contrôle dynamique de chaque endpoint public et média | NON IMPLÉMENTÉ |

Le HTML health/login n’a pas exposé de secret pendant les essais. La suite HTTP complète a échoué sur 13 délais d’attente lors de `HttpCase`; voir rapport financier, donc pas de couverture globale API déclarée.

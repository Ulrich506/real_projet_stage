# Rapport — tests Chromium

Date/heure : 2026-11-05 22:11 EAT (+03:00). Odoo 17.0; base synthétique `etat_civil_phase_next_finance_20261105_01`; instance locale temporaire HTTP 18191, gevent 18192. Aucun service existant n’a été redémarré.

## Réalisé

- Chromium disponible : `/usr/bin/google-chrome`.
- Page `http://127.0.0.1:18191/web/login` rendue en headless, fenêtre 1280 × 900. Capture : `logs/implementation_odoo17/proofs/phase-next-login-page.png`.
- Inspection visuelle de la capture : champ libellé et placeholder « Adresse e-mail »; page login Odoo visible. Aucun document personnel n’est affiché.
- Une requête HTTP directe vers health et une requête login invalide sont décrites dans `rapport-audit-api.md`.
- Serveur de test temporaire arrêté après capture et requêtes. Ports existants 8071, 18071/18072, 18181/18182, 18183/18184 et 18205 non arrêtés.

## Non exécuté

Aucune session Chromium authentifiée Agent, Officier, Régisseur ou Administrateur : aucune paire d’identifiants synthétiques autorisée n’était disponible pour cette DB, et aucun mot de passe n’a été deviné. Aucun menu, formulaire, paiement, génération de rapport ou accès direct PDF authentifié n’a été manipulé.

| Parcours | Statut |
|---|---|
| Rendu visuel de la page login et label e-mail | TERMINÉ ET TESTÉ |
| Authentification Chromium par rôle | BLOQUÉ |
| Parcours demande de copie par rôle | NON IMPLÉMENTÉ |
| PDF direct payé/non payé et accès inter-centres | NON IMPLÉMENTÉ |

La capture prouve le rendu, pas l’authentification ni les permissions de navigation.

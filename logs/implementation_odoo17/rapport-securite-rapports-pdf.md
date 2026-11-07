# Rapport — sécurité des rapports et PDF

Date/heure : 2026-11-05 22:11 EAT (+03:00). Odoo 17.0 / Python 3.14.4. Revue de sources et mise à jour de l’addon seulement sur la base synthétique `etat_civil_phase_next_finance_20261105_01`; aucune base active ou de revue utilisée en écriture.

## Constat

Les actions QWeb naissance, mariage et décès dans `custom_addons/etat_civil/reports/actes_reports.xml` sont liées aux modèles d’actes et leur `groups_id` autorise Agent, Officier et Administrateur. Leurs templates contiennent les données de l’acte. Elles ne reçoivent pas de contexte de demande de copie ni de paiement. L’avis dans le rapport indique une impression de vérification/signature physique pour les états non validés et « Extrait validé » pour les actes validés; cela ne suffit pas à déterminer le statut légal du PDF délivré.

Le rapport `etat_civil_account.copy_document` vérifie droits d’accès, règle centre, statut autorisé/délivré, état financier et acte avant rendu. Dans cette intervention, le garde-fou a été renforcé pour refuser aussi un acte qui n’est plus validé/rectifié. La méthode action et le rendu QWeb appellent cette vérification serveur. Les routes directes des rapports civils n’ont pas été retirées ou changées, car il faut une décision métier sur « document interne » vs « copie officielle » et préserver le travail administratif.

| Rôle | Consultation/impression interne observée | Délivrance officielle |
|---|---|---|
| Agent | Groupes présents sur les trois actions; URL directe non testée cette phase. | Doit passer par demande autorisée; routes civiles legacy demeurent un risque tant que la classification n’est pas décidée. |
| Officier compétent | Groupes présents; URL directe non testée cette phase. | Selon workflow de demande; hors rôle financier. |
| Régisseur | Pas dans les groupes des trois rapports civils. | Confirmation financière seule ne fournit pas le document. |
| Administrateur | Groupes présents; règles d’accès administrateur applicables. | Selon règles métier, sans supprimer la trace. |

## Vérifications / preuves

- Revue statique des quatre actions QWeb et de `report/copy_document.py`.
- Mise à jour `etat_civil_account` et 5 tests ciblés; 0 erreur/échec. Ce résultat n’est pas un test de PDF ou d’URL.
- Chromium headless a affiché la page de login de l’instance synthétique sur 18191; capture `proofs/phase-next-login-page.png`. Aucun PDF d’acte ni rapport de copie n’a été obtenu ou contrôlé visuellement.
- Pas de requête directe `/report/pdf/...` avec utilisateur authentifié/non autorisé, aucun rapport d’acte généré pendant cette phase.

| Contrôle | Statut |
|---|---|
| Garde serveur du rapport de copie et acte validé à nouveau au rendu | TERMINÉ MAIS NON TESTÉ |
| Rapports d’acte directs / contrôle par URL | EN ATTENTE DE VALIDATION MÉTIER |
| Équivalence juridique PDF d’acte vs copie destinée au citoyen | EN ATTENTE DE VALIDATION MÉTIER |
| Téléchargement non autorisé / inter-centres / cas paiement | NON IMPLÉMENTÉ |

Risque résiduel ÉLEVÉ : un rapport civil direct pourrait fournir les mêmes informations qu’une copie si les rapports sont juridiquement délivrables. Aucune modification n’a été faite aux rapports legacy sans classification approuvée.

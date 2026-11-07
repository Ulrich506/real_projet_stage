# Tests de bout en bout — état final

Les scénarios ci-dessous distinguent les parcours vraiment effectués des suites ORM. Environnement de test uniquement; aucune donnée métier réelle utilisée.

## Authentification synthétique réellement exercée par HTTP

Base restaurée `etat_civil_restore_validation_20261105_01`, instance `127.0.0.1:18183` / gevent `18184`. Quatre utilisateurs synthétiques `@example.test` créés dans cette copie restaurée, avec mots de passe aléatoires temporaires non enregistrés dans les rapports. Chaque compte a obtenu HTTP 200 sur `/api/v1/auth/login`, puis HTTP 200 sur `/api/v1/auth/me` avec uid concordant et rôle attendu.

| Rôle synthétique | Login HTTP | `/auth/me` | Résultat |
|---|---:|---:|---|
| Agent | 200 | 200; `is_agent=true` | VALIDÉ — API, pas navigateur |
| Officier | 200 | 200; `is_officier=true` | VALIDÉ — API, pas navigateur |
| Administrateur | 200 | 200; `is_admin=true` | VALIDÉ — API, pas navigateur |
| Régisseur | 200 | 200; rôle dédié absent de la réponse mais compte authentifié | PARTIEL |

Aucun identifiant réel n’a été utilisé. Les logs HTTP ne contiennent pas le corps de requête ni le mot de passe.

## Tests automatisés relancés après correction des verrous

- Base : `etat_civil_final_audit_tests_20261105`, restaurée depuis l’archive synthétique `etat_civil_dev_regression_20261105_pre_finance_retest.zip`, puis `etat_civil` et `etat_civil_account` mis à jour uniquement dans cette copie.
- Test ciblé passerelle : 5 post-tests, 0 échec/erreur; le compteur de stats du module indique 7.
- Régression conjointe : 96 post-tests, 0 échec/erreur; statistiques de classe Odoo : 105 `etat_civil`, 7 `etat_civil_account`.
- Logs : `odoo-final-audit-tests.log` et `odoo-final-audit-regression.log`.
- La suite valide les cas ORM présents (état non modifiable directement, demande liée à un acte, tarif négatif, confirmation sans rôle, etc.). Elle ne simule pas une course concurrente entre transactions.

## Parcours métier non réalisés

| Parcours | Résultat réel | Statut |
|---|---|---|
| A — acte synthétique, tarif gratuit, demande, autorisation, PDF et historique | Pas d’acte/demande synthétique créé dans ce parcours; pas de rendu PDF. | NON TESTÉ |
| B — tarif payant, facture brouillon/postée, paiement, rapprochement, régisseur, PDF | Aucun journal/compte/produit/taxe de test configuré pour un parcours financier; aucune facture/paiement créé. | NON TESTÉ |
| C — Agent/Officier/Régisseur attaquant méthodes, RPC et autre centre | Couverture partielle par tests ORM; aucun parcours HTTP complet, aucune demande financière inter-centres. | PARTIEL |
| D — annulation, note de crédit, remboursement, contestation après délivrance | Flux lié au remboursement non implémenté ni exécuté. | NON TESTÉ / PARTIEL |
| Web Chromium après connexion | Capture existante de page login seulement; pas de session Chromium authentifiée. | NON TESTÉ |
| Téléchargement direct du rapport copie payé/non payé | Le guard de rapport est en code; aucun test HTTP direct des rapports. Les rapports civils originaux restent accessibles séparément. | NON TESTÉ; RISQUE |

Les tests unitaires verts ne sont pas une preuve de facturation, paiement, reçu, remboursement ou délivrance réels. Le POS est désinstallé et demeure facultatif/non testé.

Contrôle ORM après ces connexions : les quatre comptes synthétiques ont chacun le groupe attendu. Cela valide leur affectation de groupe, pas les opérations autorisées/interdites sur des actes ou écritures comptables.

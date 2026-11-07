# Validation finale — Odoo 17

Date : 2026-11-05. Résultat : **B — PARTIELLEMENT VALIDÉ**. Aucun critère ne permet de qualifier le projet de prêt pour la production.

## Environnement contrôlé

- Checkout : `/home/ulrich/tous_les_projet/stage_l3_odoo/`, Odoo 17 du dépôt. Python configuré : 3.14.4; PostgreSQL : 18.6, selon l’audit précédent.
- Base déjà en service contrôlée sans modification : `etat_civil_dev_latest_20261105`, ports 18181/18182; `/api/v1/health` répond 200 et identifie cette base.
- Restauration d’essai : `etat_civil_restore_validation_20261105_01`, ports 18183/18184, filestore indépendant sous `data/implementation_odoo17_dev/filestore/etat_civil_restore_validation_20261105_01`.
- Tests d’upgrade : `etat_civil_final_audit_tests_20261105`, base synthétique restaurée, mise à jour effectuée uniquement sur cette base.
- Les ports protégés 8071, 18071/18072, 18205 n’ont pas été arrêtés ni modifiés. Les bases active/revue n’ont pas été ciblées.

## Résultats

| Composant | Statut | Preuve / limite |
|---|---|---|
| `etat_civil` | TERMINÉ ET TESTÉ (régression automatisée) | 96 post-tests avec les tests de la passerelle, 0 échec/erreur; le compteur de classe Odoo affiche 105 pour `etat_civil`. Cela ne vaut pas validation de chaque parcours humain. |
| `etat_civil_auth_email` | PARTIEL | Tests ORM et syntaxe réussis dans les suites précédentes. Quatre comptes synthétiques se sont authentifiés par HTTP/API et ont atteint `/api/v1/auth/me`; aucun login navigateur Chromium, compte réel, récupération de mot de passe ou OAuth testé. |
| `etat_civil_account` | PARTIEL | Installation/upgrade et 5 tests de passerelle exécutés sur la nouvelle base; 0 échec/erreur. Aucun acte, tarif réel, facture, paiement, reçu, remboursement ou PDF payé créé. |
| API d’authentification | PARTIEL | Réponses HTTP génériques aux identifiants incorrects; authentifications synthétiques positives via API; pas de test complet anti-CSRF/API externe. |
| Sauvegarde/restauration | VALIDÉE pour cet essai synthétique | Archive ZIP vérifiée, restaurée sous un nom neuf, 43 pièces stockées vérifiées sans objet manquant, registre chargé, endpoint santé 200. |
| Comptabilité de commune | NON TESTÉ | Journaux, comptes, taxes, devises, produits et politique de rapprochement réels non configurés. |
| Migration des utilisateurs réels | EN ATTENTE | Aucun compte réel inventorié ou modifié; aucune adresse inventée; aucun mot de passe/hash touché. |

## Corrections effectuées pendant cet audit

Après sauvegarde exacte du fichier dans `backups/source-before-final-audit/copy_request.py`, les actions `action_submit` et `action_deliver` verrouillent maintenant la ligne de demande et rechargent son état avant transition. La soumission conserve aussi le verrou de l’acte pour séquencer l’attribution de la première copie. Cela ferme le chemin évident de double transition concurrente dans ces méthodes. La suite automatisée complète a été relancée après cette modification, mais aucun test multithread dédié à cette course n’existe encore.

Aucun autre code métier n’a été modifié pendant cet audit. Les rapports finaux consignent les risques non résolus plutôt que d’affirmer que les parcours incomplets fonctionnent.

## Anomalies et blocages

1. **Élevé — risque de verrouillage d’administration à l’installation** : l’authentification refuse tout login non e-mail, tandis que le hook d’installation ne vérifie que les doublons, pas les anciens logins invalides. Un compte standard nommé `admin` ne peut donc plus ouvrir une nouvelle session après activation. Migration réelle ou précontrôle d’installation obligatoire.
2. **Élevé — frontière de délivrance ambiguë** : les trois rapports QWeb directs du module civil restent accessibles aux rôles Agent/Officier/Admin sans demande de copie ni contrôle de paiement. Si ces PDF sont équivalents à la copie délivrée, ils contournent la passerelle; s’ils sont uniquement des impressions internes de registre/signature, cette distinction doit être formellement documentée et testée.
3. **Élevé — intégrité du montant** : le montant de la demande provient du tarif, tandis que la facture utilise les taxes du produit et la devise/journal comptables. Aucun contrôle ne compare explicitement la devise, le partenaire et le total de facture à la demande avant confirmation. Paiement complet de la facture ≠ preuve que le tarif affiché était le bon.
4. **Moyen — session API** : `/api/v1/auth/login` renvoie aussi `session_id` dans le JSON alors que la session Odoo est déjà portée par le cookie. Revoir ce contrat et limiter l’exposition du jeton.
5. **Moyen — santé publique** : `/api/v1/health` est public et révèle le nom exact de la base via `request.db`.
6. Les reçus, remboursements, avoirs, tableau de bord Régisseur, rapprochement bancaire de la commune, authentification réelle Chromium et contrôles inter-centres de la passerelle restent non testés ou non implémentés.

## État des données et services

Aucune base active/revue, aucun compte réel, aucune facture métier et aucun paiement réel n’a été modifié. Quatre comptes synthétiques ont été créés uniquement dans la base restaurée d’essai afin de tester l’authentification; leurs secrets temporaires ne figurent pas dans les rapports. Le serveur de restauration reste disponible sur 18183/18184. Les changements Git antérieurs ont été conservés; aucun commit, push, reset ou clean n’a été exécuté.

# Rapport d’implémentation Odoo 17 — 2026-11-05

## Résumé exécutif

**B — PARTIELLEMENT VALIDÉ.** Un environnement Odoo de développement synthétique indépendant est en fonctionnement. Le module `etat_civil_auth_email` et la passerelle `etat_civil_account` ont été créés, installés dans des bases de test; les tests ciblés passent. La suite de régression du module civil passe. L'API login a été verrouillée à la DB filtrée par Odoo.

Les conditions de réussite globale ne sont pas réunies : aucun utilisateur réel n'a été migré ou authentifié, aucun flux facture/paiement/délivrance n'a été exercé en bout en bout, la configuration comptable de la commune manque, aucun tableau de bord Régisseur ni écran de reçus n'est livré, et les tests financiers directs/Chromium authentifiés sont en attente.

## Versions et environnement

Odoo 17.0, Python 3.14.4, PostgreSQL 18.6, venv du projet; `pip check` sain. Base finale de test `etat_civil_dev_latest_20261105`, filestore correspondant sous `data/implementation_odoo17_dev/filestore/etat_civil_dev_latest_20261105`. Serveur final HTTP 18181/gevent 18182. Les ports 8071, 18071/18072 et 18205 n'ont pas été stoppés/redémarrés. Aucun accès en écriture aux DB actives/revue.

## Implémentations

- `custom_addons/etat_civil_auth_email/`: validation d'identifiant e-mail côté ORM et `_login`, trim et domaine normalisé, unicité case-insensitive avec index, champ QWeb type email. Le champ contact reste distinct.
- `custom_addons/etat_civil_account/`: tarifs, demande de copie sur liens typés naissance/mariage/décès, lien à Account, conditions paiement côté serveur, rôle Régisseur, historique append-only, blocage/contrôle du rapport direct.
- `custom_addons/etat_civil/controllers/main.py`: route API login ne peut plus sélectionner une DB arbitraire ni utiliser le fallback codé en dur. Snapshot source pré-correction conservé.

## Résultats vérifiés

- Tests ciblés finaux sur DB fraîche: log Odoo `0 failed, 0 error(s) of 12 tests`; tests stats 9 auth et 7 finance (compteurs Odoo incluant regroupements/sous-tests).
- Régression `etat_civil`: 91 post-tests, statistiques Odoo 105, `0 failed, 0 error(s)`.
- Registry final : `account`, `account_payment`, `product`, `account.move`, `account.move.line`, `account.payment`, `etat_civil`, les deux nouveaux addons installés; POS désinstallé.
- HTTP `/web/login` et `/api/v1/health` : 200; le formulaire porte un champ Adresse e-mail type email. API login syntaxe invalide et DB différente renvoient le même 401 générique. Capture Chromium non authentifiée disponible.
- Sauvegardes synthétiques Odoo ZIP créées, testées par `unzip -tq`, mode 600; elles incluent le filestore correspondant. Restauration réelle non testée.

## Anomalies rencontrées pendant validation

- Première installation de `etat_civil_account` refusée par Odoo car la vue ne contenait pas le champ `company_id` référencé dans le domaine de `partner_id`; champ invisible ajouté, puis installation et tests réussis.
- Première suite email: une assertion a révélé que le validateur Odoo acceptait `@example.org`; contrôle explicite local-part/domaine ajouté, puis répétition réussie.
- Installation de test initiale a tenté de lier le port HTTP déjà pris par le premier serveur dev; aucun service n'a été arrêté; la configuration de test a été isolée sur son propre port.
- Installation de base Odoo émet deux avertissements Docutils de mise en forme du README d'`etat_civil`; ces avertissements n'empêchent pas le chargement.
- `report/copy_document.py` revalide autorisation et paiement au rendu; aucune génération PDF/demande réelle n'a encore été effectuée, donc cette protection reste à éprouver en test HTTP authentifié.

## Utilisateurs / migration

La seule base inventoriée est neuve et comporte cinq comptes Odoo par défaut (1 actif, 4 archivés), pas les comptes métier de la commune. Aucune ligne de migration préparée à partir d'un login/contact réel; 0 compte modifié, 0 adresse inventée, 0 mot de passe/hash modifié. Authentification réussie avec un compte réel : NON TESTÉE.

Dans la DB vierge dotée de la règle stricte, les logins Odoo par défaut non-e-mail sont refusés; aucun login interactif n'a donc été effectué. L'instance répond HTTP et rend la page de connexion, mais ce n'est pas une preuve d'authentification réussie.

## Limites et travaux restants

- Les comptes humains et comptes techniques réels doivent être inventoriés et les e-mails confirmés avant activation sur une base réelle; aucun import/migration de données effectué.
- La règle métier première copie gratuite et les tarifs exacts restent à confirmer par la commune.
- Configurer un plan comptable/journal/taxes et tester facture postée, paiement rapproché, option rapprochement bancaire, annulation/avoir/remboursement, confirmation régisseur, délivrance PDF et URL directe.
- Compléter les écrans de reçus et dashboard Régisseur; tester rôles/centres authentifiés, import/API et navigation Chromium avec sessions autorisées.
- Tester restauration base+filestore dans une nouvelle DB et documenter le runbook réel.
- Les erreurs Docutils du README du module (indentation et citation) ont été observées pendant installation, sans bloquer Odoo.

**État final : PARTIEL.** Les implémentations sont distinctes des fonctions réellement exercées; seules les preuves listées ci-dessus sont déclarées validées.

## Complément d’audit final

Le 2026-11-05, les transitions de soumission/délivrance de `etat_civil_account` ont été renforcées par verrouillage de ligne. Les tests combinés relancés après ce changement sur `etat_civil_final_audit_tests_20261105` sont à 96 post-tests, sans échec/erreur. Une restauration d’essai a été démarrée et quatre logins synthétiques ont réussi via l’API HTTP. Ces résultats ne remplacent pas les parcours facture/paiement/PDF, le navigateur authentifié ni une migration réelle.

Risques de mise en production relevés : comptes historiques invalides pouvant être bloqués par le login e-mail; rapports originaux du module civil accessibles sans passer par la demande payante; absence de comparaison serveur explicite du total/devise/partenaire de facture avec le montant de demande; remboursements et avoirs non intégrés au workflow. Détails dans `rapport-validation-finale.md` et `rapport-securite-finale.md`. Statut maintenu : **B — PARTIELLEMENT VALIDÉ**.

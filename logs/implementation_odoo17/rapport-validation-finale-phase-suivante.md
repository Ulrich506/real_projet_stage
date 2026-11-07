# Rapport de validation finale — phase suivante

Date/heure : 2026-11-05 22:11 EAT (+03:00). Statut global : **B — PARTIELLEMENT VALIDÉ**. Environnement : checkout Odoo 17.0; Python 3.14.4; PostgreSQL 18.6. Les tests d’écriture de cette phase ont ciblé des bases synthétiques neuves/restaurées uniquement.

## Résumé des résultats

| Domaine | Résultat |
|---|---|
| Auth e-mail | Pré-init refuse une base avec identifiant actif non e-mail; install et upgrade compatibles ont chacun exécuté 7 tests sans erreur. Comptes inactifs non conformes conservés. Connexion positive HTTP/browser non refaite. |
| Comptabilité | Garde de concordance facture/demande et paiement renforcé; addon mis à jour et 5 tests ciblés sans erreur. Aucune facture/paiement/avoir E2E créé. |
| Régression civile/API | Exécution complète de 96 post-tests a terminé avec 13 erreurs ReadTimeout dans HttpCase; ne pas revendiquer succès. 105 stats civiles, 7 compte module affichées; la suite n’est pas verte. |
| API publique | Health HTTP 200 sans nom de base; login invalide HTTP 401 générique; le JSON ne renvoie plus `session_id` selon code. |
| PDF / délivrance | Rapport de copie garde serveur renforcé; rapports directs d’acte restent accessibles aux groupes existants; classification juridique à décider. Tests URL/PDF manquants. |
| Concurrence | Verrous présents/revus, annulation verrouillée; aucune transaction réellement concurrente. |
| Chromium | Page login ouverte et capturée; pas de session authentifiée par rôle. |
| Restauration | Archive synthétique restaurée sous nouvelle base; 43 pièces stockées, 0 objet filestore absent. Aucun restore sur base existante. |

## Bases, ports et preuves

- Auth : `etat_civil_phase_next_auth_20261105_01` (installation compatible après modification ORM d’un compte synthétique) et `etat_civil_phase_next_auth_incompatible_20261105_02` (installation refusée sur login actif invalide); logs `phase-next-auth-final-incompatible.log`, `phase-next-auth-compatible-install.log`, `phase-next-auth-upgrade.log`.
- Finance/régression : `etat_civil_phase_next_finance_20261105_01`, filestore `data/implementation_odoo17_dev/filestore/etat_civil_phase_next_finance_20261105_01`; archive source `backups/etat_civil_dev_regression_20261105_pre_finance_retest.zip`, SHA 61ac9b97e9f32b4f622b45b58e524f8685009557c76c2b65e04d4269cc0903d6; logs `phase-next-finance-final-tests.log`, `phase-next-regression-http.log`, `phase-next-regression-correct-db.log`.
- Essai HTTP/Chromium : 18191/18192, processus propre à la base synthétique terminé; capture et réponses dans `proofs/phase-next-*`.
- Services préexistants : 8071, 18071/18072, 18181/18182, 18183/18184, 18205 toujours en écoute lors du contrôle après essai. Aucun d’eux redémarré.

Commandes clés : `unzip -tq` sur trois archives; `venv/bin/python odoo/odoo-bin ... -i/-u ... --test-enable`; `compileall`; `xmllint --noout`; `curl` endpoints de test; Chromium headless screenshot; audit ORM en lecture seule des objets filestore. Les sorties détaillées sont dans les logs cités.

## Modifications cette phase

- `etat_civil_auth_email`: pre-init et pre-migrate, diagnostic agrégé et migration index unique, version `17.0.1.0.1`.
- `etat_civil_account`: snapshots du prix/produit/taxes, concordance facture, paiement prouvé par partial reconciliations de la facture même, blocage note de crédit et contrôle de l’état de l’acte; verrou d’annulation.
- `etat_civil/controllers/main.py`: suppression du nom DB public et session_id JSON.
- `etat_civil/tests/test_acte_workflow.py`: assertion health sans clé database.
- Aucune migration d’utilisateurs réels; aucun compte, facture ou paiement de production/revue modifié.

## Décision

Pas de mise en production. Préconditions restantes : parcours comptable E2E avec configuration fictive, concurrence multi-transaction, validation des rapports officiels/interne par métier puis tests directs, authentification Chromium de comptes synthétiques, remboursement et régression HTTP verte. Aucun commit/push réalisé. Les changements Git préexistants ont été conservés.

## Addendum d’inventaire et de validation en lecture seule — 2026-11-05 23:25 EAT (+03:00)

### Décision de sécurité

Aucune base, aucun filestore et aucun service n’a été modifié, créé, arrêté ou redémarré pendant cet addendum. Une vérification en lecture seule du catalogue PostgreSQL avec le compte configuré n’a pas permis de lister les bases (`ProgrammingError`). Comme l’absence d’un nouveau nom de base ne peut donc pas être prouvée, les tests dynamiques, migrations, tests navigateur authentifiés et tests multi-transaction demandés sont **BLOQUÉS**. Aucune base existante n’a été réutilisée.

### Inventaire constaté

| Port(s) | Configuration/processus observé | Base / filestore | Action |
|---|---|---|---|
| 8071 | `config/odoo17.conf`, processus Odoo actif; base non épinglée dans ses arguments | Non identifiés sans accès au service ou au catalogue | Non utilisé; port protégé |
| 18071/18072 | `/tmp/etat_civil_isolated_review.conf`, processus actif | `etat_civil_final_review_20261105_1304`; `data/filestore/etat_civil_final_review_20261105_1304` | Non utilisé; ports protégés |
| 18181/18182 | `/tmp/etat_civil_dev_latest_server_20261105.conf`, processus actif | `etat_civil_dev_latest_20261105`; `data/implementation_odoo17_dev/filestore/etat_civil_dev_latest_20261105` | Non utilisé; instance de test déjà en service |
| 18183/18184 | `/tmp/etat_civil_restore_validation_20261105_01.conf`, processus actif | `etat_civil_restore_validation_20261105_01`; `data/implementation_odoo17_dev/filestore/etat_civil_restore_validation_20261105_01` | Non utilisé; instance de validation déjà en service |
| 18205 | `config/odoo17.conf` avec base et filtre explicitement épinglés dans les arguments; processus actif, propriétaire fonctionnel non déterminé | `etat_civil_final_review_20261105_1304`; `data/filestore/etat_civil_final_review_20261105_1304` | Non utilisé; port protégé |
| 18191/18192 | Aucun listener observé | Aucun serveur courant | Non utilisé |

Les processus Odoo examinés pointent vers le checkout local `odoo/odoo-bin`; `odoo-bin --version` renvoie Odoo Server 17.0. L’interpréteur est Python 3.14.4. `pg_lsclusters` indique PostgreSQL 18 sur 5432. Ces observations ne remplacent pas une validation des bases par une identité disposant des droits de catalogue.

### Contrôles effectués pendant cet addendum

- `git status --short --untracked-files=normal`, `git diff --stat`, `git diff --cached --stat`: le dépôt était déjà fortement modifié (5 entrées staged, 51 changements suivis non staged, 4 818 entrées non suivies au relevé initial). Ces modifications n’ont pas été nettoyées.
- `ss -ltnp`, `ps -eo pid,comm`, lecture des arguments de processus et des paramètres non secrets des configurations: inventaire ci-dessus. Aucun secret n’a été inclus dans les sorties conservées.
- `venv/bin/python odoo/odoo-bin --version`; import de `odoo.tools.mail.email_normalize`: Odoo 17.0 détecté, import disponible, entrée synthétique valide reconnue et login non e-mail rejeté.
- Analyse AST de 7 fichiers Python et parsing XML de 2 rapports: réussite syntaxique. Inspection IDE: le contrôleur a expiré; les avertissements SQL reflètent l’absence de source de données IDE, et aucune erreur d’exécution n’a été établie par cette inspection.
- Aucun test Odoo, appel HTTP, rendu PDF ou parcours Chromium authentifié n’a été exécuté dans cet addendum. Les résultats dynamiques précédemment documentés restent des preuves historiques associées uniquement aux bases et heures qui y sont indiquées.

### Statut consolidé selon les statuts autorisés

| Fonction | Statut | Limite ou preuve |
|---|---|---|
| Précontrôle e-mail à l’installation et la mise à jour | TERMINÉ ET TESTÉ | Scénarios synthétiques et 7 tests ciblés consignés dans `rapport-authentification-securite.md`; aucun compte réel. |
| Connexion e-mail positive après migration et classement humain/technique | BLOQUÉ | Aucun compte synthétique autorisé pour le test positif courant; aucun inventaire réel permis. |
| Classification juridique des rapports d’actes et séparation interne/officielle | EN ATTENTE DE VALIDATION MÉTIER | Ne pas retirer ou restreindre les routes legacy sans décision sur la nature juridique des PDF. |
| Contrôles de cohérence facture/paiement côté serveur | TERMINÉ MAIS NON TESTÉ | Revue de code et 5 tests ciblés antérieurs; aucune transaction comptable de bout en bout. |
| Gratuité, paiement complet/partiel, facture incorrecte, annulation/avoir/remboursement | NON IMPLÉMENTÉ | Aucun parcours financier E2E prouvé; avoir/remboursement non relié au workflow. |
| Concurrence PostgreSQL multi-transaction | BLOQUÉ | Aucun nouveau couple base/filestore n’a pu être identifié comme disponible. |
| Health anonyme sans nom de base et login invalide générique | TERMINÉ ET TESTÉ | Preuves HTTP antérieures sur une base synthétique. |
| Absence de `session_id` dans le JSON du login réussi | TERMINÉ MAIS NON TESTÉ | Confirmée statiquement; le mécanisme de cookie Odoo est conservé. |
| Tests API autorisés, CSRF/CORS et navigateur par rôle | BLOQUÉ | Pas d’identifiants synthétiques autorisés pour la base active; aucun accès URL/PDF authentifié tenté. |
| Restauration synthétique et intégrité des pièces | TERMINÉ ET TESTÉ | Restauration distincte antérieure avec 43/43 objets de filestore, voir preuves déjà référencées. |
| Migration des comptes réels / mise en production | EN ATTENTE DE VALIDATION MÉTIER | Aucune adresse à inventer; migration suspendue et aucun déploiement autorisé. |

### Fichiers et conservation

Aucun fichier source n’a été modifié dans cet addendum. Le présent rapport a été complété après sauvegarde de son contenu antérieur dans `backups/rapport-validation-finale-phase-suivante-avant-audit-20261105T2325.md` (SHA-256 `445a0707e300973411fd15e9fbad6ba5799a5f046e3e40332532ddc8ec04b969`). Les autres rapports requis et `procedure-retour-arriere.md` étaient déjà présents sous `logs/implementation_odoo17/`; ils n’ont pas été réécrits. Aucun commit ni push n’a été créé.

**Conclusion inchangée : B — PARTIELLEMENT VALIDÉ.** Le projet n’est pas prêt pour la production. Les blocages financiers, métier, concurrence, comptes et navigateur demeurent; aucune preuve de ce relevé statique ne doit être interprétée comme validation dynamique.

# Inventaire technique et plan de professionnalisation

Date de l’audit : 8 novembre 2026  
Périmètre : dépôt, manifests Odoo, scripts, configuration, artefacts Git et
métadonnées PostgreSQL. Inspection des données métier limitée aux comptes
agrégés de la base confirmée comme production; aucun enregistrement personnel
n’a été lu.

## Résumé

Le dépôt contient les sources Odoo 17, quatre addons métier, des journaux,
des bases/filestores de validation et des fichiers propres à l’environnement
local. Le principal risque de livraison identifié au début de l’audit était la
présence de configuration avec secret, données runtime, journaux, archives et
bytecode dans le suivi Git. Ces artefacts ont été retirés de l’index sans
supprimer les copies locales; l’historique Git conserve l’ancienne
configuration et n’a pas été réécrit.

La branche `chore/professionalisation-projet` a été créée depuis le commit
`a05d9c06`. Au début de l’intervention, les changements locaux préexistants
(25 chemins suivis modifiés, 46 chemins non suivis) ont été préservés. Les
retraits d’artefacts de l’index décrits ci-dessous sont intentionnels et
staged; aucun changement n’a été commité. Une copie de précaution vérifiée se trouve sous
`/tmp/gestion_etat_civil_preexisting_worktree_20261108/` :

- `tracked-changes.patch`, vérifiée avec `git apply --check --reverse`;
- `untracked-files.tar.gz`, archive valide de 1 264 entrées.

Le dossier de livraison demandé, `gestion_etat_civil`, ne doit pas remplacer le
checkout actif avant que les chemins externes soient vérifiés. Le modèle
recommandé est de garder le checkout de travail et de créer une livraison
distincte après validation.

## Inventaire des éléments du projet

| Nom actuel | Nom/organisation cible | Fonction et dépendances observées | Action |
|---|---|---|---|
| `stage_l3_odoo` (checkout) | Livraison séparée `gestion_etat_civil` | Le chemin absolu est utilisé par la configuration locale | Garder le checkout actif; préparer une copie/livraison distincte après validation des chemins |
| `odoo/` | Conserver `odoo/` | Sources natives Odoo Server 17.0, 40 107 fichiers suivis | Préserver le cœur; documenter sa révision et ne pas le renommer dans cette opération |
| `custom_addons/etat_civil` | Conserver le nom technique | Dépend de `base`, `mail`, `web`; cœur métier et API | Conserver les identifiants de modèles, manifests, migrations et tests |
| `custom_addons/etat_civil_account` | Conserver le nom technique | Dépend de `etat_civil`, `account` | Factures, paiements et demandes de copies |
| `custom_addons/etat_civil_pos` | Conserver le nom technique | Dépend de `etat_civil_account`, `point_of_sale` | Pont POS facultatif vers la facture existante |
| `custom_addons/etat_civil_auth_email` | Conserver le nom technique | Dépend de `base`, `web`, `etat_civil` | Extension facultative de connexion |
| `config/odoo17.conf` | Conserver localement; exemple dans `configuration/` | Paramètres réels, chemins absolus, DB de production | Retiré de l’index Git sans supprimer le fichier local; historique antérieur inchangé |
| `README.md` racine | README produit | Guide d’accueil et de maintenance | Fonctionnalités, modules, installation de développement, tests, sauvegardes et limites documentés |
| `docs/`, `documentation/` | `documentation/` | Rapports d’audit, périmètre et procédures | Documents utiles regroupés; notes d’installation historiques archivées |
| `requirements/` absent | `requirements/custom-addons.txt` | Odoo fournit ses dépendances de base | Ajouter uniquement les extras utilisés par les formats XLSX/ODS |
| `data/`, `logs/`, `backups/` | Runtime local hors version livrée | Filestores, sessions, validations, journaux et archives | Retirés de l’index Git sans supprimer les fichiers locaux |
| `tests/test_*.py`, `migrations/` | Conserver la structure native | Découverte de tests et mises à jour versionnées Odoo | Ne pas renommer ni supprimer sans migration vérifiée |
| `.idea/` | Configuration locale ignorée | Préférences d’IDE propres à l’utilisateur | Retirée de l’index Git; fichiers locaux conservés |
| `rapport_de_stage/` | Documents académiques conservés | Modèles, captures, documents et artefacts mobiles | Documents utiles conservés; ZIP de zéro octet et fichiers `.part` exclus de l’index mais conservés localement |
| `scripts/cleanup_odoo17.sh` | Script d’audit/maintenance | Inventaire DB et contrôle d’archives | Garder; documenter les limites et ne pas le confondre avec une sauvegarde/restauration |
| `custom_addons/etat_civil/scripts/update_module.sh` | Retiré de l’arborescence active | Cible `/opt/odoo/odoo` absente et configuration d’un autre ancien checkout; aucun appel trouvé | Non exécuté; suppression locale effectuée, historique antérieur conservé dans Git |
| `custom_addons/etat_civil/scripts/migrate_data_odoo18_to_odoo17.py` | Outil historique non validé | Migration SQL directe, sans référence trouvée dans le dépôt | Ne pas exécuter : mot de passe par défaut, écriture/commit par défaut, repli d’identifiants vers l’admin et compteur `inserted` non initialisé; revue et essais isolés nécessaires |
| `odoo17.sh` | Gestionnaire local avec garde-fous | Utilise la configuration locale, qui désigne la production | Ajout du chemin Python local et de refus de mise à jour de la DB de production ou si le service systemd est actif |

Les manifests des quatre addons ont été analysés : toutes les entrées `data`
et les motifs d’assets qu’ils déclarent existent. Les noms techniques et les
répertoires `tests/` sont des exigences Odoo et ne sont pas des éléments
temporaires malgré le mot `test`.

## Dépendances Python

Odoo définit les dépendances de base dans `odoo/requirements.txt` et
`odoo/setup.py`. Les addons utilisent notamment Pillow, qrcode, lxml,
MarkupSafe, psycopg2, Werkzeug et xlrd; ces dépendances sont déjà prises en
charge par Odoo.

Le modèle d’import/export charge `openpyxl` pour XLSX et `odfpy` pour ODS
uniquement lorsque ces formats sont utilisés; il produit un message
explicite si la bibliothèque optionnelle manque. `requirements/custom-addons.txt`
épingle les versions observées dans l’environnement local : `openpyxl 3.1.5`
et `odfpy 1.4.1`. `xlrd 2.0.1` est fourni par les exigences Odoo.

Aucune dépendance inutilisée n’a été supprimée. Les tests de format et la
compatibilité des versions optionnelles avec les fichiers réels restent à
valider avant de réduire ou modifier ces contraintes.

## PostgreSQL et filestores

PostgreSQL expose 45 bases : 38 propriétaires `odoo17`, 3 propriétaires
`odoo` et 4 propriétaires `postgres`. L’inventaire par rôle est le suivant.
Les noms de rôle des bases autres que `etat_civil_odoo17_test` restent des
hypothèses à confirmer; aucun renommage n’est effectué.

### Base confirmée comme production

`etat_civil_odoo17_test` est la base de production confirmée par l’utilisateur.
Elle appartient à `odoo17`, mesure environ 68 Mo et contient les modules
`base`, `web`, `account`, `point_of_sale`, `etat_civil`,
`etat_civil_account` et `etat_civil_pos`. `etat_civil_auth_email` y est
désinstallé. Une société est déclarée et le filestore local correspondant
contient 438 fichiers. Seuls des états de modules et des compteurs agrégés ont
été consultés; aucun dossier ou identité utilisateur n’a été lu. Aucune
connexion Odoo active à cette base n’a été observée durant l’audit.

### Bases propriétaires `odoo17` (38)

- Workflow : `ec_workflow_test_20261101`,
  `ec_workflow_test_20261101c`, `ec_workflow_test_20261101d`,
  `ec_workflow_test_20261101e`, `ec_workflow_test_20261101f`,
  `ec_workflow_test_20261101g`, `ec_workflow_test_20261101h`,
  `ec_workflow_test_20261101i`.
- Revue/validation : `etat_civil_admin_roles_validation_20261104`,
  `etat_civil_audit_targeted_20261102`,
  `etat_civil_audit_targeted_b_20261102`,
  `etat_civil_final_audit_20261102`,
  `etat_civil_final_audit_retry_20261102`,
  `etat_civil_final_audit_tests_20261105`,
  `etat_civil_final_review_20261105_1304`,
  `etat_civil_isolated_review_20261104_2225`,
  `etat_civil_isolated_review2_20261104_2240`,
  `etat_civil_isolated_review3_20261104_2300`,
  `etat_civil_predeploy_20261104_2146`,
  `etat_civil_restore_validation_20261105_01`,
  `etat_civil_validation_20261104_2125`,
  `etat_civil_validation_20261106_0100`,
  `etat_civil_validation_restore_20261106_0100`.
- Développement candidat selon les rapports antérieurs, à reconfirmer :
  `etat_civil_dev_email_account_20261105`,
  `etat_civil_dev_email_account_auth_20261105`,
  `etat_civil_dev_finalcheck_20261105`,
  `etat_civil_dev_latest_20261105`,
  `etat_civil_dev_regression_20261105`,
  `etat_civil_dev_verify_final_20261105`,
  `etat_civil_phase_next_auth_20261105_01`,
  `etat_civil_phase_next_auth_incompatible_20261105_02`,
  `etat_civil_phase_next_finance_20261105_01`,
  `etat_civil_retry_20261102b`,
  `etat_civil_stability_20261101`,
  `etat_civil_stability_20261102`.
- Bases MGA de test : `etat_civil_odoo17_mga_generic_test_20261108` et
  `etat_civil_odoo17_mga_test_20261108`. Elles restent des bases de test
  distinctes et ne sont pas des environnements de production.

Les bases propriétaires `odoo`, non inspectables avec le compte PostgreSQL
courant, sont `gestion_detat_civil`, `gestion_detat_civil_clean_odoo17` et
`gestion_detat_civil_test_odoo17`. Elles ne sont pas classées par fonction
sans accès autorisé.

Les bases appartenant à `postgres` sont `postgres`, `rich_vent`, `rich_vente`
et `transport_coop`. Elles ne sont pas considérées comme des bases de ce
projet et ne doivent pas être modifiées dans cette opération.

Des filestores locaux existent pour dix bases Odoo. Leur correspondance doit
être vérifiée avec le `data_dir` de chaque instance avant toute restauration
ou renommage. La configuration systemd `/etc/odoo/odoo.conf` est inaccessible
au compte courant; les filestores d’autres instances peuvent donc être
stockés ailleurs.

### Sauvegardes examinées

- Deux dumps PostgreSQL passent `pg_restore --list`; cela vérifie leur
  lisibilité, pas une restauration complète.
- Cinq archives ZIP de sauvegarde sont valides selon `unzip -t`.
- Deux ZIP mobiles de zéro octet sont invalides; deux téléchargements `.part`
  correspondants subsistent. Aucun n’a été supprimé ou remplacé.
- Aucune sauvegarde nouvelle de la base de production n’a été créée, car
  aucune opération sur celle-ci n’a été autorisée ou nécessaire.

**Aucune base, aucun filestore et aucun journal n’a été supprimé, déplacé ou
renommé.**

## Configuration et exécution

- `config/odoo17.conf` est retiré de l’index Git; le fichier local, mode `600`,
  est conservé et contient une valeur secrète non reproduite ici. Son retrait
  de la version courante ne retire pas les anciennes révisions Git. Aucune
  rotation ni réécriture d’historique n’a été effectuée.
- Les addons path, `data_dir` et logfile de la configuration locale contiennent
  des références absolues au checkout `stage_l3_odoo`.
- `odoo.service` est inactif. Son `ExecStart` utilise `/usr/bin/odoo` et
  `/etc/odoo/odoo.conf`, mais cette configuration n’est pas lisible par le
  compte d’audit. Le binaire système échoue à l’import sur
  `AttributeError: module 'werkzeug' has no attribute '__version__'`.
- Le binaire Odoo local répond `Odoo Server 17.0` avec Python 3.14.4.
- `odoo17.sh` auparavant ne plaçait pas explicitement les sources locales
  avant les paquets système et ne protégeait pas contre la mise à jour de la
  base confirmée comme production. Les garde-fous correspondants sont ajoutés
  dans ce checkout. L’essai de `update etat_civil` a été refusé avec le message
  attendu pour la base de production; aucune mise à jour n’a été exécutée.

## Artefacts suivis par Git et actions de livraison

Le dépôt suivait des caches `.pyc`, des logs, des dumps, des filestores et des
sessions, ainsi que des fichiers `.idea` et une configuration contenant un
secret. Ces chemins ont été retirés de l’index Git et restent présents sur le
disque. Le `.gitignore` empêche leur ajout accidentel futur. Les retraits sont
staged et doivent être examinés avant tout commit.

La configuration avec secret reste présente dans l’historique Git. Aucune
rotation de secret ni réécriture d’historique n’a été effectuée; ces opérations
nécessitent une procédure autorisée et coordonnée.

## Plan restant

1. Vérifier le diff staged des retraits et les fichiers locaux conservés avant
   tout commit ou publication.
2. Revoir séparément l’outil SQL `migrate_data_odoo18_to_odoo17.py`; ne pas
   l’exécuter avant correction, essais sur des copies isolées et validation de
   la correspondance des identifiants. Terminer aussi l’examen des documents
   académiques et rapports historiques.
3. Obtenir les paramètres **non secrets** de l’instance systemd pour confirmer
   ses addons path, sa base et son `data_dir`.
4. Valider `requirements/custom-addons.txt`, les scripts et les manifests.
   Exécuter les suites Odoo uniquement sur une base isolée, sans toucher à la
   base de production confirmée ni redémarrer le service.
5. Présenter un mapping PostgreSQL nominatif. Aucun renommage ne sera appliqué
   dans cette phase; tout changement de nom de production demande une
   autorisation distincte, un dump et un filestore vérifiés ainsi qu’un plan
   de retour arrière.
6. La licence globale reste indéterminée; aucun `LICENSE` racine n’est créé.

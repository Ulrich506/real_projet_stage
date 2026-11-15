# Audit de finalisation — POS et devise MGA

> **Note de classement (8 novembre 2026) :** ce rapport historique et ses
> commandes mentionnent `etat_civil_odoo17_test` comme base de test. Cette base
> est maintenant confirmée par l’utilisateur comme base de production. Les
> commandes et résultats ci-dessous ne doivent pas être rejoués ni interprétés
> comme autorisation de modifier la production. La nouvelle validation MGA a
> été exécutée séparément sur `etat_civil_odoo17_mga_generic_test_20261108`.

Date de l'inspection : 8 novembre 2026
Branche historique : `fix/etat-civil-account-billing`
Périmètre réalisé : phases 1 et 2 — audit et diagnostic, sans correction

## 1. Résumé exécutif

Le blocage USD/MGA est une incompatibilité de configuration, pas une
limitation générale du POS Odoo 17 ni un défaut démontré du module métier.
L'extension `etat_civil_pos` exige volontairement que la devise de la session
POS soit exactement celle de la facture liée. Dans la base de test, la société
est en USD, le journal de vente POS est en USD, les moyens de paiement et le
journal de facture sont en devise de société, et aucun taux MGA n'est défini.
Les factures de copies en MGA ne sont donc pas présentées au POS et une
commande de devise différente est rejetée.

Odoo 17 sait prendre en charge une devise de transaction POS différente de la
devise de comptabilité de la société : `pos.config.currency_id` est déterminée
par le journal de vente POS lorsqu'il porte une devise propre; sinon, elle
reprend la devise de la société. Les prix de liste, journaux de moyens de
paiement et journal de facture du POS doivent alors respecter cette devise.
Odoo convertit les écritures vers la devise de société en utilisant le taux
daté configuré. Il n'est donc ni nécessaire ni prudent de changer la devise
principale de la société USD déjà utilisée.

**Solution recommandée :** garder la société et sa comptabilité en USD,
configurer un journal de vente dédié au POS en MGA, ainsi que les moyens de
paiement, le journal de facture et la liste de prix en MGA, et charger un taux
de change MGA/USD réel, daté et validé par la commune/comptable. Aucun taux ne
doit être inventé. La configuration et le parcours complet restent à tester
avant toute conclusion de validation.

## 2. État de l'environnement examiné

### Git et modifications locales

- Branche active : `fix/etat-civil-account-billing`.
- L'arbre de travail comporte déjà de nombreuses modifications locales,
  fichiers non suivis, journaux, fichiers compilés et éléments de filestore.
  Ils n'ont pas été réinitialisés, supprimés ou écrasés pendant cet audit.
- `git diff --check` sur l'ensemble du dépôt signale des espaces finaux dans
  les lignes ajoutées au journal préexistant `logs/odoo17.log`. Aucun journal
  n'a été nettoyé ou réécrit par cette inspection.
- Aucun commit n'a été créé.

### Odoo, PostgreSQL et base

- La configuration consultée est `config/odoo17.conf`; elle désigne par
  défaut `etat_civil_odoo17_test` et place les addons dans `odoo/addons` et
  `custom_addons`.
- Les secrets présents dans cette configuration ne sont pas reproduits dans
  ce rapport. Ils sont stockés en clair dans le fichier : protéger son accès
  au dépôt et envisager une gestion dédiée des secrets.
- Aucun processus serveur `odoo-bin` n'était actif lors de l'inspection.
  PostgreSQL était actif. Aucun service Odoo n'a été démarré ni redémarré.
- Les données ont été lues par un shell Odoo sans `--update`, en transaction
  SQL `READ ONLY`, puis annulée. Aucune donnée n'a été écrite.
- Sauvegardes de test préexistantes vérifiées :
  - `/tmp/etat_civil_odoo17_test_pre_account_audit_20261108.dump`
  - `/tmp/etat_civil_odoo17_test_pre_final_billing_validation_20261108.dump`
- Aucune base active ou de production n'a été inspectée ou modifiée.

### Modules installés dans la base de test

| Module | État observé |
|---|---|
| `etat_civil` | Installé, version `17.0.2.1.9` |
| `etat_civil_account` | Installé, version `17.0.1.1.0` |
| `etat_civil_pos` | Installé, version `17.0.1.0.0` |
| `account` | Installé, version `17.0.1.2` |
| `point_of_sale` | Installé, version `17.0.1.0.1` |

## 3. Fonctionnalités et tests déjà disponibles

Le travail déjà présent dans les addons fournit notamment :

- une demande de copie liée à une facture unique;
- des versements comptables partiels et des quittances individuelles
  réimprimables;
- un rapprochement POS avec la facture de la demande existante, sans créer
  une seconde facture;
- une autorisation de délivrance qui attend le règlement complet;
- des contrôles serveur sur l'utilisateur, le centre, le demandeur, la
  session, la devise et le montant;
- des tests de permissions du Régisseur et de l'Agent.

Le journal final disponible
`/tmp/etat_civil_billing_final_tests_retry2_20261108.log` rapporte **17 tests,
0 échec, 0 erreur**, code de sortie de la commande Odoo **0**. Il couvre les
tests comptables ciblés et les tests POS dans la devise de la société. Il ne
prouve pas le scénario POS MGA/USD.

Une tentative antérieure, consignée dans
`/tmp/etat_civil_billing_final_tests_20261108.log`, s'est terminée par
**16 tests, 0 échec et 1 erreur** : le test du produit de paiement POS a échoué.
La relance finale a exécuté le test concerné et les 17 cas sans erreur.

Inventaire statique des méthodes `test_*` présentes (ce nombre n'est pas un
résultat d'exécution) :

| Module | Méthodes de test trouvées |
|---|---:|
| `etat_civil` | 98 |
| `etat_civil_account` | 12 |
| `etat_civil_pos` | 5 |

**Tests encore manquants :** exécution des suites complètes des trois modules,
exécution intégrée, parcours POS en MGA avec taux vérifié, et tests des cas
POS suivants : plusieurs versements POS MGA, annulation de commande ou de
paiement, session fermée, double clic/double encaissement, paiement échoué,
réimpression, demande gratuite et demande annulée. Les tests de non-régression
des API, assistants, rapports, imports/exports et annuaire doivent également
être inclus dans la suite complète.

## 4. Configuration réelle des devises

L'inspection en lecture seule de `etat_civil_odoo17_test` a observé :

| Élément | Configuration actuelle |
|---|---|
| Société `My Company` | Devise comptable USD |
| Devise MGA | Active |
| Taux MGA disponibles pour la société ou globaux | Aucun |
| POS | Une configuration, `Restaurant (non utilisé)` |
| Devise calculée du POS | USD |
| Journal de vente POS | `Point de Vente`, type `general`, devise de société (USD) |
| Journal de facture POS | `Factures clients`, devise de société (USD) |
| Liste de prix POS | Aucune par défaut; aucune liste disponible |
| Utilisation des listes de prix dans ce POS | Désactivée |
| Moyens de paiement | Banque et espèces, journaux en devise de société; un moyen différé |
| Sessions POS | Une session fermée; aucune session ouverte |
| Demandes/factures de copie persistées | Aucune dans la base au moment de la lecture |

Les tests actuels de facturation MGA créent dans leur transaction un taux
MGA synthétique (`rate = 0.0002`) pour rendre le test isolé reproductible.
Ce taux de fixture n'est pas une donnée métier et ne valide pas une conversion
réelle. Il ne doit pas être repris dans la configuration opérationnelle.

## 5. Cause technique précise USD/MGA

### Règle native Odoo 17

Dans `odoo/addons/point_of_sale/models/pos_config.py`, la méthode
`_compute_currency` choisit la devise du journal de vente POS si elle est
définie; sinon elle choisit la devise de la société. La contrainte native
`_check_currencies` impose que les listes de prix disponibles, les journaux
des moyens de paiement et le journal de facture soient compatibles avec la
devise POS.

Dans `odoo/addons/point_of_sale/models/pos_order.py`, le taux de conversion
d'une commande est calculé entre la devise de la société et celle de la
commande à la date de commande. Les écritures de session sont converties dans
la devise de la société par les mécanismes comptables natifs.

### Règle de l'intégration État civil

- `custom_addons/etat_civil_pos/models/copy_request.py` écarte les demandes
  dont la facture n'a pas la même devise que la session POS.
- `custom_addons/etat_civil_pos/models/pos_order.py` rejette une commande si
  la devise de la commande POS diffère de celle de la facture.
- `custom_addons/etat_civil_account/models/copy_request.py` crée la facture
  dans la devise du tarif figé sur la demande.

Il n'y a pas de conversion manuelle applicative dans ce parcours : le montant
encaissé POS doit être le montant restant de la facture dans la devise POS.
Odoo effectue ensuite la conversion comptable selon le taux de change daté.

### Diagnostic

Le POS existant est configuré en USD parce que son journal de vente POS ne
définit pas de devise et hérite donc de celle de la société. Son absence de
liste de prix MGA et de journaux de paiement MGA est cohérente avec cette
configuration. Les factures MGA sont par conséquent exclues de la sélection
POS, et la validation serveur rejetterait une commande en devise différente.
L'absence de taux MGA empêcherait en outre de valider la conversion USD/MGA
dans les écritures comptables.

Le point bloquant exact est donc l'absence de configuration d'une devise
transactionnelle MGA supportée par les journaux POS, combinée à l'absence de
taux MGA réel; ce n'est pas simplement une liste de prix manquante.

## 6. Comparaison actuelle / cible / correction

| Élément | Configuration actuelle | Configuration cible | Correction requise |
|---|---|---|---|
| Société | USD | USD conservé, sauf décision comptable distincte | Ne pas changer la devise principale de cette société |
| Journal de vente POS | Devise société (USD) | Journal POS dédié avec devise MGA | Configurer le journal selon la politique comptable et les journaux autorisés |
| Devise POS | USD | MGA, calculée depuis le journal POS | Vérifier le calcul et les contraintes Odoo |
| Liste de prix | Aucune | Liste MGA compatible, si activée | Créer/associer une liste tarifaire MGA validée |
| Journal de facture POS | Devise société (USD) | MGA pour cette configuration POS | Choisir un journal de vente MGA compatible |
| Moyens de paiement | Journaux en USD/société | Journaux compatibles MGA, un par méthode réelle | Configurer espèces et autre moyen effectivement utilisé |
| Taux de change | Aucun taux MGA | Taux officiel/validé, daté et société-compatible | Importer/configurer seulement un taux sourcé et approuvé |
| Facture de copie | Tarif MGA possible | Facture et montant restant en MGA | Préserver le lien unique demande-facture |
| Paiement/quittance | Tests en devise POS USD | Montant reçu et quittance en MGA | Vérifier devise, montant, date, rapprochement et unicité |
| Comptabilisation | USD société | Conversion MGA vers USD par Odoo | Comparer écritures et montants convertis à partir du taux officiel |

## 7. Plan de correction proposé

1. La règle a été confirmée : taux de référence publié par la Banque Centrale
   de Madagascar à la date de transaction. La source officielle résout en DNS,
   mais son certificat HTTPS ne peut pas être validé depuis cet environnement
   (chaîne d'autorité inconnue). Le contenu n'a pas été utilisé et la
   vérification TLS n'a pas été contournée. Attendre une source HTTPS
   vérifiable ou un document BFM authentifiable avant d'ajouter un taux.
2. Sur une configuration de test isolée, sans modifier la devise de la société,
   préparer le journal de vente POS MGA, le journal de facture MGA, les
   journaux associés aux moyens de paiement réels et une liste de prix MGA
   si nécessaire.
3. Vérifier la devise calculée du POS et toutes les contraintes natives avant
   d'ouvrir une session de test.
4. Réaliser sur base de test un parcours complet MGA : facture unique,
   paiements POS, rapprochements, quittances, conversion USD, et contrôle du
   solde avant délivrance.
5. Ajouter des tests de non-régression ciblés et tester les échecs,
   annulations et doubles soumissions; ne pas relâcher les validations
   serveur.
6. Exécuter ensuite séparément les suites complètes `etat_civil`,
   `etat_civil_account`, `etat_civil_pos`, puis la suite intégrée, en conservant
   logs, codes de sortie et sauvegarde de la base de test.

## 8. État à la fin de cet audit

Ce livrable couvre uniquement les phases 1 et 2. Aucun code, manifeste,
paramètre Odoo, journal comptable, taux de change, base ou filestore n'a été
modifié. La base active n'a pas été mise à jour et aucun service Odoo n'a été
redémarré.

**Conclusion à ce stade : B — PARTIELLEMENT VALIDÉ.** Le parcours ciblé en USD
est testé; le fonctionnement POS MGA, la conversion par un taux réel et les
suites complètes restent à valider. L'utilisateur a choisi le taux BFM à la
date de transaction, mais la source ne peut actuellement pas être authentifiée
depuis cet environnement. Aucun statut A ne peut être annoncé avant ces
validations.

## 9. Addendum — validation isolée MGA du 8 novembre 2026

Cet addendum complète l'audit initial après le choix explicite d'un flux
exclusivement MGA sur une nouvelle base de test. Il ne remplace pas le constat
historique ci-dessus sur la base de test initiale en USD.

### Base et configuration utilisées

- Base testée : `etat_civil_odoo17_mga_generic_test_20261108`.
- Le plan comptable `generic_coa` et les modules `account`,
  `point_of_sale`, `etat_civil`, `etat_civil_account` et `etat_civil_pos`
  sont installés.
- La société de cette base est configurée avec le pays MG et la devise MGA;
  la devise calculée du POS est également MGA.
- `l10n_fr` est non installé. Une première base distincte,
  `etat_civil_odoo17_mga_test_20261108`, avait sélectionné le chart français;
  elle a été conservée et n'a pas été utilisée pour les résultats ci-dessous.
- Aucun mouvement comptable, aucune commande POS et aucune session POS
  n'existaient au moment où la devise de la société a été réglée après
  l'installation du chart.
- USD reste actif dans le référentiel Odoo, mais aucune devise ni aucun taux
  USD/MGA n'est utilisé par cette configuration. Il n'y a pas de conversion
  à valider tant que les opérations, factures et la société restent toutes
  en MGA.
- Aucune donnée ni configuration de production, aucun service Odoo et aucune
  base active n'ont été modifiés. Le service n'a pas été redémarré.

Sauvegardes conservées avant les étapes correspondantes :

- `/tmp/etat_civil_odoo17_mga_generic_base_20261108.dump`
- `/tmp/etat_civil_odoo17_mga_generic_pre_modules_20261108.dump`
- `/tmp/etat_civil_odoo17_mga_generic_post_install_pre_country_20261108.dump`

### Tests exécutés

La mise à jour et l'exécution des tests ont été lancées avec Odoo 17 local,
sur la base isolée, avec `--no-http` et `--stop-after-init`. Le code de sortie
de la commande est **0**.

Journal complet :
`/tmp/etat_civil_odoo17_mga_generic_tests_20261108.log`

Résultat agrégé Odoo : **115 tests, 0 échec, 0 erreur**. Les lignes
`Starting Test` confirment 98 tests `etat_civil`, 12
`etat_civil_account` et 5 `etat_civil_pos`, soit les 115 méthodes présentes
dans ces suites. Aucun compteur de tests ignorés n'est émis par le résumé
Odoo; les tests ignorés ne peuvent donc pas être chiffrés à partir de ce
journal.

Les tests pertinents comprennent notamment :

- création d'une facture de copie en MGA et vérification de sa devise;
- rapprochement du paiement dans la devise de facture;
- versements partiels et finaux avec quittances;
- paiements POS partiels et finaux rapprochés à une seule facture;
- contrôles d'accès du Régisseur et de l'Agent.

Après les tests, les contrôles de base confirment toujours MG/MGA,
`generic_coa`, POS en MGA, zéro mouvement comptable persistant et zéro taux
MGA/USD ou USD.

Un avertissement de test est consigné : le test d'import reçoit volontairement
un fichier JSON invalide et journalise son rejet. Il n'y a ni erreur ni échec
de test associé. La sortie standard de l'installation a aussi émis des
diagnostics Docutils de formatage (« Unexpected indentation » et « Block quote
ends without a blank line »); l'origine exacte du texte analysé n'a pas été
identifiée. Ils n'ont pas interrompu l'installation, dont le code de sortie
était 0. Le journal Odoo d'installation n'enregistre aucun ERROR, CRITICAL ou
WARNING.

Les agrégats `odoo.tests.stats` affichent séparément 114 tests pour
`etat_civil`, 16 pour `etat_civil_account` et 9 pour `etat_civil_pos`, alors
que le résumé agrégé et les démarrages de tests dénombrent 115 méthodes
uniques. Le total de ces compteurs par addon n'est donc pas utilisé comme
nombre de tests distincts; le compte vérifiable retenu est le résumé Odoo et
les 115 lignes de démarrage.

### Résultat et limites

**Conclusion : B — PARTIELLEMENT VALIDÉ.** Les suites complètes des trois
modules se sont exécutées sur la base isolée et les parcours MGA de facturation
et d'encaissement POS couverts par les tests ont réussi. Aucun fichier
applicatif n'a été modifié dans cette phase; la correction effectuée concerne
uniquement la configuration de la nouvelle base de test.

Le résultat ne constitue pas une validation complète de mise en production :

- aucun taux BFM n'a été récupéré, authentifié ou importé;
- aucune conversion MGA/USD, écriture multidevise, différence de change ou
  clôture de session POS multidevise n'a été testée;
- le chart générique est un choix de test technique et n'est pas une
  recommandation de plan comptable ou de conformité malgache;
- les tests automatisés ne remplacent pas un essai d'acceptation utilisateur
  des journaux, moyens d'encaissement, taxes, prix, remboursements et
  quittances.

### Avant toute mise à jour de la base active

1. Confirmer avec le comptable et les responsables métier que la devise
   comptable de la société doit réellement devenir MGA, et valider le plan
   comptable et les journaux appropriés à Madagascar.
2. Décider si un flux USD est requis. S'il l'est, obtenir une publication BFM
   authentifiable, avec date, sens de cotation et type de cours; configurer
   ensuite les taux historiques sans les écraser et tester les conversions.
3. Vérifier les journaux, taxes, méthodes de paiement, listes de prix,
   clôtures POS et remboursements avec des données représentatives.
4. Réaliser une sauvegarde vérifiée de la base active, établir un plan de
   migration et de retour arrière, puis obtenir une autorisation explicite
   avant toute intervention sur cette base.

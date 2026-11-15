# Audit du parcours de facturation des copies

> **Note de classement (8 novembre 2026) :** les résultats et commandes
> historiques de ce document mentionnent `etat_civil_odoo17_test`. Cette base
> est maintenant confirmée par l’utilisateur comme base de production. Ne
> rejouez aucune commande de mise à jour ou de test sur cette base. Les
> validations suivantes doivent viser une base isolée sauvegardée.

Date : 8 novembre 2026  
Branche historique : `fix/etat-civil-account-billing`  
État initial : audit terminé, corrections applicatives non commencées  
État courant : corrections ciblées implémentées et validées sur la base de test

## Résultat après corrections

Les sections ci-dessous consignent l'audit initial. Depuis cet audit, le
parcours a été complété : la demande reste liée à une facture unique, le
Régisseur peut enregistrer des versements partiels via un wizard métier et le
POS rapproche ses paiements à cette même facture. Chaque versement crée une
quittance réimprimable; la délivrance reste bloquée jusqu'au règlement complet.
Le ticket guichet est relié à la demande de copie.

La validation ciblée la plus récente a mis à jour `etat_civil_account` et
`etat_civil_pos`, puis exécuté **17 tests : 0 échec, 0 erreur**, code de sortie
Odoo **0**. Les tests incluent le versement comptable partiel puis final par le
Régisseur, le rapprochement POS partiel puis final, l'unicité de la facture,
les quittances, les contrôles d'accès et le blocage de la délivrance avant
règlement complet. Aucun test ignoré n'est signalé dans le journal.

Commande exécutée, uniquement sur `etat_civil_odoo17_test` :

```text
./venv/bin/python odoo/odoo-bin
  --config=config/odoo17.conf
  --database=etat_civil_odoo17_test
  --update=etat_civil_account,etat_civil_pos
  --stop-after-init --no-http --test-enable
  --test-tags=/etat_civil_account,/etat_civil_pos
```

Journal complet : `/tmp/etat_civil_billing_final_tests_retry2_20261108.log`  
Sortie console : `/tmp/etat_civil_billing_final_tests_retry2_console_20261108.log`  
Code de sortie de la commande Odoo : `0`.

Les modifications applicatives sont dans `custom_addons/etat_civil_account`
et le nouvel addon `custom_addons/etat_civil_pos`. Le test
`test_regisseur_registers_partial_and_final_versments_with_quittances` couvre
maintenant aussi le parcours d'encaissement comptable métier en deux versements.
Les contrôles syntaxiques Python/XML/JavaScript et `git diff --check` ont
réussi.

**Limites restantes :** la société de la base de test tient sa comptabilité
en USD, tandis que les tarifs de copie sont en MGA. Le scénario POS de test
utilise la devise POS de la société; un encaissement réel de factures MGA par
POS n'est donc pas validé. Le taux de change MGA doit être configuré et vérifié.
La numérotation et le contenu de la quittance doivent être validés par la
commune. La suite complète d'`etat_civil` et les parcours API, assistants,
import/export et annuaire n'ont pas été exécutés dans cette validation. La
base active n'a pas été mise à jour et le service Odoo n'a pas été redémarré.

## 1. Périmètre et précautions

L'audit porte sur le module `custom_addons/etat_civil_account`, son lien avec
`account`, le modèle de tickets au guichet et le point de vente Odoo 17.

La branche dédiée a été créée depuis `main` sans écraser ni déplacer les
modifications locales déjà présentes. L'arbre de travail reste préexistant et
non propre; les modifications locales ont été conservées. Aucun fichier de
code n'a été corrigé pendant cet audit.

La configuration Odoo pointe explicitement vers `etat_civil_odoo17_test`.
Le service Odoo était arrêté avant les opérations et l'est resté. Avant le
chargement des tests, un dump PostgreSQL a été créé et vérifié :

- `/tmp/etat_civil_odoo17_test_pre_account_audit_20261108.dump`
- l'archive identifie bien `etat_civil_odoo17_test` comme base source;
- le dump est au format PostgreSQL custom et contient son catalogue d'objets.

Le seul chargement/mise à jour de module effectué pendant cet audit a visé
`etat_civil_account` dans cette base de test. Aucune autre base n'a été mise à
jour ou supprimée, aucun filestore n'a été supprimé et le service n'a pas été
redémarré.

## 2. État observé

- `etat_civil_account` est installé en version `17.0.1.0.0`.
- `account` et `point_of_sale` sont installés.
- Le manifeste d'`etat_civil_account` dépend de `etat_civil` et `account`,
  mais pas de `point_of_sale`.
- La société de la base de test tient sa comptabilité en USD. MGA est
  disponible, mais aucun taux MGA n'a été trouvé dans cette base lors de
  l'inspection. Le test de facturation crée son propre taux de change.
- La base de test ne contient aucune demande de copie, aucun paiement ni
  aucune commande POS; elle contient une écriture comptable préexistante.
- Deux configurations POS existent, mais aucune n'a de liste de prix liée
  dans la base inspectée. Aucune vente POS ne permet donc de démontrer ici un
  parcours d'encaissement MGA opérationnel.
- Le Régisseur est limité à son groupe métier, qui n'implique pas
  `account.group_account_invoice`. Ses ACL sur les factures et lignes de
  facture sont en lecture seule.

## 3. Constats et risques

### C-01 — Le Régisseur ne peut pas terminer l'encaissement par l'interface

La demande peut créer une facture brouillon via une opération élevée
(`sudo`), puis ouvrir cette facture. Le Régisseur n'a toutefois pas les droits
comptables pour modifier/poster la facture, créer un paiement ou utiliser le
wizard natif `account.payment.register`. Le bouton « Confirmer
l'encaissement » ne crée pas de paiement : il vérifie qu'un paiement client
déjà comptabilisé est rapproché et couvre exactement la facture.

En conséquence, le code actuel sait reconnaître un paiement comptable
préexistant, mais ne fournit pas au Régisseur le parcours UI minimal pour
poster la facture et enregistrer cet encaissement. Accorder au Régisseur le
groupe comptable général serait une extension trop large des privilèges et
n'est pas une correction acceptable.

Le test actuel de création de facture vérifie qu'une facture brouillon est
créée pour le Régisseur. Le test de paiement poste la facture et crée le
paiement depuis l'environnement de test privilégié; il ne prouve pas que le
Régisseur peut le faire lui-même.

### C-02 — Paiements partiels et quittances absents

`_payment_is_satisfied()` ne considère la demande payée que lorsque le total
de facture est intégralement rapproché. Les paiements partiels ne permettent
donc pas d'autoriser une délivrance, et aucun objet de paiement par versement
n'est associé à la demande.

Le module ne contient ni modèle de quittance, ni rapport QWeb de quittance,
ni séquence de quittance, ni action de réimpression. Le rapport existant est
celui de la copie d'acte autorisée. L'historique financier contient un
événement global de confirmation de paiement, pas un reçu distinct pour
chaque versement.

### C-03 — Le point de vente et la demande de copie ne sont pas reliés

Ni le modèle de demande de copie ni le modèle de ticket guichet ne portent de
lien POS. Aucune commande ou ligne POS n'identifie une demande de copie.
L'objet `pos.payment` possède son propre lien vers une commande et une
écriture comptable, mais le module métier n'exploite pas ces relations.

Le flux POS natif peut générer et comptabiliser sa propre facture. Lancer en
parallèle ce flux et la création de facture d'`etat_civil_account` peut donc
produire deux factures pour une même demande. Il faut retenir un seul
document comptable source par demande et réutiliser son lien dans le flux
POS, au lieu de créer une facture POS en plus de la facture de copie.

### C-04 — La gratuité est calculée par acte, pas par individu

À la soumission, le calcul recherche les demandes déjà délivrées pour le même
acte précis. Il ne recherche pas les copies d'un même individu sur plusieurs
actes. La demande identifie le payeur (`partner_id`) et l'acte, mais ne
possède pas de lien distinct vers l'individu concerné par l'acte.

Le comportement actuel correspond à une gratuité par acte; il ne peut pas
garantir une gratuité « une seule fois par individu » si cette règle vise
plusieurs actes de naissance de la même personne. Cette divergence doit être
tranchée avant la correction.

### C-05 — Le ticket guichet est isolé du parcours financier

`etat.civil.demande.guichet` enregistre le numéro de ticket, le nom/CIN,
le type et le statut du service demandé. Il ne référence ni demande de copie,
ni acte, ni facture, ni paiement. Le traitement d'un ticket ne déclenche donc
pas de demande financière et n'en reçoit pas le statut.

### C-06 — MGA nécessite une configuration de change effective

La société de test est en USD alors que le tarif et la facture de copie sont
en MGA. Le code refuse déjà de créer la facture s'il ne trouve pas de taux
MGA approprié. Aucun taux n'a été constaté dans la base de test examinée;
le test de facturation injecte un taux fictif dans sa transaction. Il faudra
configurer et valider le taux applicable avant tout essai métier réel.

## 4. Tests réellement exécutés

Commande exécutée sur `etat_civil_odoo17_test`, après le dump de sauvegarde :

```text
venv/bin/python odoo/odoo-bin -c config/odoo17.conf
  -d etat_civil_odoo17_test -u etat_civil_account
  --test-enable --test-tags /etat_civil_account --stop-after-init
```

Résultat Odoo : **11 tests exécutés, 0 échec, 0 erreur; aucun test ignoré
signalé**. Les 11 cas de test ont démarré.

Couverture réellement exercée :

- calcul du tarif de naissance et de la première copie gratuite;
- copie suivante payante et quantité multiple;
- création d'une facture brouillon MGA avec quantité facturable;
- reconnaissance d'une facture totalement rapprochée;
- refus de certaines écritures directes, d'une confirmation par un rôle non
  habilité, d'une demande sans acte exact et d'un tarif négatif.

Cette réussite ne valide pas les paiements partiels, les quittances, le
parcours réel de paiement du Régisseur, l'intégration POS, le lien du ticket
guichet, les règles de gratuité à l'échelle d'un individu ou le parcours de
bout en bout en interface.

Journal complet conservé : `/tmp/etat_civil_account_audit_baseline_20261108.log`  
Sortie standard conservée : `/tmp/etat_civil_account_audit_baseline_20261108.stdout`  
Code de sortie de la commande Odoo : `0`.

Un journal historique distinct de la phase précédente indique également
`0 failed, 0 error(s) of 109 tests`. Ce résultat antérieur ne couvre pas les
fonctionnalités manquantes ci-dessus et ne remplace pas les tests ciblés de
cet audit.

## 5. Décisions retenues pour les corrections

Les choix suivants ont été confirmés avant le début des corrections :

1. La première copie gratuite de naissance est accordée par individu sujet
   de l'acte (`enfant_id`), jamais par demandeur/payeur. Le modèle d'acte
   actuel impose déjà un acte de naissance unique par individu; la correction
   enregistrera explicitement cet identifiant et conservera la gratuité déjà
   consommée lors d'une mise à niveau.
2. La demande crée l'unique facture comptable. Le POS encaisse et rapproche
   son paiement à cette facture; il ne doit pas créer une seconde facture.
3. Les paiements partiels sont activés. Une quittance distincte est émise pour
   chaque versement réel, mais la délivrance reste bloquée jusqu'au solde
   intégral.
4. Une quittance technique avec séquence et mentions configurables est
   souhaitée. Son caractère officiel, sa numérotation et ses mentions restent
   à valider par la commune; aucune conformité légale n'est présumée.
5. Le ticket guichet doit être relié à la demande de copie pour conserver le
   suivi du dossier.

## 6. Conclusion de l'audit initial

Le module possède une base de calcul tarifaire et un contrôle comptable du
règlement complet, mais **le parcours demandé de facturation, encaissement par
le Régisseur, quittance et intégration POS n'est pas validé et n'est pas
complet**. Le résultat de 11 tests réussis valide uniquement les cas listés à
la section 4. La correction doit préserver les ACL minimales du Régisseur,
le rapprochement comptable réel, l'unicité de la facture et la traçabilité
des paiements.

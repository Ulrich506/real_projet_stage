# Rapport — données synthétiques de validation

**Relevé :** 2026-11-06 09:20 EAT (+03:00).  
**Base :** `etat_civil_validation_20261106_0100`; filestore dédié sous `data/validation_20261106_0100/filestore/`.  
**Instance :** HTTP/gevent 18391/18392 sur loopback.  
**Odoo / Python / PostgreSQL :** 17.0 / 3.14.4 / 18.6.  
**Modules concernés :** `etat_civil`, `etat_civil_auth_email`, `etat_civil_account`, `account`.  
**Statut :** TERMINÉ ET TESTÉ pour la préparation et le comptage des fixtures.

## Inventaire

Les contrôles PostgreSQL en lecture seule donnent :

| Type | Nombre | État / remarque |
|---|---:|---|
| Centre d'état civil | 1 | Fictif, affecté aux comptes de test |
| Registres | 3 | Synthétiques |
| Citoyens / individus | 6 | Fictifs |
| Actes | 3 | Un acte brouillon de naissance, mariage et décès |
| Demandes de copie | 3 | Toutes à l'état `draft` |
| Produit | 1 | Produit de fixture |
| Tarifs | 3 | Inactifs, prix de test non juridiques |
| Factures `account.move` | 0 | Aucune facture créée |
| Paiements `account.payment` | 0 | Aucun paiement créé |

La base compte aussi 11 partenaires (dont les partenaires techniques standards) et 474 lignes `ir_attachment`. Aucune donnée personnelle réelle n'a été utilisée. Les montants des fixtures ne constituent ni un tarif officiel ni une règle juridique.

La configuration de gratuité et les tarifs restent des paramètres synthétiques en attente de validation métier. Les tarifs inactifs ne sont pas utilisables comme barème. Aucun journal, compte bancaire, taxe ou paiement de test n'a été configuré pour simuler un parcours comptable complet.

## Résultats / limites

Les trois demandes sont lisibles par chacun des quatre rôles dans les tests de droits, sous la règle du centre affecté. Aucun acte n'a été validé; aucune facture, aucun paiement, aucun avoir, remboursement ou PDF officiel n'a été généré. La présence de fixtures ne vaut pas validation d'un flux fonctionnel.

Les nombres ont été relevés par SQL en lecture seule. La tentative initiale de création depuis un rôle insuffisant a été rejetée; sa transaction a été abandonnée, puis les données ont été créées par le compte Administrateur synthétique.

**Fichiers et ressources :** base et filestore neufs; données de fixture créées dans la base. Aucun fichier source du module n'a été modifié pendant cette validation; aucun nom, login, adresse ou document réel n'est reproduit.

**Commandes exécutées :** requêtes PostgreSQL `count(*)` en lecture seule pour les tables métier/comptables; requêtes d'état sur demandes et tarifs; chargement Odoo ORM pour la base source et sa restauration. Aucun test de création d'une facture ou d'un paiement n'a été exécuté.
**Sauvegarde :** cette base synthétique et son filestore sont compris dans le dump et l'archive dédiés, avec empreintes SHA-256; voir `rapport-sauvegarde-validation.md`.

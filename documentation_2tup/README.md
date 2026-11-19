# Documentation 2TUP — État Civil Odoo

Documentation complète du projet de gestion d'état civil sur Odoo 17, produite par audit en lecture seule.

## Structure

```
documentation_2tup/
├── README.md                          ← Ce fichier
├── style.puml                         Style PlantUML commun
├── 00_synthese/
│   └── rapport_qualite.md             Audit qualité (63%)
├── 01_inventaire/                     Partie A — 7 fichiers
│   ├── README.md
│   ├── 01_environnement.md            OS, Python, Odoo, PostgreSQL
│   ├── 02_modules.md                  Modules custom, statistiques
│   ├── 03_catalogue_modeles.md        30+ modèles ORM
│   ├── 04_securite.md                 Groupes, ACL, règles
│   ├── 05_git_installation.md         Git, CI/CD, installation
│   └── 06_arborescence.md             Structure du projet
├── 02_branche_fonctionnelle/          Partie C — 26 fichiers
│   ├── README.md
│   ├── 01_contexte_statique.puml      Acteurs, système, systèmes externes
│   ├── 02_contexte_dynamique.puml     24 flux d'interaction
│   ├── 03_cas_utilisation.puml        22 cas d'utilisation globaux
│   ├── 04_etats_acte.puml             Cycle de vie d'un acte (7 états)
│   ├── 05_etats_ticket.puml           Cycle de vie d'un ticket (4 états)
│   ├── 06_sequence_saisie_acte.puml   Saisie d'un acte par l'agent
│   ├── 07_sequence_validation.puml    Validation par l'officier
│   ├── 08_activite_copie_guichet.puml Traitement d'une demande de copie
│   ├── 09_cas_utilisation_agent.puml  10 UC de l'Agent
│   ├── 10_cas_utilisation_officier.puml 5 UC de l'Officier
│   ├── 11_cas_utilisation_admin.puml  9 UC de l'Administrateur
│   ├── 12_cas_utilisation_regisseur.puml 6 UC du Régisseur
│   ├── 13_fiches_cas_utilisation.md   Fiches détaillées (28 UC)
│   ├── 14_sequence_transmission.puml  Transmission à l'officier
│   ├── 15_sequence_copie_pos.puml     Demande de copie au POS
│   ├── 16_sequence_marquer_traite.puml Marquer traité
│   ├── 17_sequence_paiement_quittance.puml Paiement et quittance
│   ├── 18_sequence_export.puml        Export ODF/Excel
│   ├── 19_sequence_rectification.puml Rectification d'acte refusé
│   ├── 20_sequence_audit.puml         Journal d'audit automatique
│   ├── 21_activite_cycle_vie_acte.puml Cycle de vie complet d'un acte
│   ├── 22_activite_export.puml        Processus d'export
│   ├── 23_activite_file_attente.puml  File d'attente du guichet
│   ├── 24_etats_quittance.puml        États de la quittance
│   ├── 25_classes_analyse.puml        Modèle du domaine (15+ classes)
│   └── 26_packages_analyse.puml       13 packages fonctionnels
├── 03_branche_technique/              Partie C — 6 fichiers
│   ├── README.md
│   ├── 01_deploiement.puml            Infrastructure de déploiement
│   ├── 02_composants.puml             Architecture en couches
│   ├── 03_packages.puml               Dépendances entre modules
│   ├── 04_exigences_adr.md            24 exigences + 7 ADR
│   ├── 05_architecture_couches.puml   6 couches logicielles
│   └── 06_flux_donnees.puml           Flux de données
├── 04_branche_realisation/            Partie C — 9 fichiers
│   ├── README.md
│   ├── 01_classes_conception.puml     Classes du domaine Actes
│   ├── 02_packages_conception.puml    Structure des 4 modules
│   ├── 03_classes_detaillees_actes.puml Classes actes (naissance/mariage/décès)
│   ├── 04_classes_detaillees_guichet.puml Classes guichet/compta/POS
│   ├── 05_classes_detaillees_audit.puml Classes audit/config/export
│   ├── 06_sequence_conception.puml    Vue → Python → ORM → Base
│   ├── 07_diagramme_objets.puml       Exemple : acte de naissance
│   ├── 08_carte_tests.md              Tests et pipeline CI
│   └── 09_matrice_tracabilite.md      28 UC ↔ code (238 lignes)
├── 05_base_de_donnees/                Partie C — 3 fichiers
│   ├── README.md
│   ├── 01_erd.puml                    ERD principal (10 tables)
│   ├── 02_erd_guichet_compta.puml     ERD guichet/compta/POS (8 tables)
│   └── 03_erd_audit_config.puml       ERD audit/config/séquences
└── exports/                           PNG/SVG (si plantuml disponible)
```

## Résumé

- **Pourcentage global** : 63 %
- **Niveau** : Démo/soutenance ✅ | Pilote mairie ❌ | Production multi-villes ❌
- **Diagrammes PlantUML** : 44 fichiers (25 fonctionnels + 5 techniques + 6 réalisation + 3 ERD)
- **Fichiers markdown** : 14 (7 inventaire + 1 rapport + 1 fiches UC + 1 exigences + 1 carte tests + 1 matrice traçabilité + 6 README)
- **Total fichiers** : 58 (44 .puml + 14 .md)
- **Problèmes P0** : 4 (secrets en clair, pas de chiffrement, cron désactivé, pas de signature électronique)

## Outils

Les diagrammes `.puml` peuvent être rendus avec :
- `plantuml fichier.puml` (si installé)
- PlantUML.jar : `java -jar plantuml.jar fichier.puml`
- Extension VS Code PlantUML
- https://www.planttext.com/

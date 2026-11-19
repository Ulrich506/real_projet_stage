# Branche Fonctionnelle — README

Diagrammes de capture des besoins fonctionnels (méthode 2TUP, branche gauche).

## Contexte et cas d'utilisation

| Fichier | Description |
|---------|-------------|
| [01_contexte_statique.puml](01_contexte_statique.puml) | Acteurs, système, systèmes externes |
| [02_contexte_dynamique.puml](02_contexte_dynamique.puml) | 24 flux d'interaction entre acteurs et système |
| [03_cas_utilisation.puml](03_cas_utilisation.puml) | 22 cas d'utilisation globaux avec includes |

## Cas d'utilisation par acteur

| Fichier | Description |
|---------|-------------|
| [09_cas_utilisation_agent.puml](09_cas_utilisation_agent.puml) | 10 cas d'utilisation de l'Agent |
| [10_cas_utilisation_officier.puml](10_cas_utilisation_officier.puml) | 5 cas d'utilisation de l'Officier |
| [11_cas_utilisation_admin.puml](11_cas_utilisation_admin.puml) | 9 cas d'utilisation de l'Administrateur |
| [12_cas_utilisation_regisseur.puml](12_cas_utilisation_regisseur.puml) | 6 cas d'utilisation du Régisseur |
| [13_fiches_cas_utilisation.md](13_fiches_cas_utilisation.md) | Fiches textuelles détaillées (28 UC avec pré/post-conditions, scénarios) |

## Diagrammes de séquence système

| Fichier | Description |
|---------|-------------|
| [06_sequence_saisie_acte.puml](06_sequence_saisie_acte.puml) | Saisie et transmission d'un acte par l'agent |
| [07_sequence_validation.puml](07_sequence_validation.puml) | Validation d'un acte par l'officier |
| [14_sequence_transmission.puml](14_sequence_transmission.puml) | Transmission d'un acte à l'officier |
| [15_sequence_copie_pos.puml](15_sequence_copie_pos.puml) | Demande de copie au point de vente |
| [16_sequence_marquer_traite.puml](16_sequence_marquer_traite.puml) | Marquer une demande comme traitée |
| [17_sequence_paiement_quittance.puml](17_sequence_paiement_quittance.puml) | Paiement et quittance de copie |
| [18_sequence_export.puml](18_sequence_export.puml) | Export des données (ODF/Excel) |
| [19_sequence_rectification.puml](19_sequence_rectification.puml) | Rectification d'un acte refusé |
| [20_sequence_audit.puml](20_sequence_audit.puml) | Journal d'audit automatique |

## Diagrammes d'activités

| Fichier | Description |
|---------|-------------|
| [08_activite_copie_guichet.puml](08_activite_copie_guichet.puml) | Processus de traitement d'une demande de copie |
| [21_activite_cycle_vie_acte.puml](21_activite_cycle_vie_acte.puml) | Cycle de vie complet d'un acte |
| [22_activite_export.puml](22_activite_export.puml) | Processus d'export des données |
| [23_activite_file_attente.puml](23_activite_file_attente.puml) | Traitement de la file d'attente du guichet |

## Diagrammes d'états-transitions

| Fichier | Description |
|---------|-------------|
| [04_etats_acte.puml](04_etats_acte.puml) | Cycle de vie d'un acte (7 états) |
| [05_etats_ticket.puml](05_etats_ticket.puml) | Cycle de vie d'un ticket guichet (4 états) |
| [24_etats_quittance.puml](24_etats_quittance.puml) | États de la quittance de paiement |

## Classes et packages d'analyse

| Fichier | Description |
|---------|-------------|
| [25_classes_analyse.puml](25_classes_analyse.puml) | Modèle du domaine (8 packages, 15+ classes) |
| [26_packages_analyse.puml](26_packages_analyse.puml) | 13 packages fonctionnels avec dépendances |

**Total : 26 fichiers (25 .puml + 1 .md)**

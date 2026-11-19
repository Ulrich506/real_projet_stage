# Branche Technique — README

Diagrammes de capture des besoins techniques et architecture (méthode 2TUP, branche droite).

## Architecture et déploiement

| Fichier | Description |
|---------|-------------|
| [01_deploiement.puml](01_deploiement.puml) | Infrastructure : navigateurs, serveur Odoo, PostgreSQL, POS, GitHub |
| [02_composants.puml](02_composants.puml) | Architecture en couches : présentation, contrôle, métier, sécurité, persistance |
| [03_packages.puml](03_packages.puml) | Dépendances entre les 4 modules custom |

## Exigences et décisions d'architecture

| Fichier | Description |
|---------|-------------|
| [04_exigences_adr.md](04_exigences_adr.md) | 24 exigences techniques + 7 ADR avec preuves |

## Architecture détaillée

| Fichier | Description |
|---------|-------------|
| [05_architecture_couches.puml](05_architecture_couches.puml) | 6 couches logicielles (présentation, métier, sécurité, persistance, config, intégration) |
| [06_flux_donnees.puml](06_flux_donnees.puml) | Flux de données entre acteurs, système et base |

**Total : 6 fichiers (4 .puml + 1 .md + 1 README)**

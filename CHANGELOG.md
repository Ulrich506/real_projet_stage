# Changelog

## [17.0.2.1.12] — 2026-11-15

### Modules

- **etat_civil** (17.0.2.1.12) : Gestion des citoyens, actes d'état civil, registres, demandes de guichet
- **etat_civil_account** (17.0.1.1.2) : Passerelle comptable avec facturation
- **etat_civil_pos** (17.0.1.0.1) : Encaissement au point de vente

### Corrections

- Correction des numéros de version des manifests : format Odoo 17 (`17.0.x.y.z`)
- Stabilisation de l'environnement Python 3.12 avec les dépendances requises
- Nettoyage de la configuration pour éviter les conflits Odoo 17/18

### Améliorations

- Ajout des modèles `audit_log` et `piece_requise`
- Amélioration des vues et des rapports
- Tests unitaires pour la facturation et le flux POS

## [17.0.2.1.9] — 2026-11-14

- Version de base avant la professionnalisation du dépôt
- Modules fonctionnels avec Odoo 17 Community

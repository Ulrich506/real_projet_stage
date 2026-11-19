# Branche Réalisation — README

Diagrammes de conception, codage, tests et recette (méthode 2TUP, branche réalisation).

## Conception préliminaire

| Fichier | Description |
|---------|-------------|
| [01_classes_conception.puml](01_classes_conception.puml) | Diagramme de classes du domaine Actes avec héritage |
| [02_packages_conception.puml](02_packages_conception.puml) | Structure des 4 modules Odoo avec sous-packages |

## Conception détaillée — Classes par domaine

| Fichier | Description |
|---------|-------------|
| [03_classes_detaillees_actes.puml](03_classes_detaillees_actes.puml) | Actes : acte_officiel (abstrait), naissance, mariage, décès, registre, centre |
| [04_classes_detaillees_guichet.puml](04_classes_detaillees_guichet.puml) | Guichet/Compta : individu, demande, copie, paiement, tarif, POS |
| [05_classes_detaillees_audit.puml](05_classes_detaillees_audit.puml) | Audit/Config : audit mixin, audit log, mentions, pièces, config, export |

## Séquences et objets

| Fichier | Description |
|---------|-------------|
| [06_sequence_conception.puml](06_sequence_conception.puml) | Vue → Méthode Python → ORM → Base (create, write, transition) |
| [07_diagramme_objets.puml](07_diagramme_objets.puml) | Exemple concret : acte de naissance à la Mairie d'Antananarivo |

## Tests et traçabilité

| Fichier | Description |
|---------|-------------|
| [08_carte_tests.md](08_carte_tests.md) | 22 fichiers de tests, couverture estimée, pipeline CI |
| [09_matrice_tracabilite.md](09_matrice_tracabilite.md) | 28 cas d'utilisation ↔ modèles/vues/méthodes (238 lignes) |

**Total : 9 fichiers (6 .puml + 2 .md + 1 README)**

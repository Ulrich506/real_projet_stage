# Carte des tests et pipeline CI

## Tests automatisés existants

### Module etat_civil

| Fichier | Description | Type |
|---------|-------------|------|
| `tests/test_demande_guichet_status.py` | Tests des transitions de statut des demandes guichet | Unit |
| `tests/test_acte_workflow.py` (déduit) | Tests du workflow des actes | Unit |
| `tests/test_individu.py` (déduit) | Tests du modèle Individu | Unit |
| `tests/test_audit_log.py` (déduit) | Tests du journal d'audit | Unit |
| `tests/test_security.py` (déduit) | Tests des ACL et règles d'accès | Unit |
| `tests/test_piece_justificative.py` (déduit) | Tests des pièces justificatives | Unit |
| `tests/test_mention_marginale.py` (déduit) | Tests des mentions marginales | Unit |
| `tests/test_registre.py` (déduit) | Tests des registres | Unit |
| `tests/test_config_settings.py` (déduit) | Tests de la configuration | Unit |
| `tests/test_export.py` (déduit) | Tests d'export ODF/Excel | Unit |
| `tests/test_import_export_log.py` (déduit) | Tests du journal import/export | Unit |
| `tests/test_malagasy_date_utils.py` (déduit) | Tests des utilitaires de dates | Unit |

> **Note** : 22 fichiers de tests détectés dans `etat_civil/tests/`. Seuls les noms confirmés sont listés sans "(déduit)". Les autres sont déduits de la structure du module.

### Modules autres

| Module | Tests détectés |
|--------|---------------|
| etat_civil_account | Non vérifié |
| etat_civil_pos | Non vérifié |
| etat_civil_auth_email | Non vérifié |

## Couverture estimée

| Domaine | Couverture estimée | Preuve |
|---------|-------------------|--------|
| Workflow actes | Partielle | Tests de statut existants |
| Sécurité (ACL) | Partielle | Tests de rôle détectés |
| Audit log | Partielle | Tests d'immuabilité |
| Export | Non vérifié | Fichiers de tests présents |
| Comptabilité | Non vérifié | Non inspecté |
| POS | Non vérifié | Non inspecté |

> ⚠️ **La couverture exacte n'a pas pu être mesurée** sans exécution des tests (interdit en mode lecture seule).

## Pipeline CI/CD (GitHub Actions)

### Workflows détectés

| Workflow | Déclencheur | Étapes |
|----------|------------|--------|
| `ci.yml` (déduit) | push, pull_request | Lint, tests unitaires |
| `lint.yml` (déduit) | push, pull_request | Flake8 / Pylint |

### Étapes typiques

```
1. Checkout du code
2. Installation des dépendances Python (requirements.txt)
3. Lint du code Python
4. Exécution des tests Odoo
5. Rapport de couverture (si configuré)
```

> ⚠️ **Les workflows exacts n'ont pas pu être inspectés** en détail. La présence de `.github/workflows/` a été détectée.

## Recommandations pour les tests

1. **Augmenter la couverture** : viser 80 % minimum sur les modèles core.
2. **Tests d'intégration** : ajouter des tests de bout en bout pour le workflow acte.
3. **Tests de sécurité** : vérifier les ACL et règles d'accès par programme.
4. **Tests de performance** : benchmarks sur les requêtes fréquentes.
5. **Tests de migration** : vérifier les scripts de migration entre versions.

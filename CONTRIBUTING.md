# Contribuer

Merci de votre intérêt pour ce projet !

## Avant de contribuer

1. **Lisez la documentation** : [INSTALL.md](documentation/INSTALL.md), [CONFIGURATION.md](documentation/CONFIGURATION.md)
2. **Créez une branche** : `git checkout -b feature/votre-fonctionnalite`
3. **Testez localement** : Assurez-vous que les modifications ne cassent pas le service existant

## Conventions de commit

Suivez le format [Conventional Commits](https://www.conventionalcommits.org/) :

```
type(scope): description

- feat: nouvelle fonctionnalité
- fix: correction de bug
- docs: documentation
- chore: tâches de maintenance
- refactor: refactoring de code
- test: ajout ou modification de tests
```

Exemples :
```
feat(etat_civil): ajouter le modèle piece_requise
fix(etat_civil_account): corriger le calcul de la facture
docs: mettre à jour le guide d'installation
```

## Structure des modules

Chaque module suit la structure standard Odoo :

```
custom_addons/nom_module/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── *.py
├── views/
│   └── *.xml
├── security/
│   ├── ir.model.access.csv
│   └── security.xml
├── data/
│   └── *.xml
├── reports/
│   └── *.xml
└── static/
    └── src/
```

## Tests

Avant de soumettre une pull request :

1. Vérifiez que le service démarre sans erreur : `./odoo17.sh start`
2. Consultez les logs : `tail -f logs/odoo17.log`
3. Assurez-vous que les modules se chargent correctement

## Soumission de code

1. Créez une branche depuis `main`
2. Faites des commits atomiques et bien documentés
3. Ouvrez une pull request avec une description claire des changements

## Licence

En contribuant, vous acceptez que vos contributions soient sous licence LGPL-3.

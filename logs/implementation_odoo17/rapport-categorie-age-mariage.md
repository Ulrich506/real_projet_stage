# Rapport — Catégorie d'âge et restriction des conjoints

## Modifications
- `models/individu.py` : ajout de `categorie_age` et `eligible_conjoint`, calcul exact avec `dateutil.relativedelta`, gestion de la date inconnue et actualisation quotidienne planifiée.
- `models/individu.py` : modification de `date_naissance` pour permettre une valeur inconnue et contrôle lors du changement de naissance d'un individu déjà associé à un mariage.
- `models/acte_mariage.py` : ajout des contrôles serveur du double conjoint, de la date de naissance absente et de l'âge inférieur à 18 ans.
- `views/individu_views.xml` : affichage de la catégorie en formulaire et liste, filtres et regroupement par catégorie.
- `views/acte_mariage_views.xml` : domaines XML excluant les individus sans naissance et les individus non éligibles.
- `data/age_category_cron.xml` : tâche quotidienne invalidant et recalculant les valeurs stockées.
- `tests/test_individu_age_marriage.py` : tests de catégories, anniversaire, année bissextile, date inconnue, contournement ORM, changement de naissance et double conjoint.
- Version du module portée à `17.0.2.1.9`.

## Règles fonctionnelles
- Nourrisson : 0 à moins de 2 ans.
- Enfant : 2 à moins de 12 ans.
- Adolescent : 12 à moins de 18 ans.
- Adulte : 18 à moins de 60 ans.
- Senior : 60 ans et plus.
- Date inconnue : « Non déterminé » et non éligible.
- La restriction matrimoniale utilise la date réelle de naissance et `relativedelta`, avec l'âge vérifié à la date du mariage lorsque elle existe.

## Vérifications exécutées
- `compileall` sur les modèles et tests : réussi après correction de la dernière syntaxe.
- Validation XML avec `xmllint` : réussie pour les vues et le cron.
- AST Python : réussie.
- `git diff --check` sur les fichiers modifiés : réussi.

## Tests serveur
Les tests Odoo n'ont pas été lancés sur la base principale, conformément aux protections de l'environnement. Une base isolée a été prévue dans le contexte du projet, mais l'accès PostgreSQL disponible via les identifiants de l'assistant n'a pas permis de vérifier cette base; aucune base ni aucun filestore n'a donc été modifié.

## Limitations restantes
- Validation Odoo TransactionCase non exécutée dans cette session.
- Mise à jour du module sur une base isolée et démarrage navigateur de la vue Individu/Marriage à effectuer après provisionnement des droits PostgreSQL requis.

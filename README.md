# Gestion d’état civil

Application de gestion des actes et démarches d’état civil construite sur
Odoo 17. Le dépôt contient les sources Odoo Community utilisées par ce projet,
les modules métier et les outils locaux de maintenance.

> **Prudence pour les opérations réelles.** La configuration locale historique
> désigne `etat_civil_odoo17_test`, base confirmée comme production. N’utilisez
> jamais cette base pour une installation, une mise à jour ou un essai. Les
> commandes de validation doivent viser une base isolée sauvegardée. La
> configuration système Odoo n’a pas été vérifiée et le service `odoo.service`
> était inactif lors du dernier audit.

## Fonctionnalités

- Gestion des actes de naissance, mariage et décès, registres, centres,
  citoyens, pièces justificatives, mentions marginales et guichet.
- Workflow contrôlé par rôles Agent, Officier et Administrateur d’état civil,
  avec traçabilité, restrictions par centre et rapports PDF.
- Dossiers de demande de copie, tarifs, factures Odoo, versements et
  quittances via `etat_civil_account`.
- Encaissements POS reliés à la facture existante via `etat_civil_pos`.
- Connexion par adresse e-mail, optionnelle, via `etat_civil_auth_email`.
- Extraits PDF distincts pour les actes et mentions, et quittances liées aux
  encaissements rapprochés.

Les procédures administratives et comptables doivent être validées par la
commune et son comptable avant usage officiel.

## Architecture

| Chemin | Responsabilité |
|---|---|
| `odoo/` | Sources natives Odoo 17 utilisées par ce checkout; ne pas renommer ni modifier dans le cadre du nettoyage du projet |
| `custom_addons/etat_civil/` | Workflow et données métier d’état civil |
| `custom_addons/etat_civil_account/` | Facturation, demandes de copie et quittances |
| `custom_addons/etat_civil_pos/` | Encaissement POS des factures de copie |
| `custom_addons/etat_civil_auth_email/` | Authentification par e-mail, optionnelle |
| `configuration/` | Exemples expurgés de configuration; les fichiers opérationnels restent locaux et non versionnés |
| `documentation/` | Inventaires, architecture, installation et rapports techniques |
| `requirements/` | Dépendances Python additionnelles aux exigences du checkout Odoo |
| `scripts/` | Outils de maintenance non destructifs |

Les filestores, sessions, journaux, bases de données, dumps et sauvegardes sont
des données d’exécution ou d’exploitation. Ils ne font pas partie d’une
livraison logicielle et doivent rester protégés, même lorsqu’ils sont présents
localement dans les dossiers historiques `data/` et `logs/`.

## Modules Odoo

| Module technique | Dépendances principales | Usage |
|---|---|---|
| `etat_civil` | `base`, `mail`, `web` | Application principale |
| `etat_civil_account` | `etat_civil`, `account` | Factures et paiements de copies |
| `etat_civil_pos` | `etat_civil_account`, `point_of_sale` | Encaissement des factures au POS |
| `etat_civil_auth_email` | `base`, `web`, `etat_civil` | Connexion par e-mail, en option |

Ne renommez pas ces noms techniques : ils sont utilisés par les manifests,
les identifiants externes, les migrations et le registre Odoo. De même, les
fichiers `tests/test_*.py` et leur structure sont nécessaires à la découverte
native des tests Odoo.

## Prérequis

- Sources Odoo 17 disponibles dans `odoo/`.
- PostgreSQL compatible avec la version Odoo déployée.
- Python et les dépendances définis par `odoo/requirements.txt`.
- Une base dédiée et un filestore sauvegardés pour les installations et tests.

L’environnement local audité répondait à `Odoo Server 17.0`, Python 3.14.4 et
PostgreSQL 18.6. Cela décrit cet environnement seulement; ce n’est pas une
certification de compatibilité de production. Les services Odoo installés
hors de ce checkout doivent utiliser leur propre configuration vérifiée.

## Installation locale sur une base de développement

1. Créez un environnement virtuel et installez les dépendances de base et
   celles des imports/exports optionnels :

   ```bash
   python3 -m venv venv
   ./venv/bin/pip install -r odoo/requirements.txt
   ./venv/bin/pip install -r requirements/custom-addons.txt
   ```

2. Créez une configuration privée à partir du modèle :

   ```bash
   if test -e config/odoo17.conf; then
     echo "Configuration existante : ne pas l'écraser."
   else
     cp configuration/odoo17.conf.example config/odoo17.conf
     chmod 600 config/odoo17.conf
   fi
   ```

   Modifiez localement tous les champs `CHANGE_ME` et les chemins. Le fichier
   `config/odoo17.conf` est ignoré par Git. Ne copiez pas les paramètres de
   production dans une base de test et ne publiez pas de secrets.

3. Créez ou restaurez une base **de développement isolée** nommée
   `gestion_etat_civil_dev`, avec son filestore. Installez les modules
   nécessaires :

   ```bash
   PYTHONPATH="$PWD/odoo:$PWD" ./venv/bin/python odoo/odoo-bin \
     --config=config/odoo17.conf \
     --database=gestion_etat_civil_dev \
     --init=etat_civil,etat_civil_account,etat_civil_pos \
     --stop-after-init --no-http
   ```

   Pour activer la connexion par e-mail, ajoutez `etat_civil_auth_email` à la
   liste après avoir vérifié ses prérequis. Cette commande ne doit jamais être
   lancée avec le nom de la base de production.

Le chemin Python local est placé avant les bibliothèques système afin que le
processus utilise les sources Odoo 17 du dépôt. Le binaire système
`/usr/bin/odoo` a échoué au contrôle d’import lors du dernier audit; ne
considérez pas le service système comme validé.

## Tests

Exécutez les tests uniquement sur une base de validation dédiée et sauvegardée.
Exemple pour la suite complète des modules état civil et paiement :

```bash
PYTHONPATH="$PWD/odoo:$PWD" ./venv/bin/python odoo/odoo-bin \
  --config=config/odoo17.conf \
  --database=gestion_etat_civil_dev \
  --update=etat_civil,etat_civil_account,etat_civil_pos \
  --test-enable \
  --test-tags=/etat_civil,/etat_civil_account,/etat_civil_pos \
  --stop-after-init --no-http
```

Le code de sortie de la commande et le résumé `odoo.tests.result` font foi.
L’absence de démarrage ou un arrêt avant l’exécution des tests ne constitue pas
un résultat réussi. La suite `etat_civil_auth_email` se teste séparément si ce
module est installé.

## Démarrage et maintenance

Le script local `odoo17.sh` propose `start`, `stop`, `status`, `restart`,
`update` et `logs`. Il utilise `config/odoo17.conf`; vérifiez d’abord que
celle-ci désigne une base de développement. Le script refuse les mises à jour
de `etat_civil_odoo17_test` et ne doit pas être utilisé pour contourner cette
protection.

Pour contrôler les bases accessibles et vérifier les sauvegardes :

```bash
./scripts/cleanup_odoo17.sh --list-databases
./scripts/cleanup_odoo17.sh --verify-backups
```

Ces commandes d’audit ne remplacent pas une sauvegarde/restauration vérifiée.
Les procédures système, unités systemd et configurations sous `/etc/odoo`
doivent être examinées séparément par un administrateur autorisé.

## Sauvegarde et restauration

Stockez les sauvegardes hors du checkout, avec des permissions restreintes.
Sauvegardez ensemble la base PostgreSQL et le filestore associé, puis vérifiez
les deux archives avant toute opération :

```bash
pg_dump -Fc --dbname=gestion_etat_civil_dev \
  --file=/chemin-securise/gestion_etat_civil_dev.dump
pg_restore --list /chemin-securise/gestion_etat_civil_dev.dump
```

L’emplacement du filestore dépend de `data_dir` dans la configuration Odoo.
Archivez le répertoire exact `filestore/<nom-de-la-base>` et vérifiez son
contenu avant de considérer la sauvegarde complète. Une restauration doit
d’abord être faite dans une base isolée, avec le nom de base et le filestore
correspondants. Ne renommez et ne supprimez aucune base existante sans
autorisation nominative, sauvegarde vérifiée et plan de retour arrière.

## Sécurité et licence

- Les fichiers de configuration opérationnels, mots de passe, filestores,
  sessions, journaux et sauvegardes ne doivent pas être ajoutés à Git.
- Le fichier de configuration local historique a été suivi dans l’historique
  Git. Son retrait de la version courante ne supprime pas les anciennes
  versions; la gestion d’une rotation de secret et d’une éventuelle purge
  d’historique nécessite une procédure séparée.
- Les manifests des modules personnalisés déclarent `LGPL-3`. La licence
  globale des livrables reste à confirmer; aucun fichier `LICENSE` racine
  n’est fourni tant que cette décision n’est pas prise.

## Documentation

- [Index de la documentation](documentation/README.md)
- [Inventaire et risques du dépôt](documentation/architecture/project-inventory.md)
- [Audit de correction de facturation](documentation/maintenance/audit_correction_facturation.md)
- [Validation POS en MGA](documentation/maintenance/finalisation_audit_pos_mga.md)

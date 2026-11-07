# Rapport — Mise à jour `all` des modules Odoo

## Objet

Évolution de `odoo17.sh` pour permettre la commande :

```text
odoo17 update NOM_BASE [MODULE|all]
```

## Audit initial

- Script examiné avant modification : `odoo17.sh`
- Branche Git observée : `main`
- Sauvegarde exacte créée avant toute modification :
  - `logs/implementation_odoo17/odoo17.sh.before-update-all.20261106091646`
- Préservation vérifiée : l'intervention ne remplace aucun fichier préexistant.
- L'état initial du script contenait déjà les protections suivantes, conservées :
  - obligation de fournir explicitement le nom de la base;
  - validation du nom de la base;
  - refus de mise à jour si une instance Odoo gérée correspond à la configuration est active;
  - absence d'arrêt automatique du serveur;
  - exécution Odoo avec `--stop-after-init`, `--no-http` et un fichier de log dédié.
- Droits du script avant/après modification : mode `775`, propriétaire inchangé.

## Modification

Valeur de module adaptée comme demandé :

- absence de module : `all`;
- module `all` : `all`;
- module unique : conservé tel quel;
- liste séparée par virgules : conservée pour transmission à Odoo;
- transmission effective conservée sous la forme `-u "$module"`.

L'option `-u all` reste utilisée uniquement par la mise à jour Odoo. Elle ne constitue pas une demande d'installation et laisse Odoo mettre à jour les modules déjà installés selon son comportement natif.

Les validations acceptent uniquement les lettres ASCII, les chiffres et les underscores, avec des virgules autorisées uniquement entre les noms de modules. Les noms invalides sont refusés avant toute invocation Odoo.

La commande `update` n'a jamais arrêté automatiquement un serveur actif. Elle vérifie d'abord `find_odoo_pid` et retourne une erreur si une instance est détectée.

## Aide

L'aide affiche désormais notamment :

```text
odoo17 update NOM_BASE [MODULE|all]
```

Elle précise aussi que l'omission du module met à jour tous les modules déjà installés.

## Tests réalisés

### Syntaxe

- `bash -n odoo17.sh` : succès.
- `git diff --check -- odoo17.sh` : succès.

### Arguments sans vraie mise à jour

Test réalisé avec un exécutant Python factice, sans modifier de base, de filestore ou de configuration :

- `update ma_base_test` → argument reçu : `-u all`;
- `update ma_base_test all` → argument reçu : `-u all`;
- `update ma_base_test etat_civil` → argument reçu : `-u etat_civil`;
- `update ma_base_test etat_civil,etat_civil_account` → argument reçu : `-u etat_civil,etat_civil_account`.

Les quatre cas ont retourné le résultat factice attendu sans accéder à PostgreSQL ni lancer Odoo réel.

### Refus

- Absence de base : code `2`;
- base contenant un caractère invalide : code `2`;
- module contenant un caractère invalide : code `2`;
- instance Odoo simulée active : code `1`, aucune commande Odoo factice exécutée.

### Vérification active

Le nom de la base reste toujours obligatoire. Le nom n'est jamais déduit d'une variable ou d'une base par défaut.

## Commandes non modifiées

Les fonctions et le comportement de :

- `start`;
- `stop`;
- `restart`;
- `status`;
- `logs`;

n'ont pas été remplacés ni étendus dans cette intervention. La section `stop_odoo` correspondante était byte-for-byte identique dans la sauvegarde et le script actuel lors du contrôle.

## Fichiers

- Script modifié : `odoo17.sh`
- Sauvegarde exacte : `logs/implementation_odoo17/odoo17.sh.before-update-all.20261106091646`
- Rapport : `logs/implementation_odoo17/rapport-update-all-modules.md`

## Limites

- Aucun module n'a été réellement mis à jour.
- Aucune base ni aucun filestore n'a été modifié.
- Aucun serveur actif n'a été arrêté ou redémarré.
- Aucun test avec une vraie instance PostgreSQL/Odoo `-u all` n'a été effectué, conformément aux interdictions.
- Le comportement natif exact de `-u all` reste celui fourni par Odoo 17 : mise à jour des modules installés, sans installation globale de tous les modules disponibles.

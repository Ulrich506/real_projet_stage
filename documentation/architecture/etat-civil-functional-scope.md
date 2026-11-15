# État civil — Périmètre fonctionnel

Odoo Web est l’interface principale de gestion. Les références à une
application mobile décrivent un client externe; son code source n’est pas
présent dans ce dépôt.

## Correction principale

Le champ `qr_code_image` est déclaré dans le modèle abstrait
`etat.civil.acte.officiel` puis hérité par les trois actes :

- `etat.civil.acte.naissance`
- `etat.civil.acte.mariage`
- `etat.civil.acte.deces`

Les formulaires référencent un champ présent dans le registre lorsque le
manifest et les modèles chargés sont cohérents.

`qr_code_signature` contient la donnée de vérification QR (texte), alors que
`qr_code_image` contient l'image PNG encodée en base64.

## Parcours métier

- Les actes restent des brouillons jusqu’à leur validation par un officier.
- Les pièces obligatoires dépendent du type de dossier et des informations
  saisies. Leur scan ou leur photo est facultatif ; l’officier en vérifie la
  réception avant de valider.
- Une naissance à l’hôpital demande la déclaration de l’hôpital. Pour une
  naissance à la maison, la personne déclarante est requise. Les pièces de
  filiation légitime ou illégitime sont affichées selon le cas.
- Un mariage validé crée une mention pour chaque conjoint et conserve le suivi
  de notification à sa commune de naissance.
- Les mentions (reconnaissance, adoption simple, mariage, divorce, décès,
  veuvage et changement de nom) sont associées à la personne ou à l’acte visé.
  L’adoption complexe relève de la justice et n’est pas un parcours communal.

Les règles de procédure décrivent le fonctionnement attendu pour ce projet et
doivent être confirmées par la commune avant tout usage officiel.

Dans l’application Flutter, le Malagasy est sélectionné par défaut et le
français est disponible. La traduction des libellés est encore partielle ; les
textes d’Odoo dépendent également des traductions installées et de la langue du
compte utilisateur.

## Modules Odoo à activer

Obligatoires pour ce module :

- `base`
- `web`
- `mail`

Optionnels selon le périmètre et les modules réellement disponibles :

- `contacts`
- `documents`
- `auth_signup`
- `l10n_mg` si le module de localisation Madagascar est disponible dans ton installation et réellement utile à ton périmètre.

## Déploiement

Les scripts `deploy_validate_etat_civil.sh` décrits dans les notes historiques
ne sont pas présents dans ce dépôt. Utilisez les instructions du [README
racine](../../README.md) et une base de développement isolée. Ne supprimez pas
une base PostgreSQL pour corriger une erreur de vue et ne mettez pas à jour la
base de production pour diagnostiquer un écart de code.

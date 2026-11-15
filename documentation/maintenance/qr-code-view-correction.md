
# Historique de maintenance — vue du QR de vérification

## Cause constatée

Dans la version examinée, `qr_code_image` est **déclaré dans le modèle abstrait**
`etat.civil.acte.officiel` puis hérité par `etat.civil.acte.mariage`.

`models/__init__.py` importe bien `acte_officiel` avant `acte_mariage`.

L'archive historique examinée ne contenait pas de fichier
`views/acte_mariage_views.xml` à l'emplacement annoncé dans l'erreur. Elle
contient `views/actes_mariage_deces_views.xml`. Cela pouvait signifier que le fichier
chargé par l'instance Odoo et l'archive analysée peuvent être de versions
différentes, ou que la base utilise encore une ancienne vue.

## Correction apportée à l’époque

Le module 2.0.2 sépare désormais les vues de mariage et de décès :

- `views/acte_mariage_views.xml`
- `views/acte_deces_views.xml`

et les référence explicitement dans `__manifest__.py`.

La déclaration du champ critique reste centralisée dans :

`models/acte_officiel.py`

```python
qr_code_image = fields.Binary(
    string="QR de vérification",
    readonly=True,
    attachment=False,
)
```

Ce document est un historique, pas une procédure de déploiement. Les chemins
et scripts de déploiement mentionnés dans l’ancienne version ne sont pas
présents dans ce dépôt. Pour un diagnostic actuel, vérifier en lecture seule
la version du code, le manifeste, les vues actives et le schéma d’une base de
test restaurée. Suivre le guide racine avant toute mise à jour.

Ne pas supprimer manuellement les colonnes SQL de `ir_model_fields` ou des
tables métier pour résoudre ce type de problème. La mise à jour de la
production nécessite une autorisation distincte et une sauvegarde vérifiée.

# Inventaire — Modules Custom

## Modules Odoo custom

| Module | Version | Catégorie | Dépendances | Type |
|--------|---------|-----------|-------------|------|
| etat_civil | 17.0.2.1.30 | Public Sector | base, mail, web | Application |
| etat_civil_account | 17.0.1.1.6 | Services/Accounting | etat_civil, account | Module |
| etat_civil_pos | 17.0.1.0.9 | Services/Accounting | etat_civil_account, point_of_sale | Module |
| etat_civil_auth_email | 17.0.1.0.2 | Administration | base, web, etat_civil | Module |

## Chaîne de dépendances

```
etat_civil (base)
  └── etat_civil_account (comptabilité)
        └── etat_civil_pos (point de vente)
etat_civil_auth_email (authentification e-mail)
```

## Statistiques par module

### etat_civil

| Catégorie | Comptage |
|-----------|----------|
| Fichiers Python (modèles) | 17 fichiers, 4743 lignes |
| Fichiers Python (wizards) | 13 fichiers |
| Fichiers Python (contrôleurs) | 4 fichiers |
| Fichiers Python (tests) | 22 fichiers |
| Vues XML | 27 fichiers |
| Rapports QWeb | 12 fichiers |
| Données XML | 16 fichiers |
| Démo XML | 3 fichiers |
| Sécurité XML | 1 fichier (security.xml) |
| ACL CSV | 1 fichier (82 lignes) |
| JavaScript/OWL | 3 fichiers JS + 2 fichiers XML |
| SCSS | 1 fichier |
| Modèles ORM | 16 (voir catalogue) |
| Groupes sécurité | 4 (agent, officier, admin, tech_admin) |
| Règles ir.rule | ~15 règles |
| Séquences | 4+ (actes naissance/mariage/décès, mentions, demandes) |
| Cron | 1 (mise à jour catégorie d'âge) |

### etat_civil_account

| Catégorie | Comptage |
|-----------|----------|
| Fichiers Python (modèles) | 8 fichiers, 1587 lignes |
| Vues XML | ~6 fichiers |
| Rapports QWeb | 2 fichiers |
| Sécurité XML | 1 fichier |
| ACL CSV | 1 fichier |
| Modèles ORM | 7 |

### etat_civil_pos

| Catégorie | Comptage |
|-----------|----------|
| Fichiers Python (modèles) | 6 fichiers, 819 lignes |
| Vues XML | ~4 fichiers |
| Rapports QWeb | 1 fichier |
| Données XML | 4 fichiers |
| Sécurité XML | 2 fichiers |
| ACL CSV | 1 fichier |
| Assets POS (JS/XML) | plusieurs fichiers |
| Modèles ORM | 5 |

### etat_civil_auth_email

| Catégorie | Comptage |
|-----------|----------|
| Fichiers Python (modèles) | 2 fichiers, 147 lignes |
| Vues XML | 1 fichier (login_templates.xml) |
| Modèles ORM | 1 (extension res.users) |
| Hooks | pre_init_hook, post_init_hook |

## Statistiques globales

| Métrique | Valeur |
|----------|--------|
| Lignes Python totales (modèles) | 7904 |
| Fichiers XML totaux | 64 |
| Fichiers JavaScript | 6 |
| Fichiers SCSS | 1 |
| Fichiers CSV | 3 |
| Fichiers de tests | 22 |
| Contrôleurs HTTP | 4 |
| Wizards | 13 |
| Vues XML | 27 |
| Rapports QWeb | 12 |
| Données XML | 16 |
| Démo XML | 3 |

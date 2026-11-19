# Inventaire — Arborescence du Projet

## Structure à 3 niveaux

```
stage_l3_odoo/
├── custom_addons/                          Modules custom
│   ├── etat_civil/                         Application principale
│   │   ├── __manifest__.py                 Manifest (v17.0.2.1.30)
│   │   ├── models/                         17 fichiers Python (4743 lignes)
│   │   │   ├── individu.py                 Citoyen (493 lignes)
│   │   │   ├── acte_officiel.py            Abstrait — workflow actes (1410 lignes)
│   │   │   ├── acte_naissance.py           Acte naissance (224 lignes)
│   │   │   ├── acte_mariage.py             Acte mariage (326 lignes)
│   │   │   ├── acte_deces.py               Acte décès (122 lignes)
│   │   │   ├── mention_marginale.py        Mentions (373 lignes)
│   │   │   ├── piece_justificative.py      Pièces (544 lignes)
│   │   │   ├── piece_requise.py            Config pièces requises (143 lignes)
│   │   │   ├── demande_guichet.py          Tickets guichet (516 lignes)
│   │   │   ├── audit_log.py                Journal audit (366 lignes)
│   │   │   ├── registre.py                 Centre + Registre (107 lignes)
│   │   │   ├── config_settings.py          Config identité (345 lignes)
│   │   │   ├── import_export_log.py        Journal import/export (35 lignes)
│   │   │   ├── res_users.py                Extension utilisateur (123 lignes)
│   │   │   ├── malagasy_date_utils.py      Utilitaires dates (337 lignes)
│   │   │   └── officier_views_hook.py      Hook vues officier (92 lignes)
│   │   ├── views/                          27 fichiers XML
│   │   │   ├── menus.xml                   Menus principaux
│   │   │   ├── individu_views.xml          Vues citoyen
│   │   │   ├── acte_naissance_views.xml    Vues acte naissance
│   │   │   ├── acte_mariage_views.xml      Vues acte mariage
│   │   │   ├── acte_deces_views.xml        Vues acte décès
│   │   │   ├── mentions_marginales_views.xml
│   │   │   ├── demandes_guichet_views.xml  Vues tickets guichet
│   │   │   ├── audit_log_views.xml         Vues journal audit
│   │   │   ├── config_settings_views.xml   Vues configuration
│   │   │   └── ...                         Autres vues
│   │   ├── wizards/                        13 fichiers Python + XML
│   │   │   ├── creer_acte_wizard*          Wizard création acte
│   │   │   ├── transmission_acte_wizard*   Wizard transmission
│   │   │   ├── retour_correction_wizard*   Wizard retour correction
│   │   │   ├── annulation_acte_wizard*     Wizard annulation
│   │   │   └── ...                         Autres wizards
│   │   ├── controllers/                    4 fichiers Python
│   │   │   ├── main.py                     Routes HTTP (download/imprimer)
│   │   │   └── ...
│   │   ├── security/                       Sécurité
│   │   │   ├── security.xml                Groupes + règles ir.rule
│   │   │   └── ir.model.access.csv         82 lignes ACL
│   │   ├── data/                           16 fichiers XML
│   │   │   ├── acte_sequence.xml           Séquences actes
│   │   │   ├── demande_guichet_sequence.xml
│   │   │   ├── mention_sequence.xml        Séquences mentions
│   │   │   ├── piece_requise_data.xml      Données pièces requises
│   │   │   ├── config_identity_data.xml    Identité commune
│   │   │   └── ...
│   │   ├── reports/                        12 fichiers XML (QWeb)
│   │   │   ├── actes_reports.xml           Rapports actes
│   │   │   ├── citizen_export_report.xml   Export citoyen
│   │   │   └── ...
│   │   ├── static/                         Assets
│   │   │   └── src/
│   │   │       ├── scss/                   1 fichier SCSS
│   │   │       ├── js/                     3 fichiers JS (OWL)
│   │   │       └── xml/                    2 fichiers XML (templates JS)
│   │   ├── tests/                          22 fichiers de tests
│   │   └── demo/                           3 fichiers XML
│   ├── etat_civil_account/                 Passerelle comptable
│   │   ├── __manifest__.py                 v17.0.1.1.6
│   │   ├── models/                         8 fichiers (1587 lignes)
│   │   │   ├── copy_request.py             Demande copie (836 lignes)
│   │   │   ├── copy_payment.py             Paiement (196 lignes)
│   │   │   ├── copy_tariff.py              Tarifs (101 lignes)
│   │   │   ├── guichet.py                  Guichet comptable (209 lignes)
│   │   │   ├── acte_copy_link.py           Lien acte-copie (70 lignes)
│   │   │   ├── operation_event.py          Événement opération (38 lignes)
│   │   │   └── account_move.py             Extension facture (29 lignes)
│   │   ├── views/                          Vues
│   │   ├── report/                         2 rapports QWeb
│   │   ├── security/                       Sécurité
│   │   ├── data/                           Données
│   │   └── wizards/                        Wizards
│   ├── etat_civil_pos/                     Point de vente
│   │   ├── __manifest__.py                 v17.0.1.0.9
│   │   ├── models/                         6 fichiers (819 lignes)
│   │   │   ├── guichet_ticket.py           Ticket guichet POS (226 lignes)
│   │   │   ├── pos_order.py               Commande POS (261 lignes)
│   │   │   ├── pos_config.py              Config POS (113 lignes)
│   │   │   ├── copy_request.py             Extension demande (82 lignes)
│   │   │   └── copy_payment.py             Extension paiement (12 lignes)
│   │   ├── views/                          Vues
│   │   ├── report/                         1 rapport
│   │   ├── data/                           4 fichiers (produits, tarifs)
│   │   ├── security/                       2 fichiers + 1 CSV
│   │   └── static/                         Assets POS (JS/XML)
│   └── etat_civil_auth_email/              Authentification e-mail
│       ├── __manifest__.py                 v17.0.1.0.2
│       ├── models/                         2 fichiers (147 lignes)
│       │   └── res_users.py                Contrainte e-mail login
│       └── views/                          1 fichier (login_templates.xml)
├── odoo/                                   Odoo 17.0 (core)
├── config/                                 Configuration
│   ├── odoo17.conf                         Config principale
│   └── odoo17.conf.example                 Exemple
├── data/                                   Données Odoo
├── logs/                                   Logs
├── scripts/                                Scripts utilitaires
├── documentation/                          Documentation existante
├── requirements/                           Dépendances
├── README.md                               Documentation principale
├── DEPLOIEMENT.md                          Guide déploiement
├── CHANGELOG.md                            Historique des versions
└── documentation_2tup/                     ← Ce dossier (audit)
```

## Rôle de chaque dossier principal

| Dossier | Rôle |
|--------|------|
| custom_addons/ | Modules Odoo custom du projet |
| odoo/ | Core Odoo 17.0 (serveur + modules standard) |
| config/ | Fichiers de configuration Odoo |
| data/ | Répertoire de données Odoo (fichiers joints, sessions) |
| logs/ | Fichiers de log Odoo |
| scripts/ | Scripts utilitaires (génération données, etc.) |
| documentation/ | Documentation existante du projet |
| requirements/ | Fichiers de dépendances Python |
| backups/ | Sauvegardes de base de données |
| tmp_odoo_update.log | Log de mise à jour Odoo |

# Exigences techniques et Décisions d'Architecture (ADR)

Document récapitulatif des exigences techniques et des décisions d'architecture retrouvées dans le projet État Civil.

---

## Exigences techniques

### Sécurité

| ID | Exigence | Statut | Preuve |
|----|----------|--------|--------|
| SEC-01 | Authentification par e-mail obligatoire | Implémenté | `etat_civil_auth_email/models/res_users.py` — contrainte SQL sur e-mail |
| SEC-02 | Contrôle d'accès par groupes (Agent, Officier, Admin) | Implémenté | `security/security.xml` — 4 groupes définis |
| SEC-03 | ACL par modèle (82 règles CRUD) | Implémenté | `security/ir.model.access.csv` |
| SEC-04 | Règles d'accès par centre (isolation territoriale) | Implémenté | `security/security.xml` — `ir.rule` avec domaine sur `registre_id.centre_id` |
| SEC-05 | Vérification serveur des rôles (`_ensure_*`) | Implémenté | `acte_officiel.py` — méthodes `_ensure_agent()`, `_ensure_officier()`, `_ensure_admin()` |
| SEC-06 | Journal d'audit immuable | Implémenté | `audit_log.py` — `write()` et `unlink()` lèvent `AccessError` |
| SEC-07 | Chiffrement des données personnelles | **Non implémenté** | P0 — rapport qualité |
| SEC-08 | Secrets de configuration chiffrés | **Non implémenté** | P0 — `config/odoo17.conf` contient mots de passe en clair |
| SEC-09 | Protection contre injection SQL | Partiellement | Odoo ORM protège nativement, mais vérification manuelle requise pour les requêtes raw |
| SEC-10 | Protection contre XSS | Partiellement | `markupsafe` utilisé dans `piece_justificative.py`, mais pas systématique |

### Performance

| ID | Exigence | Statut | Preuve |
|----|----------|--------|--------|
| PERF-01 | Index sur les champs de recherche fréquents | Partiellement | Index sur `cin` (Individu), `numero_acte` (Acte), `ticket_numero` (Demande) |
| PERF-02 | Limitation des requêtes N+1 | **Non vérifié** | À analyser dans les méthodes `read_group` et vues |
| PERF-03 | Champs calculés avec `depends` correct | Implémenté | Champs calculés dans `acte_officiel.py` avec `@api.depends` |
| PERF-04 | Pagination des listes | Implémenté | Vues list Odoo avec pagination native |

### Déploiement

| ID | Exigence | Statut | Preuve |
|----|----------|--------|--------|
| DEP-01 | Installation reproductible | Partiellement | `requirements.txt` présent, mais procédure manuelle dans `DEPLOIEMENT.md` |
| DEP-02 | Configuration externalisée | Implémenté | `config/odoo17.conf` séparé du code |
| DEP-03 | Sauvegarde automatique | **Non implémenté** | P1 — rapport qualité |
| DEP-04 | Logs structurés | Implémenté | `logs/odoo17.log`, niveau `info` |
| DEP-05 | CI/CD automatisé | Partiellement | GitHub Actions workflows présents mais limités |

### Intégration

| ID | Exigence | Statut | Preuve |
|----|----------|--------|--------|
| INT-01 | Intégration module Comptabilité Odoo | Implémenté | `etat_civil_account` — extension `account.move` |
| INT-02 | Intégration Point de Vente Odoo | Implémenté | `etat_civil_pos` — extension `pos.order` |
| INT-03 | Export ODF | Implémenté | `odfpy` dans requirements |
| INT-04 | Export Excel | Implémenté | `openpyxl` dans requirements |
| INT-05 | QR Code sur les actes | Implémenté | `qrcode` dans requirements, `qr_code_image` dans actes |

---

## Décisions d'Architecture (ADR)

### ADR-01 : Héritage simple pour les types d'actes

**Contexte** : Trois types d'actes (naissance, mariage, décès) partagent un workflow commun (brouillon → transmis → validé/refusé).

**Décision** : Utiliser l'héritage simple Odoo (`_inherit = 'etat.civil.acte.officiel'`) plutôt que `_inherits` (délégation) ou un modèle unique avec champ de type.

**Conséquences** :
- ✅ Code partagé dans `acte_officiel.py` (1410 lignes de logique commune).
- ✅ Chaque type d'acte a sa propre table PostgreSQL.
- ✅ Vues et menus séparés par type.
- ⚠️ Duplication potentielle si les workflows divergent.

**Preuve** : `acte_naissance.py`, `acte_mariage.py`, `acte_deces.py` — tous héritent de `etat.civil.acte.officiel`.

---

### ADR-02 : Mixin abstrait pour l'audit

**Contexte** : Tous les modèles sensibles doivent être tracés (création, modification, suppression).

**Décision** : Créer un mixin abstrait `etat.civil.audit.mixin` qui surcharge `create()`, `write()`, `unlink()` et appelle `_log_event()` sur `etat.civil.audit.log`.

**Conséquences** :
- ✅ Traçabilité automatique sur tous les modèles qui héritent du mixin.
- ✅ Journal immuable (write/unlink bloqués sur `audit.log`).
- ⚠️ Surcharge de chaque opération ORM — impact performance potentiel.

**Preuve** : `audit_log.py` — mixin avec surcharge des méthodes ORM.

---

### ADR-03 : Modules séparés pour la comptabilité et le POS

**Contexte** : Les fonctionnalités de paiement et de point de vente sont optionnelles et dépendent de modules Odoo standard (`account`, `point_of_sale`).

**Décision** : Créer deux modules distincts (`etat_civil_account` et `etat_civil_pos`) avec dépendances chaînées.

**Conséquences** :
- ✅ Installation optionnelle — le module de base fonctionne sans comptabilité.
- ✅ Isolation des dépendances — `account` et `pos` ne sont pas requis par le cœur.
- ⚠️ Complexité de déploiement — 3 modules à installer dans l'ordre.

**Preuve** : Chaîne de dépendances : `etat_civil` → `etat_civil_account` → `etat_civil_pos`.

---

### ADR-04 : Token interne pour les transitions de statut

**Contexte** : Le statut des actes doit changer uniquement via les méthodes action dédiées, pas par `write()` direct.

**Décision** : Utiliser un token interne `_INTERNAL_TRANSITION_TOKEN` passé en paramètre lors des transitions légitimes, vérifié dans `write()`.

**Conséquences** :
- ✅ Protection contre les modifications de statut hors workflow.
- ✅ Traçabilité garantie des transitions.

**Preuve** : `acte_officiel.py` — `_INTERNAL_TRANSITION_TOKEN` utilisé dans `action_transmit()`, `action_validate()`, etc.

---

### ADR-05 : Authentification e-mail via module séparé

**Contexte** : L'authentification par e-mail est une exigence spécifique qui ne doit pas affecter le module principal.

**Décision** : Module `etat_civil_auth_email` avec hooks `pre_init_hook` et `post_init_hook` pour ajouter une contrainte SQL sur la colonne e-mail.

**Conséquences** :
- ✅ Modification minimale du modèle `res.users`.
- ✅ Contrainte au niveau de la base de données (plus fiable que validation Python seule).
- ⚠️ Hooks d'initialisation — risque si le module est installé sur une base existante avec des utilisateurs sans e-mail.

**Preuve** : `etat_civil_auth_email/__manifest__.py` — hooks définis, `models/res_users.py` — contrainte.

---

### ADR-06 : Rapports QWeb pour l'impression

**Contexte** : Les actes, quittances, et copies doivent être imprimés avec un format officiel.

**Décision** : Utiliser les rapports QWeb d'Odoo (XML → HTML → PDF via `wkhtmltopdf`).

**Conséquences** :
- ✅ Intégration native avec Odoo.
- ✅ Personnalisation via templates XML.
- ⚠️ Dépendance externe `wkhtmltopdf` — version à gérer.

**Preuve** : 12 fichiers de rapports QWeb dans `etat_civil/reports/`.

---

### ADR-07 : Composants OWL pour l'interface front-end

**Contexte** : Des fonctionnalités front-end personnalisées sont nécessaires (composants d'audit, widgets).

**Décision** : Utiliser le framework OWL (Odoo Web Library) pour les composants JavaScript.

**Conséquences** :
- ✅ Intégration avec le framework Odoo 17.
- ✅ Composants réutilisables.
- ⚠️ 3 fichiers JS — couverture limitée.

**Preuve** : `static/src/js/` — 3 fichiers JS + 2 fichiers XML templates.

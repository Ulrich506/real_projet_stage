# Rapport Qualité — Audit Statique du Projet État Civil

> **Avertissement** : Ce rapport est une estimation issue d'une analyse statique du code source, sans exécution des tests ni vérification en base de données. Les notes sont attribuées de manière stricte et factuelle ; ce qui ne peut être vérifié est marqué « non vérifié » et ne reçoit pas de points.

## Grille d'évaluation

### 1. Complétude fonctionnelle (poids 15)

| Sous-critère | Statut | Preuves |
|--------------|--------|---------|
| Naissance | ✓ Complet | acte_naissance.py:4-225, contraintes sexe parent/enfant, filiation, lieu accouchement |
| Mariage | ✓ Complet | acte_mariage.py:4-327, conjoints, témoins, régime matrimonial, mentions marginales auto |
| Décès | ✓ Complet | acte_deces.py:4-123, défunt, déclarant, mise à jour statut vital |
| Demandes de copies guichet | ✓ Complet | demande_guichet.py:7-517, workflow ticket, impression actes |
| Point de vente (POS) | ✓ Partiel | etat_civil_pos/ modèles POS, produits, tarifs |
| Quittances / facturation | ✓ Partiel | etat_civil_account/ copy_request.py (836 lignes), copy_payment.py |
| Rôles agent/officier/admin | ✓ Complet | security.xml:13-40, 4 groupes + régisseur |
| Mentions marginales | ✓ Complet | mention_marginale.py:10-374, 9 types de mentions |
| Pièces justificatives | ✓ Complet | piece_justificative.py:44-545, 40 types, workflow a_fournir→recu→verifie |
| Export | ✓ Partiel | import_export_log.py (35 lignes), wizards export |
| Citoyen/Individu | ✓ Complet | individu.py:11-494, CIN, âge, statut vital, matrimonial |

**Note : 85/100** — Fonctionnalités principales couvertes. L'export et le POS sont partiels.

### 2. Sécurité et contrôle d'accès (poids 15)

| Sous-critère | Statut | Preuves |
|--------------|--------|---------|
| Groupes de sécurité | ✓ | 4 groupes métier + régisseur (security.xml) |
| ACL par modèle | ✓ | 82 lignes CSV, granularité agent/officier/admin |
| Règles ir.rule | ✓ | Isolation par centre pour agents, assignation pour officiers |
| Vérification territoriale serveur | ✓ | _ensure_competence_territoriale() acte_officiel.py:224 |
| Protection workflow (token) | ✓ | _INTERNAL_TRANSITION_TOKEN acte_officiel.py:11 |
| Secrets en clair | ✗ **P0** | config/odoo17.conf:4,10 — admin_passwd et db_password visibles |
| sudo() | ⚠ Partiel | demande_guichet.py:253,273,294 — sudo() pour écrire le statut |
| Injection SQL | ✓ | Pas de SQL brut détecté sauf FOR UPDATE légitime (acte_mariage.py:274) |
| XSS | ⚠ | markupsafe importé (piece_justificative.py:1) mais usage à vérifier |
| Routes publiques | ⚠ | Contrôleurs non audités en détail |

**Note : 60/100** — Architecture sécurité solide, mais secrets en clair (P0) et sudo() partiel.

### 3. Données personnelles et audit (poids 10)

| Sous-critère | Statut | Preuves |
|--------------|--------|---------|
| Journal d'audit | ✓ Complet | audit_log.py:34-367, 27 types d'action, immuable |
| Traçabilité automatique | ✓ | etat.civil.audit.mixin trace create/write/unlink |
| IP + session hash | ✓ | audit_log.py:248-271 |
| Fuseau horaire | ✓ | UTC + local avec pytz |
| Export contrôlé | ⚠ Partiel | Wizards export existent mais non audités en détail |
| Confidentialité | ⚠ | Pas de chiffrement des données sensibles détecté |

**Note : 75/100** — Audit excellent, mais pas de chiffrement des données sensibles.

### 4. Intégrité et fiabilité (poids 12)

| Sous-critère | Statut | Preuves |
|--------------|--------|---------|
| Contraintes SQL | ✓ | unique(enfant_id), unique(defunt_id), unique(ticket_numero), etc. |
| Contraintes Python | ✓ | @api.constrains sur tous les actes |
| Séquences | ✓ | ir.sequence avec no_gap pour numéros d'acte |
| Transactions | ✓ | savepoint() utilisé (acte_officiel.py:581) |
| Verrouillage concurrent | ✓ | FOR UPDATE sur individu lors validation mariage (acte_mariage.py:274) |
| Migrations | ⚠ | migrations/2.1.30/post-migrate.py présent mais non examiné en détail |
| Gestion erreurs | ✓ | ValidationError, AccessError, UserError utilisés |

**Note : 80/100** — Bonne intégrité, migrations partielles.

### 5. Qualité du code et maintenabilité (poids 10)

| Sous-critère | Statut | Preuves |
|--------------|--------|---------|
| Conventions Odoo | ✓ | _name, _description, _rec_name, api.depends |
| Héritage propre | ✓ | Modèle abstrait acte_officiel, mixin audit |
| Nommage | ✓ | Nommage cohérent en français |
| Commentaires | ⚠ Partiel | Certains fichiers bien commentés, d'autres moins |
| Duplication | ⚠ | _check_and_lock_identity() dupliqué dans 3 fichiers actes |
| Taille fichiers | ⚠ | acte_officiel.py: 1410 lignes (trop long) |

**Note : 70/100** — Bonne structure, mais duplication et fichiers trop longs.

### 6. Tests automatisés (poids 10)

| Sous-critère | Statut | Preuves |
|--------------|--------|---------|
| Fichiers de tests | ✓ | 22 fichiers dans tests/ |
| Couverture | ⚠ Non vérifiée | Tests présents mais couverture non mesurée |
| CI | ✗ | Aucun workflow GitHub Actions détecté |
| Tests exécutés | ⚠ Non vérifié | Non exécutés pendant l'audit |

**Note : 35/100** — Tests présents mais pas de CI, couverture inconnue.

### 7. Ergonomie et UX (poids 8)

| Sous-critère | Statut | Preuves |
|--------------|--------|---------|
| Vues form/list/search | ✓ | 27 fichiers de vues |
| Workflow guichet | ✓ | Tickets, priorités, statuts |
| Messages d'erreur | ✓ | Messages détaillés en français |
| Bilinguisme fr/mg | ⚠ Partiel | Traductions non vérifiées |
| JavaScript OWL | ✓ | 3 composants JS |
| SCSS | ✓ | 1 fichier |

**Note : 65/100** — Vues complètes, bilinguisme à vérifier.

### 8. Performance et volume (poids 5)

| Sous-critère | Statut | Preuves |
|--------------|--------|---------|
| Index | ✓ | cin indexé, event_uuid indexé, action_type indexé |
| Champs calculés stockés | ✓ | nom_complet store=True, categorie_age store=True |
| Recherches sans limite | ⚠ | À vérifier dans le code |
| N+1 | ⚠ Non vérifié | Non testé |

**Note : 60/100** — Index présents, performance non testée.

### 9. Déploiement et exploitation (poids 8)

| Sous-critère | Statut | Preuves |
|--------------|--------|---------|
| Installation reproductible | ⚠ Partiel | DEPLOIEMENT.md existe mais incomplet |
| Docker | ✗ | Aucun Dockerfile/docker-compose |
| Sauvegardes | ⚠ | backups/ présent mais procédure non documentée |
| Logs | ✓ | logfile configuré, log_level info |
| Mise à jour | ⚠ | Migrations partielles |

**Note : 35/100** — Déploiement manuel, pas de Docker.

### 10. Documentation (poids 4)

| Sous-critère | Statut | Preuves |
|--------------|--------|---------|
| README | ✓ | README.md, README_GITHUB.md |
| CHANGELOG | ✓ | CHANGELOG.md |
| DEPLOIEMENT | ⚠ | DEPLOIEMENT.md partiel |
| Documentation code | ⚠ Partiel | Commentaires inégaux |
| Documentation utilisateur | ✗ | Non détectée |

**Note : 45/100** — Documentation de base présente, insuffisante pour production.

### 11. Contexte réel (poids 3)

| Sous-critère | Statut | Preuves |
|--------------|--------|---------|
| Valeur légale des actes | ⚠ | QR code + hash SHA-256, mais pas de signature électronique qualifiée |
| Signature | ⚠ | Hash SHA-256 (acte_officiel.py:272), pas de signature numérique |
| Impression officielle | ✓ | Rapports QWeb, wkhtmltopdf |
| Protection des données | ⚠ | Pas de chiffrement, pas de politique de rétention |

**Note : 40/100** — Empreinte SHA-256 présente mais insuffisante pour valeur légale.

## Tableau récapitulatif

| # | Critère | Note /100 | Poids | Points |
|---|---------|-----------|-------|--------|
| 1 | Complétude fonctionnelle | 85 | 15 | 12,75 |
| 2 | Sécurité et contrôle d'accès | 60 | 15 | 9,00 |
| 3 | Données personnelles et audit | 75 | 10 | 7,50 |
| 4 | Intégrité et fiabilité | 80 | 12 | 9,60 |
| 5 | Qualité du code | 70 | 10 | 7,00 |
| 6 | Tests automatisés | 35 | 10 | 3,50 |
| 7 | Ergonomie et UX | 65 | 8 | 5,20 |
| 8 | Performance | 60 | 5 | 3,00 |
| 9 | Déploiement | 35 | 8 | 2,80 |
| 10 | Documentation | 45 | 4 | 1,80 |
| 11 | Contexte réel | 40 | 3 | 1,20 |
| | **TOTAL** | | **100** | **63,35** |

## Pourcentage global : **63 %**

### Niveaux de préparation

| Niveau | Seuil | Statut |
|--------|-------|--------|
| Démo / soutenance | 50 % | ✅ **Atteint (63 %)** |
| Pilote réel dans une seule mairie | 75 % | ❌ Non atteint |
| Production multi-villes | 90 % | ❌ Non atteint |

## Points forts

1. **Workflow métier complet** : brouillon → transmission → validation/refus/correction avec contrôle de rôle
2. **Sécurité par couches** : ACL + ir.rule + vérifications Python + token interne
3. **Audit exhaustif** : journal immuable avec IP, session, fuseau horaire, 27 types d'action
4. **Intégrité des données** : contraintes SQL, verrouillage concurrent, séquences no_gap
5. **Empreinte cryptographique** : SHA-256 + QR code sur les actes validés
6. **Isolation territoriale** : agents et officiers limités à leurs centres

## Problèmes classés par priorité

### P0 — Bloquants pour un usage réel

| # | Problème | Fichier:Ligne | Impact |
|---|----------|---------------|--------|
| P0-1 | Mots de passe en clair dans config/odoo17.conf | config/odoo17.conf:4,10 | Accès non autorisé à la base et au serveur |
| P0-2 | Pas de chiffrement des données personnelles (CIN, noms) | Tous les modèles | Violation RGPD/locale si fuite |
| P0-3 | max_cron_threads = 0 désactive les tâches planifiées | config/odoo17.conf:32 | La cron de mise à jour des catégories d'âge ne s'exécute pas |
| P0-4 | Pas de signature électronique qualifiée | acte_officiel.py:272 | Les actes n'ont pas de valeur légale numérique |

### P1 — Importants

| # | Problème | Fichier:Ligne | Impact |
|---|----------|---------------|--------|
| P1-1 | sudo() utilisé dans demande_guichet.py pour écrire le statut | demande_guichet.py:253,273,294 | Contourne les ACL, risque d'écriture non autorisée |
| P1-2 | _check_and_lock_identity() dupliqué dans 3 fichiers | acte_naissance.py:194, acte_mariage.py:191, acte_deces.py:93 | Dette technique, risque d'incohérence |
| P1-3 | acte_officiel.py trop long (1410 lignes) | acte_officiel.py | Difficile à maintenir |
| P1-4 | Pas de CI/CD | — | Les régressions ne sont pas détectées automatiquement |
| P1-5 | Dépendance qrcode non listée dans external_dependencies | etat_civil/__manifest__.py | Installation peut échouer |
| P1-6 | Bilinguisme fr/mg non vérifié | — | Utilisateurs malgaches peuvent être exclus |

### P2 — Mineurs

| # | Problème | Fichier:Ligne | Impact |
|---|----------|---------------|--------|
| P2-1 | Commentaires inégaux entre fichiers | Divers | Maintenabilité |
| P2-2 | Fichier migration non commité | migrations/2.1.30/post-migrate.py | Risque de perte |
| P2-3 | Pas de Dockerfile | — | Déploiement manuel |
| P2-4 | Tags Git absents | — | Difficile de repérer les versions |
| P2-5 | Documentation utilisateur absente | — | Formation difficile |

## Recommandations priorisées

| Priorité | Recommandation | Effort estimé |
|----------|---------------|---------------|
| P0 | Utiliser des variables d'environnement pour les secrets | 0,5 jour |
| P0 | Implémenter le chiffrement des champs sensibles (CIN) | 2 jours |
| P0 | Corriger max_cron_threads dans la config de production | 0,1 jour |
| P0 | Évaluer une solution de signature électronique qualifiée | 5 jours |
| P1 | Remplacer sudo() par des ACL ciblées | 1 jour |
| P1 | Factoriser _check_and_lock_identity() dans un mixin | 0,5 jour |
| P1 | Découper acte_officiel.py en modules plus petits | 2 jours |
| P1 | Configurer GitHub Actions pour les tests | 1 jour |
| P1 | Ajouter qrcode à external_dependencies | 0,1 jour |
| P1 | Vérifier et compléter les traductions fr/mg | 2 jours |
| P2 | Créer un Dockerfile et docker-compose.yml | 1 jour |
| P2 | Ajouter des tags Git pour les versions | 0,1 jour |
| P2 | Rédiger une documentation utilisateur | 3 jours |
| P2 | Uniformiser les commentaires dans le code | 1 jour |

**Effort total estimé : ~20 jours**

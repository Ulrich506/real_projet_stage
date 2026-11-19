# Inventaire — Matrice de Sécurité

## Groupes de sécurité

| Groupe | XML ID | Description | Implique |
|--------|--------|-------------|----------|
| Agent d'état civil | etat_civil.group_etat_civil_agent | Prépare et transmet les actes | base.group_user |
| Officier d'état civil | etat_civil.group_etat_civil_officier | Valide/refuse les actes | base.group_user |
| Administrateur d'état civil | etat_civil.group_etat_civil_admin | Droits complets métier | agent + officier |
| Administrateur technique | etat_civil.group_etat_civil_tech_admin | Installation, config, sauvegarde | base.group_user |
| Régisseur | etat_civil_account.group_etat_civil_regisseur | Encaissement POS, quittances | (module account) |

## Matrice ACL — Modèles principaux

### etat.civil.individu

| Groupe | Read | Write | Create | Unlink |
|--------|------|-------|--------|--------|
| Agent | ✓ | ✓ | ✓ | ✗ |
| Officier | ✓ | ✗ | ✗ | ✗ |
| Admin | ✓ | ✓ | ✓ | ✓ |

### etat.civil.acte.naissance (idem mariage, décès)

| Groupe | Read | Write | Create | Unlink |
|--------|------|-------|--------|--------|
| Agent | ✓ | ✓ | ✓ | ✗ |
| Officier | ✓ | ✓ | ✗ | ✗ |
| Admin | ✓ | ✓ | ✓ | ✓ |

### etat.civil.mention.marginale

| Groupe | Read | Write | Create | Unlink |
|--------|------|-------|--------|--------|
| Agent | ✓ | ✗ | ✗ | ✗ |
| Officier | ✓ | ✗ | ✗ | ✗ |
| Admin | ✓ | ✓ | ✓ | ✓ |

### etat.civil.piece.justificative

| Groupe | Read | Write | Create | Unlink |
|--------|------|-------|--------|--------|
| Agent | ✓ | ✓ | ✓ | ✗ |
| Officier | ✓ | ✓ | ✗ | ✗ |
| Admin | ✓ | ✓ | ✓ | ✓ |

### etat.civil.demande.guichet

| Groupe | Read | Write | Create | Unlink |
|--------|------|-------|--------|--------|
| Agent | ✓ | ✓ | ✓ | ✗ |
| Officier | ✓ | ✓ | ✓ | ✗ |
| Admin | ✓ | ✓ | ✓ | ✓ |

### etat.civil.audit.log

| Groupe | Read | Write | Create | Unlink |
|--------|------|-------|--------|--------|
| Admin | ✓ | ✗ | ✗ | ✗ |
| (Immuable — seul le système peut créer) |

## Règles d'accès (ir.rule)

| Règle | Modèle | Groupe | Domaine | Effet |
|-------|--------|--------|---------|-------|
| rule_acte_naissance_centre | acte.naissance | Agent | registre_id.centre_id IN user.centres | Isolation par centre |
| rule_acte_mariage_centre | acte.mariage | Agent | registre_id.centre_id IN user.centres | Isolation par centre |
| rule_acte_deces_centre | acte.deces | Agent | registre_id.centre_id IN user.centres | Isolation par centre |
| rule_acte_naissance_officier_centre | acte.naissance | Officier | officier_validateur_id = user.id | Lecture seule des dossiers assignés |
| rule_acte_mariage_officier_centre | acte.mariage | Officier | officier_validateur_id = user.id | Lecture seule des dossiers assignés |
| rule_acte_deces_officier_centre | acte.deces | Officier | officier_validateur_id = user.id | Lecture seule des dossiers assignés |
| rule_centre_officier | centre | Officier | id IN user.centres | Lecture seule centres affectés |
| rule_registre_officier_centre | registre | Officier | centre_id IN user.centres | Lecture seule registres affectés |

## Protection supplémentaire (code Python)

- `_ensure_competence_territoriale()` : vérification serveur de l'appartenance au centre (acte_officiel.py:224)
- `_ensure_agent()`, `_ensure_officier()`, `_ensure_admin()` : contrôle des rôles avant chaque action
- `_ensure_officier_responsable()` : seul l'officier désigné peut traiter le dossier
- Token interne `_INTERNAL_TRANSITION_TOKEN` : empêche la modification directe du statut
- Audit log immuable : write() et unlink() lèvent AccessError

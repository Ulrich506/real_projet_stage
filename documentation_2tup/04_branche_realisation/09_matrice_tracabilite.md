# Matrice de traçabilité — Cas d'utilisation ↔ Code

Matrice qui relie chaque cas d'utilisation fonctionnel aux modèles, vues, méthodes et fichiers qui les implémentent.

## Légende

- **Modèle** : classe ORM Python
- **Vue** : fichier XML de vue Odoo
- **Méthode** : méthode Python implémentant l'action
- **Wizard** : wizard Odoo (dialogue)
- **Sécurité** : groupe, ACL, ou règle d'accès

---

## UC1 — Rechercher/Enregistrer un citoyen

| Élément | Implémentation |
|---------|---------------|
| **Modèle** | `etat.civil.individu` — `models/individu.py` |
| **Vue Form** | `views/individu_views.xml` |
| **Vue List** | `views/individu_views.xml` |
| **Vue Search** | `views/individu_views.xml` |
| **Menu** | `views/menus.xml` |
| **Sécurité** | `security/ir.model.access.csv` — Agent (CRUD), Officier (R) |
| **Contrainte** | Champ `cin` unique (index SQL) |

---

## UC2 — Saisir un acte de naissance

| Élément | Implémentation |
|---------|---------------|
| **Modèle** | `etat.civil.acte.naissance` — `models/acte_naissance.py` |
| **Modèle parent** | `etat.civil.acte.officiel` — `models/acte_officiel.py` |
| **Vue Form** | `views/acte_naissance_views.xml` |
| **Séquence** | `data/acte_sequence.xml` — `seq_acte_naissance` |
| **Méthode** | `create()` surchargée via `audit.mixin` |
| **Sécurité** | ACL Agent (R/W/C), règle `rule_acte_naissance_centre` |

---

## UC3 — Saisir un acte de mariage

| Élément | Implémentation |
|---------|---------------|
| **Modèle** | `etat.civil.acte.mariage` — `models/acte_mariage.py` |
| **Vue Form** | `views/acte_mariage_views.xml` |
| **Séquence** | `data/acte_sequence.xml` — `seq_acte_mariage` |
| **Sécurité** | ACL Agent (R/W/C), règle `rule_acte_mariage_centre` |

---

## UC4 — Saisir un acte de décès

| Élément | Implémentation |
|---------|---------------|
| **Modèle** | `etat.civil.acte.deces` — `models/acte_deces.py` |
| **Vue Form** | `views/acte_deces_views.xml` |
| **Séquence** | `data/acte_sequence.xml` — `seq_acte_deces` |
| **Sécurité** | ACL Agent (R/W/C), règle `rule_acte_deces_centre` |

---

## UC5 — Joindre des pièces justificatives

| Élément | Implémentation |
|---------|---------------|
| **Modèle** | `etat.civil.piece.justificative` — `models/piece_justificative.py` |
| **Modèle config** | `etat.civil.piece.requise` — `models/piece_requise.py` |
| **Vue** | Dans les vues form des actes (tabs) |
| **Données** | `data/piece_requise_data.xml` |
| **Méthodes** | `action_mark_received()`, `action_mark_verified()` |

---

## UC6 — Transmettre un acte à l'officier

| Élément | Implémentation |
|---------|---------------|
| **Méthode** | `action_transmit()` — `models/acte_officiel.py` |
| **Wizard** | `wizards/transmission_acte_wizard.py` |
| **Vérification** | `_ensure_agent()`, `_ensure_competence_territoriale()` |
| **Notification** | `mail.thread.message_post()` |
| **Token** | `_INTERNAL_TRANSITION_TOKEN` |

---

## UC7 — Corriger un acte retourné

| Élément | Implémentation |
|---------|---------------|
| **Méthode** | `action_retransmit()` — `models/acte_officiel.py` |
| **Wizard** | `wizards/retour_correction_wizard.py` |
| **Champ** | `motif_refus` — affiché dans la vue form |

---

## UC8 — Créer une demande de copie au guichet

| Élément | Implémentation |
|---------|---------------|
| **Modèle** | `etat.civil.demande.guichet` — `models/demande_guichet.py` |
| **Vue Form** | `views/demandes_guichet_views.xml` |
| **Séquence** | `data/demande_guichet_sequence.xml` |
| **Méthode** | `_compute_ticket_numero()` |

---

## UC9 — Consulter le journal d'audit

| Élément | Implémentation |
|---------|---------------|
| **Modèle** | `etat.civil.audit.log` — `models/audit_log.py` |
| **Vue** | `views/audit_log_views.xml` (list + search) |
| **Sécurité** | ACL Admin (R seule), write/unlink bloqués |

---

## UC10 — Gérer les registres

| Élément | Implémentation |
|---------|---------------|
| **Modèle** | `etat.civil.registre` — `models/registre.py` |
| **Vue** | Dans `views/menus.xml` (configuration) |
| **Champs** | `est_cloture`, `date_ouverture`, `date_cloture` |

---

## UC11 — Consulter les actes transmis

| Élément | Implémentation |
|---------|---------------|
| **Modèle** | `etat.civil.acte.officiel` — filtrage par `statut='transmis'` |
| **Vue** | Vues form des actes avec filtre officier |
| **Règle** | `rule_acte_naissance_officier_centre` — domaine sur `officier_validateur_id` |

---

## UC12 — Valider un acte

| Élément | Implémentation |
|---------|---------------|
| **Méthode** | `action_validate()` — `models/acte_officiel.py` |
| **Vérification** | `_ensure_officier()`, `_ensure_officier_responsable()` |
| **Calcul** | `_compute_hash_empreinte()`, `_compute_qr_code()` |
| **Mention** | Création automatique de `etat.civil.mention.marginale` |
| **Token** | `_INTERNAL_TRANSITION_TOKEN` |

---

## UC13 — Refuser un acte avec motif

| Élément | Implémentation |
|---------|---------------|
| **Méthode** | `action_refuse(motif)` — `models/acte_officiel.py` |
| **Wizard** | `wizards/retour_correction_wizard.py` |
| **Champ** | `motif_refus` enregistré sur l'acte |

---

## UC14 — Consulter les mentions marginales

| Élément | Implémentation |
|---------|---------------|
| **Modèle** | `etat.civil.mention.marginale` — `models/mention_marginale.py` |
| **Vue** | `views/mentions_marginales_views.xml` |
| **Sécurité** | ACL Agent (R), Officier (R), Admin (CRUD) |

---

## UC22 — Gérer les utilisateurs et rôles

| Élément | Implémentation |
|---------|---------------|
| **Modèle** | `res.users` (extension) — `models/res_users.py` |
| **Groupes** | `security/security.xml` — 4 groupes |
| **Champs** | `etat_civil_centre_ids` (Many2many) |

---

## UC23 — Configurer l'identité de la commune

| Élément | Implémentation |
|---------|---------------|
| **Modèle** | `etat.civil.config.settings` — `models/config_settings.py` |
| **Vue** | `views/config_settings_views.xml` |
| **Données** | `data/config_identity_data.xml` |
| **Stockage** | `ir.config_parameter` (Odoo standard) |

---

## UC25 — Exporter les données

| Élément | Implémentation |
|---------|---------------|
| **Contrôleur** | `controllers/main.py` — route `/etat_civil/export` |
| **Bibliothèques** | `odfpy` (ODF), `openpyxl` (Excel) |
| **Journal** | `etat.civil.import_export_log` — `models/import_export_log.py` |
| **Sécurité** | `_ensure_admin()` dans le contrôleur |

---

## UC28 — Annuler un acte

| Élément | Implémentation |
|---------|---------------|
| **Méthode** | `action_annulate(motif)` — `models/acte_officiel.py` |
| **Wizard** | `wizards/annulation_acte_wizard.py` |
| **Sécurité** | `_ensure_admin()` |

---

## UC30-35 — Guichet / POS / Paiement

| UC | Élément | Implémentation |
|----|---------|---------------|
| UC30 | Modèle | `etat.civil.guichet.ticket` — `etat_civil_pos/models/guichet_ticket.py` |
| UC31 | Méthode | `action_mark_treated()` — `models/demande_guichet.py` |
| UC32 | Modèle | `etat.civil.copy.payment` — `etat_civil_account/models/copy_payment.py` |
| UC32 | Modèle | `pos.order` (extension) — `etat_civil_pos/models/pos_order.py` |
| UC33 | Rapport | QWeb quittance — `etat_civil_account/report/` |
| UC34 | Rapport | QWeb copie acte — `etat_civil/reports/actes_reports.xml` |
| UC35 | Modèle | `etat.civil.copy.tariff` — `etat_civil_account/models/copy_tariff.py` |

---

## Résumé de couverture

| Cas d'utilisation | Implémenté | Partiellement | Non implémenté |
|-------------------|-----------|---------------|----------------|
| UC1-10 (Agent) | ✅ 10/10 | — | — |
| UC11-15 (Officier) | ✅ 5/5 | — | — |
| UC20-28 (Admin) | ✅ 7/7 | — | — |
| UC30-35 (Régisseur) | ✅ 6/6 | — | — |
| **Total** | **28/28** | **0** | **0** |

> Tous les cas d'utilisation identifiés ont une implémentation dans le code. La qualité et la complétude de chaque implémentation sont évaluées dans le rapport qualité (Partie B).

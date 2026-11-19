# Inventaire — Catalogue des Modèles ORM

## Module etat_civil

| Modèle | Nom technique | Description | Héritage | Champs principaux |
|--------|---------------|-------------|----------|-------------------|
| Individu | etat.civil.individu | Citoyen / personne physique | etat.civil.audit.mixin | cin, nom, prenoms, sexe, date_naissance, statut_vital, situation_matrimoniale, lieu_naissance_commune, profession_actuelle, domicile_actuel, nationalite_actuelle |
| Centre | etat.civil.centre | Centre d'État Civil / Mairie | etat.civil.audit.mixin | code_centre, nom_centre, commune, district_province, pays, logo_commune, logo_region, reference_legale |
| Registre | etat.civil.registre | Registre annuel des actes | etat.civil.audit.mixin | annee, type_registre, numero_volume, centre_id, est_cloture, date_ouverture, date_cloture |
| Acte Officiel | etat.civil.acte.officiel | **Abstrait** — Base commune des actes | mail.thread, mail.activity.mixin, etat.civil.audit.mixin | numero_acte, feuillet_numero, registre_id, date_dressage, texte_integral_acte, statut, hash_empreinte_num, qr_code_image, agent_transmetteur_id, officier_validateur_id |
| Acte Naissance | etat.civil.acte.naissance | Acte de naissance | etat.civil.acte.officiel | enfant_id, pere_id, mere_id, declarant_id, heure_naissance, lieu_naissance, lieu_accouchement, filiation, est_jumeau, rang_naissance |
| Acte Mariage | etat.civil.acte.mariage | Acte de mariage | etat.civil.acte.officiel | conjoint_1_id, conjoint_2_id, temoin_1_id, temoin_2_id, date_mariage, lieu_mariage, regime_matrimonial, conjoint_X_est_etranger |
| Acte Décès | etat.civil.acte.deces | Acte de décès | etat.civil.acte.officiel | defunt_id, declarant_id, date_deces, heure_deces, lieu_deces, cause_deces, certificat_medical_ref |
| Mention Marginale | etat.civil.mention.marginale | Mention sur acte (mariage, divorce, décès…) | etat.civil.audit.mixin | name, type_mention, date_mention, contenu, personne_concernee_id, acte_naissance_id, acte_mariage_id, acte_deces_id, statut |
| Pièce Justificative | etat.civil.piece.justificative | Document joint à un acte | mail.thread, etat.civil.audit.mixin | name (40 types), obligatoire, etat (a_fournir/recu/verifie), attachment_ids, acte_X_id |
| Pièce Requise | etat.civil.piece.requise | Configuration des pièces requises par type d'acte | — | code_piece, type_acte, condition, obligatoire, sequence |
| Demande Guichet | etat.civil.demande.guichet | Ticket de demande au guichet | etat.civil.audit.mixin | ticket_numero, citoyen_nom, citoyen_cin, citoyen_id, type_acte, type_demande, statut, priorite |
| Audit Log | etat.civil.audit.log | Journal d'audit immuable | — | event_uuid, event_datetime_utc, user_id, action_type, record_model, record_id, ip_address, session_hash |
| Audit Mixin | etat.civil.audit.mixin | **Abstrait** — Traçabilité automatique | — | (surcharge create/write/unlink) |
| Config Settings | etat.civil.config.settings | Configuration de l'identité de la commune | — | identity_locked, commune_code, etc. |
| Import/Export Log | etat.civil.import_export_log | Journal d'import/export | — | détails des opérations d'échange |
| res.users (extension) | res.users | Extension utilisateur | — | etat_civil_centre_ids, _is_etat_civil_admin() |
| malagasy_date_utils | — | Utilitaires de calcul de date malgache | — | Fonctions utilitaires (pas un modèle) |

## Module etat_civil_account

| Modèle | Nom technique | Description | Héritage |
|--------|---------------|-------------|----------|
| Demande de copie | etat.civil.copy.request | Demande de copie avec facturation | etat.civil.demande.guichet (extends) |
| Paiement copie | etat.civil.copy.payment | Paiement lié à une copie | — |
| Tarif copie | etat.civil.copy.tariff | Tarifs par type de copie | — |
| Lien acte-copie | etat.civil.acte.copy.link | Lien entre acte et copie | — |
| Événement opération | etat.civil.operation.event | Traçabilité financière | — |
| Guichet (account) | etat.civil.guichet | Extension guichet comptable | — |
| account.move (extension) | account.move | Extension facture | — |

## Module etat_civil_pos

| Modèle | Nom technique | Description | Héritage |
|--------|---------------|-------------|----------|
| Ticket guichet (POS) | etat.civil.guichet.ticket | Extension ticket pour POS | — |
| Demande POS | pos.order | Extension commande POS | — |
| Config POS | pos.config | Extension configuration POS | — |
| Paiement copie (POS) | etat.civil.copy.payment | Extension paiement POS | — |
| Demande copie (POS) | etat.civil.copy.request | Extension demande copie POS | — |

## Module etat_civil_auth_email

| Modèle | Nom technique | Description | Héritage |
|--------|---------------|-------------|----------|
| res.users (extension) | res.users | Contrainte e-mail comme login | — |

## Relations entre modèles (résumé)

```
etat.civil.individu
  ├── 1←N etat.civil.acte.naissance (enfant_id, pere_id, mere_id, declarant_id)
  ├── 1←N etat.civil.acte.mariage (conjoint_1_id, conjoint_2_id, temoin_1_id, temoin_2_id)
  ├── 1←N etat.civil.acte.deces (defunt_id, declarant_id)
  └── 1←N etat.civil.mention.marginale (personne_concernee_id)

etat.civil.acte.officiel (abstrait)
  ├── etat.civil.acte.naissance
  ├── etat.civil.acte.mariage
  └── etat.civil.acte.deces
  └── N→1 etat.civil.registre
      └── N→1 etat.civil.centre

etat.civil.piece.justificative
  ├── N→1 etat.civil.acte.naissance
  ├── N→1 etat.civil.acte.mariage
  ├── N→1 etat.civil.acte.deces
  └── N→1 etat.civil.mention.marginale

etat.civil.demande.guichet
  └── N→1 etat.civil.individu (citoyen_id)
```

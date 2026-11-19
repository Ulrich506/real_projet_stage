# Fiches de cas d'utilisation

Fiches détaillées des cas d'utilisation principaux du système d'État Civil. Chaque fiche décrit l'acteur, les préconditions, le scénario nominal, et les alternatives.

---

## UC1 — Rechercher/Enregistrer un citoyen (Individu)

| Champ | Valeur |
|-------|--------|
| **Acteur** | Agent, Officier (lecture), Administrateur |
| **Description** | Rechercher un citoyen par CIN, nom, ou créer un nouveau citoyen |
| **Préconditions** | Utilisateur connecté, groupe Agent ou supérieur |
| **Postconditions** | Fiche citoyen affichée ou créée en base |

### Scénario nominal
1. L'agent accède au menu *État Civil → Citoyens*.
2. Il saisit le CIN ou le nom dans la barre de recherche.
3. Le système affiche la liste des résultats filtrée par centre.
4. L'agent clique sur un résultat pour voir la fiche complète.
5. *Ou* l'agent clique sur *Nouveau* et remplit les champs obligatoires (CIN, nom, prénoms, sexe, date de naissance).
6. Le système enregistre l'individu et affiche la fiche.

### Alternatives
- **A1** : CIN déjà existant → message d'erreur, l'agent doit vérifier les données.
- **A2** : Citoyen trouvé dans un autre centre → lecture seule si l'agent n'a pas le droit cross-centre.

### Modèles impliqués
`etat.civil.individu` — champs : `cin`, `nom`, `prenoms`, `sexe`, `date_naissance`, `statut_vital`, `situation_matrimoniale`, `lieu_naissance_commune`, `profession_actuelle`, `domicile_actuel`, `nationalite_actuelle`.

---

## UC2 — Saisir un acte de naissance

| Champ | Valeur |
|-------|--------|
| **Acteur** | Agent |
| **Description** | Enregistrer une nouvelle naissance dans le registre |
| **Préconditions** | Agent connecté, registre ouvert pour l'année en cours |
| **Postconditions** | Acte de naissance créé avec statut `brouillon`, numéro de séquence attribué |

### Scénario nominal
1. L'agent accède au menu *Actes → Naissances → Nouveau*.
2. Il sélectionne ou crée l'enfant (Individu).
3. Il remplit les champs : père, mère, déclarant, heure de naissance, lieu de naissance, lieu d'accouchement, filiation.
4. Il indique si l'enfant est jumeau et le rang de naissance.
5. Le système attribue un numéro d'acte via la séquence `seq_acte_naissance`.
6. L'acte est enregistré avec le statut `brouillon`.

### Alternatives
- **A1** : Registre non ouvert → erreur, l'agent doit contacter l'administrateur.
- **A2** : Parent non trouvé → l'agent crée d'abord l'individu parent.

### Modèles impliqués
`etat.civil.acte.naissance` hérite de `etat.civil.acte.officiel`. Champs : `enfant_id`, `pere_id`, `mere_id`, `declarant_id`, `heure_naissance`, `lieu_naissance`, `lieu_accouchement`, `filiation`, `est_jumeau`, `rang_naissance`.

---

## UC3 — Saisir un acte de mariage

| Champ | Valeur |
|-------|--------|
| **Acteur** | Agent |
| **Description** | Enregistrer un mariage dans le registre |
| **Préconditions** | Agent connecté, registre ouvert, 2 conjoints existants |
| **Postconditions** | Acte de mariage créé avec statut `brouillon` |

### Scénario nominal
1. L'agent accède au menu *Actes → Mariages → Nouveau*.
2. Il sélectionne les deux conjoints (Individu).
3. Il remplit : date de mariage, lieu, régime matrimonial, témoins (2).
4. Il indique si chaque conjoint est étranger.
5. Le système attribue un numéro via `seq_acte_mariage`.
6. L'acte est enregistré avec le statut `brouillon`.

### Alternatives
- **A1** : Conjoint déjà marié sans mention de divorce → avertissement.
- **A2** : Conjoint décédé → blocage, acte impossible.

### Modèles impliqués
`etat.civil.acte.mariage`. Champs : `conjoint_1_id`, `conjoint_2_id`, `temoin_1_id`, `temoin_2_id`, `date_mariage`, `lieu_mariage`, `regime_matrimonial`.

---

## UC4 — Saisir un acte de décès

| Champ | Valeur |
|-------|--------|
| **Acteur** | Agent |
| **Description** | Enregistrer un décès dans le registre |
| **Préconditions** | Agent connecté, registre ouvert, défunt existant |
| **Postconditions** | Acte de décès créé, statut vital du défunt mis à jour |

### Scénario nominal
1. L'agent accède au menu *Actes → Décès → Nouveau*.
2. Il sélectionne le défunt (Individu).
3. Il remplit : déclarant, date de décès, heure, lieu, cause, référence certificat médical.
4. Le système attribue un numéro via `seq_acte_deces`.
5. Le statut vital du défunt est mis à jour à `decede`.
6. L'acte est enregistré avec le statut `brouillon`.

### Alternatives
- **A1** : Défunt déjà marqué comme décédé → avertissement, double saisie possible.

### Modèles impliqués
`etat.civil.acte.deces`. Champs : `defunt_id`, `declarant_id`, `date_deces`, `heure_deces`, `lieu_deces`, `cause_deces`, `certificat_medical_ref`.

---

## UC5 — Joindre des pièces justificatives

| Champ | Valeur |
|-------|--------|
| **Acteur** | Agent |
| **Description** | Attacher des documents justificatifs à un acte |
| **Préconditions** | Acte existant en statut `brouillon` ou `transmis` |
| **Postconditions** | Pièces enregistrées avec état `a_fournir`, `recu`, ou `verifie` |

### Scénario nominal
1. Depuis la fiche de l'acte, l'agent clique sur *Pièces justificatives*.
2. Le système affiche la liste des pièces requises (configurée dans `etat.civil.piece.requise`).
3. L'agent télécharge les fichiers et marque l'état de chaque pièce.
4. Le système enregistre les pièces avec leur état.

### Modèles impliqués
`etat.civil.piece.justificative`, `etat.civil.piece.requise`.

---

## UC6 — Transmettre un acte à l'officier

| Champ | Valeur |
|-------|--------|
| **Acteur** | Agent |
| **Description** | Envoyer un acte complété pour validation par l'officier |
| **Préconditions** | Acte en statut `brouillon`, pièces justificatives complètes |
| **Postconditions** | Acte en statut `transmis`, notification envoyée à l'officier |

### Scénario nominal
1. L'agent vérifie que toutes les pièces sont jointes.
2. Il lance le wizard de transmission (`transmission_acte_wizard`).
3. Le système vérifie la compétence territoriale (`_ensure_competence_territoriale`).
4. Le statut passe à `transmis`.
5. Une notification mail est envoyée à l'officier désigné.

### Alternatives
- **A1** : Pièces manquantes → blocage, liste des pièces requises affichée.
- **A2** : Centre incompatible → erreur de compétence territoriale.

### Modèles impliqués
`etat.civil.acte.officiel` méthode `action_transmit`, wizard `transmission_acte_wizard`.

---

## UC7 — Corriger un acte retourné

| Champ | Valeur |
|-------|--------|
| **Acteur** | Agent |
| **Description** | Modifier un acte refusé par l'officier |
| **Préconditions** | Acte en statut `retourne_correction`, motif de refus connu |
| **Postconditions** | Acte corrigé, retransmis à l'officier |

### Scénario nominal
1. L'agent consulte l'acte retourné et lit le motif de refus.
2. Il corrige les champs concernés.
3. Il lance le wizard de retransmission.
4. Le statut repasse à `transmis`.

### Modèles impliqués
`etat.civil.acte.officiel` méthode `action_retransmit`, wizard `retour_correction_wizard`.

---

## UC8 — Créer une demande de copie au guichet

| Champ | Valeur |
|-------|--------|
| **Acteur** | Agent |
| **Description** | Enregistrer une demande de copie d'acte au guichet |
| **Préconditions** | Acte validé existant, citoyen identifié |
| **Postconditions** | Ticket guichet créé en statut `en_attente` |

### Scénario nominal
1. L'agent accède au menu *Guichet → Demandes → Nouveau*.
2. Il identifie le citoyen (CIN ou nom).
3. Il sélectionne le type d'acte et le type de demande (copie intégrale, extrait, etc.).
4. Il définit la priorité (normale, urgente).
5. Le système crée le ticket avec un numéro de séquence.

### Modèles impliqués
`etat.civil.demande.guichet`. Champs : `ticket_numero`, `citoyen_nom`, `citoyen_cin`, `citoyen_id`, `type_acte`, `type_demande`, `statut`, `priorite`.

---

## UC9 — Consulter le journal d'audit

| Champ | Valeur |
|-------|--------|
| **Acteur** | Agent (filtré), Administrateur (complet) |
| **Description** | Lire l'historique des actions effectuées sur le système |
| **Préconditions** | Utilisateur connecté |
| **Postconditions** | Aucune (lecture seule) |

### Scénario nominal
1. L'utilisateur accède au menu *Configuration → Journal d'audit*.
2. Il applique des filtres (date, utilisateur, type d'action, modèle).
3. Le système affiche les entrées du journal triées par date décroissante.

### Modèles impliqués
`etat.civil.audit.log`. Champs : `event_uuid`, `event_datetime_utc`, `user_id`, `action_type`, `record_model`, `record_id`, `ip_address`, `session_hash`.

---

## UC10 — Gérer les registres

| Champ | Valeur |
|-------|--------|
| **Acteur** | Agent, Administrateur |
| **Description** | Ouvrir, consulter, ou clôturer un registre annuel |
| **Préconditions** | Utilisateur avec droit sur le centre |
| **Postconditions** | Registre ouvert ou clôturé |

### Scénario nominal
1. L'utilisateur accède au menu *Configuration → Registres*.
2. Pour ouvrir un registre : il crée un enregistrement avec année, type, numéro de volume, centre.
3. Pour clôturer : il coche `est_cloture` et la date de clôture.

### Modèles impliqués
`etat.civil.registre`. Champs : `annee`, `type_registre`, `numero_volume`, `centre_id`, `est_cloture`, `date_ouverture`, `date_cloture`.

---

## UC11 — Consulter les actes transmis

| Champ | Valeur |
|-------|--------|
| **Acteur** | Officier |
| **Description** | Voir la liste des actes en attente de validation |
| **Préconditions** | Officier connecté |
| **Postconditions** | Aucune (lecture) |

### Scénario nominal
1. L'officier accède au menu *Actes → À valider*.
2. Le système affiche les actes avec statut `transmis`, filtrés par centre et officier responsable.
3. L'officier clique sur un acte pour le consulter en détail.

---

## UC12 — Valider un acte

| Champ | Valeur |
|-------|--------|
| **Acteur** | Officier |
| **Description** | Approuver et sceller un acte après vérification |
| **Préconditions** | Acte en statut `transmis`, officier désigné |
| **Postconditions** | Acte en statut `valide`, hash d'empreinte calculé, QR code généré |

### Scénario nominal
1. L'officier consulte l'acte et vérifie les données et pièces.
2. Il clique sur *Valider*.
3. Le système vérifie `_ensure_officier()` et `_ensure_officier_responsable()`.
4. Le statut passe à `valide`.
5. Le hash SHA-256 de l'empreinte numérique est calculé (`hash_empreinte_num`).
6. Un QR code est généré (`qr_code_image`).
7. Une mention marginale est créée automatiquement si applicable.

### Modèles impliqués
`etat.civil.acte.officiel` méthode `action_validate`.

---

## UC13 — Refuser un acte avec motif

| Champ | Valeur |
|-------|--------|
| **Acteur** | Officier |
| **Description** | Retourner un acte à l'agent avec un motif de correction |
| **Préconditions** | Acte en statut `transmis` |
| **Postconditions** | Acte en statut `retourne_correction`, motif enregistré |

### Scénario nominal
1. L'officier identifie les erreurs.
2. Il clique sur *Refuser* et saisit le motif dans le wizard.
3. Le statut passe à `retourne_correction`.
4. L'agent reçoit une notification.

### Modèles impliqués
`etat.civil.acte.officiel` méthode `action_refuse`, wizard `retour_correction_wizard`.

---

## UC14 — Consulter les mentions marginales

| Champ | Valeur |
|-------|--------|
| **Acteur** | Officier, Agent (lecture) |
| **Description** | Voir les mentions portées sur les actes |
| **Préconditions** | Utilisateur connecté |
| **Postconditions** | Aucune (lecture) |

### Modèles impliqués
`etat.civil.mention.marginale`. Champs : `name`, `type_mention`, `date_mention`, `contenu`, `personne_concernee_id`, `statut`.

---

## UC15 — Consulter les registres (Officier)

| Champ | Valeur |
|-------|--------|
| **Acteur** | Officier |
| **Description** | Voir les registres de son centre (lecture seule) |
| **Préconditions** | Officier connecté |
| **Postconditions** | Aucune |

---

## UC20-21 — Tous les droits Agent / Officier (Administrateur)

L'administrateur hérite de tous les cas d'utilisation de l'Agent et de l'Officier via l'implication de groupes dans `security.xml`.

---

## UC22 — Gérer les utilisateurs et rôles

| Champ | Valeur |
|-------|--------|
| **Acteur** | Administrateur |
| **Description** | Créer, modifier, supprimer des utilisateurs et assigner des rôles |
| **Préconditions** | Groupe `etat_civil_admin` |
| **Postconditions** | Utilisateur créé avec les droits appropriés |

### Scénario nominal
1. L'admin accède à *Configuration → Utilisateurs*.
2. Il crée un utilisateur, assigne un groupe (Agent, Officier).
3. Il affecte les centres d'état civil (`etat_civil_centre_ids`).

---

## UC23 — Configurer l'identité de la commune

| Champ | Valeur |
|-------|--------|
| **Acteur** | Administrateur |
| **Description** | Définir les informations d'identité affichées sur les actes |
| **Préconditions** | Groupe `etat_civil_admin` |
| **Postconditions** | Paramètres sauvegardés dans `ir.config_parameter` |

### Modèles impliqués
`etat.civil.config.settings`. Champs : `identity_locked`, `commune_code`, `logo_commune`, `logo_region`, `reference_legale`.

---

## UC24 — Gérer les centres d'état civil

| Champ | Valeur |
|-------|--------|
| **Acteur** | Administrateur |
| **Description** | Créer et configurer les centres (mairies) |
| **Préconditions** | Groupe `etat_civil_admin` |
| **Postconditions** | Centre créé avec code, nom, commune, district |

### Modèles impliqués
`etat.civil.centre`. Champs : `code_centre`, `nom_centre`, `commune`, `district_province`, `pays`, `logo_commune`, `logo_region`, `reference_legale`.

---

## UC25 — Exporter les données (ODF/Excel)

| Champ | Valeur |
|-------|--------|
| **Acteur** | Administrateur |
| **Description** | Exporter les données d'actes au format ODF ou Excel |
| **Préconditions** | Groupe `etat_civil_admin`, actes sélectionnés |
| **Postconditions** | Fichier téléchargé, entrée dans le journal d'import/export |

### Modèles impliqués
`etat.civil.import_export_log`, contrôleurs dans `controllers/main.py`.

---

## UC26 — Consulter le journal d'audit complet

| Champ | Valeur |
|-------|--------|
| **Acteur** | Administrateur |
| **Description** | Voir toutes les entrées du journal sans restriction de centre |
| **Différence avec UC9** | Pas de filtrage par centre, accès à tous les événements |

---

## UC27 — Gérer les séquences de numérotation

| Champ | Valeur |
|-------|--------|
| **Acteur** | Administrateur |
| **Description** | Configurer les préfixes, suffixes, et prochaines valeurs des séquences |
| **Préconditions** | Groupe `etat_civil_admin` |
| **Postconditions** | Séquences modifiées |

### Séquences existantes
- `seq_acte_naissance`
- `seq_acte_mariage`
- `seq_acte_deces`
- `seq_mention_marginale`
- `seq_demande_guichet`

---

## UC28 — Annuler un acte

| Champ | Valeur |
|-------|--------|
| **Acteur** | Administrateur |
| **Description** | Annuler un acte avec motif (wizard) |
| **Préconditions** | Acte existant, groupe admin |
| **Postconditions** | Acte en statut `annule`, motif enregistré |

### Modèles impliqués
Wizard `annulation_acte_wizard`.

---

## UC30 — Consulter la file d'attente du guichet

| Champ | Valeur |
|-------|--------|
| **Acteur** | Régisseur |
| **Description** | Voir les demandes en attente, triées par priorité et date |
| **Préconditions** | Groupe `regisseur` |
| **Postconditions** | Aucune (lecture) |

### Modèles impliqués
`etat.civil.guichet.ticket` (extension POS).

---

## UC31 — Marquer une demande comme traitée

| Champ | Valeur |
|-------|--------|
| **Acteur** | Régisseur |
| **Description** | Passer un ticket de `en_attente` à `traite` |
| **Préconditions** | Ticket en statut `en_attente` |
| **Postconditions** | Ticket en statut `traite`, date de traitement enregistrée |

### Modèles impliqués
`etat.civil.demande.guichet` méthode `action_mark_treated`.

---

## UC32 — Encaisser un paiement

| Champ | Valeur |
|-------|--------|
| **Acteur** | Régisseur |
| **Description** | Enregistrer le paiement d'une copie d'acte via le POS |
| **Préconditions** | Tarif configuré, demande de copie existante |
| **Postconditions** | Paiement enregistré, facture créée |

### Modèles impliqués
`etat.civil.copy.payment`, `pos.order` (extension POS), `etat.civil.copy.tariff`.

---

## UC33 — Émettre une quittance

| Champ | Valeur |
|-------|--------|
| **Acteur** | Régisseur |
| **Description** | Générer et imprimer une quittance de paiement |
| **Préconditions** | Paiement enregistré |
| **Postconditions** | Quittance imprimée, statut mis à jour |

### Modèles impliqués
Rapport QWeb quittance dans `etat_civil_account/report/`.

---

## UC34 — Imprimer une copie d'acte

| Champ | Valeur |
|-------|--------|
| **Acteur** | Régisseur |
| **Description** | Imprimer une copie certifiée d'un acte validé |
| **Préconditions** | Acte en statut `valide`, paiement effectué |
| **Postconditions** | Copie imprimée, lien acte-copie enregistré |

### Modèles impliqués
`etat.civil.acte.copy.link`, rapports QWeb dans `etat_civil/reports/`.

---

## UC35 — Consulter les tarifs en vigueur

| Champ | Valeur |
|-------|--------|
| **Acteur** | Régisseur |
| **Description** | Voir les tarifs par type de copie |
| **Préconditions** | Groupe `regisseur` |
| **Postconditions** | Aucune (lecture) |

### Modèles impliqués
`etat.civil.copy.tariff`.

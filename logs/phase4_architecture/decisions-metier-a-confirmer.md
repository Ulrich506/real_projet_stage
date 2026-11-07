# Décisions métier et comptables à confirmer

Les propositions ci-dessous ne valent pas approbation légale ni paramétrage. Les réponses doivent être fournies par la commune, la comptabilité et le responsable légal avant développement.

| ID | Sujet / décision attendue | Proposition de conception | Répondant / preuve attendue | État |
|---|---|---|---|---|
| DEC-001 | Première copie gratuite : par acte, individu, type de copie ou demandeur? La portée exacte des documents/canaux? | Un entitlement unique lié à chaque acte concret est seulement l’hypothèse demandée; limiter aux délivrances effectivement réalisées. | Autorité métier/juridique; texte ou instruction communale. | À CONFIRMER |
| DEC-002 | Une demande annulée, rejetée ou jamais retirée consomme-t-elle le droit gratuit? | Libérer si aucune délivrance n’a été réalisée; tracer la réservation et son abandon. | Responsable état civil. | À CONFIRMER |
| DEC-003 | Tarif par extrait/copie/type/période; devise; taxe; date à laquelle tarif est appliqué. | Configurable, snapshot à la demande/facturation; aucun montant codé en dur. | Autorité tarifaire et comptable; barème approuvé. | À CONFIRMER |
| DEC-004 | Tarification par centre ou unique commune; société Odoo correspondante. | Tarif société, surcharge centre uniquement si décision expresse. | Comptabilité/mairie; organisation multi-company. | À CONFIRMER |
| DEC-005 | Journal, comptes de revenu, taxes, partenaire facturé, échéance et numérotation de facture. | `account.move` standard; configuration séparée par société. | Administrateur comptable. | À CONFIRMER |
| DEC-006 | Moyen d’encaissement: cash journal, virement, paiement en ligne ou POS. | Accounting manuel d’abord; POS optionnel seulement si caisse/session exigée. | Régisseur/comptabilité. | À CONFIRMER |
| DEC-007 | Quel niveau confirme l’encaissement : facture soldée et paiement rapproché à facture, ou rapprochement bancaire `is_matched` requis? | Facture postée, résiduel nul, `payment_state=paid`, paiements postés/reliés, puis confirmation Régisseur; rapprochement bancaire distinct. | Responsable comptable; procédure écrite de caisse. | À CONFIRMER |
| DEC-008 | Qui saisit le paiement et qui confirme la délivrance; cumul des rôles autorisé? | Séparer saisie et confirmation lorsque possible; à défaut, double trace et revue. | Responsable contrôle interne. | À CONFIRMER |
| DEC-009 | Régisseur: centres, société, droit aux données civiles minimales, possibilité de facture/avoir, impression de reçu. | Groupe dédié sans rôle système; droits Accounting minimum explicites. | Administrateur Odoo et commune. | À CONFIRMER |
| DEC-010 | Reçu comptable Odoo suffisant ou reçu légal séparé? Numéro, mentions, duplicata, annulation. | Dériver du paiement; extension de séquence seulement si obligation démontrée. | Comptable/juriste. | À CONFIRMER |
| DEC-011 | Partenaire facturé: citoyen, représentant, organisme; relation avec `etat.civil.individu`. | Mapping explicite, dédoublonnage, aucun lien automatique supposé. | Responsable métier/comptabilité. | À CONFIRMER |
| DEC-012 | Paiements partiels, trop-perçus, paiement couvrant plusieurs factures. | Pas de délivrance en partiel; paiements multi-facture exclus du premier lot. | Comptabilité. | À CONFIRMER |
| DEC-013 | Demande annulée après paiement: avoir/remboursement, réactivation ou annulation définitive. | Ne jamais supprimer facture/paiement comptabilisés; utiliser flux comptable approprié. | Comptabilité et responsable d’état civil. | À CONFIRMER |
| DEC-014 | Paiement remboursé après délivrance ou contesté. | Conserver délivrance, créer incident, traiter remboursement séparément. | Juridique/commune/comptabilité. | À CONFIRMER |
| DEC-015 | Rejet de justificatif: faut-il un état séparé, motif, re-soumission? | Ajouter uniquement si procédure formelle définie. | Responsable état civil. | À CONFIRMER |
| DEC-016 | Administrateur civil doit-il disposer aussi des ACL de facturation/paiement Account ou seulement des fonctions civiles? | Tout droit comptable vient de groupes Accounting; journaliser action admin. | DSI et comptabilité. | À CONFIRMER |
| DEC-017 | Suppression/remplacement de justificatif déjà reçu/vérifié; conservation. | Versionner/archiver et tracer; éviter unlink après vérification. | Juriste/archives/commune. | À CONFIRMER |
| DEC-018 | Durée de conservation des actes, factures, pièces, journaux de consultation et événements financiers. | Appliquer les politiques légales et comptables approuvées; ne pas inventer de durée. | Juriste/archives/comptable. | À CONFIRMER |
| DEC-019 | Rapport final PDF: informations, signatures physiques, watermark brouillon, re-téléchargement après délivrance. | Rapport copie distinct; accès privé réautorisé à chaque accès. | Responsable métier/juridique. | À CONFIRMER |
| DEC-020 | POS nécessaire? Matériel, session, clôture, caissier, remboursements, facture/reçu source. | Non dans premier lot; module POS optionnel relié à la même demande. | Régisseur/DSI. | À CONFIRMER |
| DEC-021 | Centres et sociétés, utilisateurs de test Agent/Officier/Régisseur/Admin, rôles cumulés. | Base de test isolée synthétique; identifiants saisis par testeur. | Administrateur Odoo. | À CONFIRMER |
| DEC-022 | Règle de délivrance à un représentant et vérification d’identité. | Données minimales et validation au guichet selon procédure. | Juridique/état civil. | À CONFIRMER |

## Décisions d’architecture déjà retenues comme recommandation

1. `account` standard est le seul ledger financier recommandé; ne pas construire une comptabilité parallèle.
2. Addon passerelle `etat_civil_account` séparé pour que le module civil reste installable sans Accounting.
3. POS est optionnel; le scénario le plus simple pour une commune est le paiement par journal caisse/bancaire Accounting, sauf besoin démontré de session POS.
4. Le paiement « confirmé pour délivrance » est une action métier séparée de `account.move.payment_state` et de `account.payment.state`.
5. Les liens de demande vers les actes sont des FK vers les trois modèles concrets; `etat.civil.acte.officiel` est abstrait.

Ces choix sont des recommandations documentaires; ils ne signifient pas que le code ou les modules existent.

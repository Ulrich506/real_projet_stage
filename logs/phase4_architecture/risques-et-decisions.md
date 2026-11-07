# Risques, décisions et points à arbitrer

**État : proposition d’architecture.** Aucun arbitrage métier n’est présumé acquis. Pas de modification de source ou de base pendant cette phase.

## Décisions nécessaires avant conception détaillée

| ID | Décision | Proposition de travail | Pourquoi elle est nécessaire |
|---|---|---|---|
| D01 | Module comptable cible | Addon passerelle `etat_civil_account` dépendant de `account`; pas de grand livre parallèle. | Aucun module financier personnalisé n’a été trouvé et `account` n’est pas installé dans la base revue. |
| D02 | Périmètre de « première copie » | Une gratuité par acte et catégorie de copie, à confirmer juridiquement; conserver une délivrance historique immuable. | Le code actuel ne porte pas d’historique de délivrance. « Première » peut dépendre du citoyen, de l’acte, du type de copie ou du bénéficiaire. |
| D03 | Gratuité et annulation | Définir si une copie autorisée puis non remise consomme le droit gratuit; seules les copies effectivement délivrées devraient normalement le consommer. | Évite la réutilisation après annulation et les délivrances gratuites multiples. |
| D04 | Tarifs | Préciser autorité compétente, période d’effet, monnaie, taxes, société et éventuelle variation par centre. Aucun montant par défaut. | Les montants ne doivent pas être codés en dur et une absence/ambiguïté doit bloquer la demande payante. |
| D05 | Régisseur | Identifier groupe, centres autorisés, capacité de recevoir/constater un paiement, de rapprocher une transaction, et de confirmer. | La confirmation est une action sensible; le justificatif seul ne prouve pas l’encaissement. |
| D06 | Moyen de paiement | Définir paiement comptabilisé/rapproché dans Odoo, encaissement externe rapproché ou POS. | Le statut `paid` dépend des flux comptables; saisie d’un paiement et paiement effectivement rapproché ne sont pas équivalents. |
| D07 | Facturation | Choisir société, journal, compte de revenu, taxes, partenaire, conditions et politique d’avoir/annulation. | `account.move` exige une configuration comptable valide; le projet n’a pas encore de ces modèles installés dans la base revue. |
| D08 | Reçu | Déterminer si le reçu légal est un rapport Odoo d’un paiement comptabilisé ou un reçu externe attaché, et son numéro légal. | Ne pas dupliquer le reçu et distinguer reçu justificatif de pièce vérifiée. |
| D09 | Paiement partiel | Décider si une copie requiert paiement intégral; proposition : aucune délivrance tant que le reliquat n’est pas nul et l’écriture comptablement réglée. | La règle doit couvrir paiements partiels, avoirs et annulations. |
| D10 | POS | Confirmer si la caisse Odoo POS est requise et son matériel/configuration. | `point_of_sale` est disponible dans le checkout mais désinstallé en base revue; intégration non incluse dans le premier lot. |
| D11 | Historique / conservation | Définir durée légale, audit des consultations/téléchargements, corrections, annulations et droits de suppression. | Les actes et preuves peuvent être soumis à conservation légale. |
| D12 | Pièces rejetées | Confirmer si un état `rejeté` est requis, son auteur, motif obligatoire, renvoi à l’agent et historisation. | Les états présents sont `a_fournir`, `recu`, `verifie`; aucune transition rejetée identifiée. |
| D13 | Administration | Confirmer que l’administrateur système est autorisé à toutes les transitions métier; préserver journalisation et séparation comptable. | Droit technique global ne doit pas effacer l’audit ni autoriser une écriture financière non comptabilisée. |
| D14 | Identité demandeur | Définir comment relier `etat.civil.individu` à `res.partner`, notamment en présence de doublons ou d’un représentant. | Ne pas forcer une identité comptable incorrecte ni créer des partenaires en doublon. |
| D15 | Accès multi-centres | Valider règle de rattachement acte, centre demandeur, centre de délivrance et société comptable. | Les règles Odoo multi-company ne remplacent pas les record rules métier de centre. |
| D16 | Environnement de test | Fournir une DB dédiée neuve/synthétique, rôles de test et comptes autorisés; aucune écriture dans la DB de revue pour ces parcours. | Les tests financiers et de concurrence impliquent des écritures et ne doivent pas toucher les actes existants. |

## Registre des risques

| ID | Gravité | Risque | Mesure proposée / preuve exigée |
|---|---|---|---|
| R01 | CRITIQUE | PDF final accessible par route, action rapport ou cache avant paiement. | Autorisation dans le modèle/contrôleur à chaque accès; aucun URL public ou `access_token` de contournement; tests HTTP/RPC anonymes et authentifiés avant/après confirmation. |
| R02 | ÉLEVÉE | Deux demandes concurrentes obtiennent une première copie gratuite. | Verrou transactionnel sur l’acte/clés de gratuité plus contrainte unique d’historique; test concurrentiel. |
| R03 | ÉLEVÉE | Confondre justificatif téléversé, reçu vérifié ou statut manuel avec paiement. | Lire le document financier canonique et contrôler société, montant, devise, état, annulation, rapprochement et journal; aucune confirmation par simple pièce jointe. |
| R04 | ÉLEVÉE | Double facture, reçu ou encaissement suite à double clic/retry. | Idempotence par demande, contrainte de facture unique, transitions atomiques et test de répétition/webhook double. |
| R05 | ÉLEVÉE | Montant modifié par RPC ou tarif modifié après demande. | Champs prix calculés côté serveur; snapshot verrouillé de tarif/devise/taxe; recalcul/validation au moment de la facture. |
| R06 | ÉLEVÉE | Fuite inter-centres ou multi-company via relations et rapports. | Record rules sur demande et document; contrôler également les relations M2O et routes; tests direct URL, RPC, ORM et rapport. |
| R07 | ÉLEVÉE | Suppression d’une pièce justificative ou d’un historique utile. | Checkout source ACL actuel donne `unlink=1` au groupe Admin pour pièce; vérifier runtime avant tout changement. Concevoir conservation/archivage et auditer suppression. |
| R08 | ÉLEVÉE | État comptable faussement modifié par méthode publique/custom. | Ne jamais écrire `payment_state`; laisser Account calculer selon rapprochements; droits serveur et tests RPC. |
| R09 | MOYENNE | Facturation impossible par configuration manquante (journal, taxes, compte, partenaire). | Contrôle préalable explicite et message bloquant; configuration documentée par société. |
| R10 | MOYENNE | Changement de tarif ou de fiscalité après demande affecte le montant historique. | Snapshot montant/devise/taxes et référence de version du tarif; modification tarifaire sans altérer les demandes déjà facturées. |
| R11 | MOYENNE | POS crée un flux distinct et des ventes incohérentes avec la demande. | Garder POS hors lot 1; intégration optionnelle avec relation `pos.order` et même requête canonique, valider remboursements et clôture. |
| R12 | MOYENNE | `res.partner` dupliqué ou identité de facturation non pertinente. | Décision métier D14 et contrôles de rapprochement avant génération de facture. |
| R13 | MOYENNE | Rupture d’upgrade si dépendance account imposée à tous les déploiements. | Addon passerelle séparé; installation seulement dans une base autorisée et migration testée. |
| R14 | FAIBLE | Trous de séquence après transaction annulée. | Documenter que les séquences Odoo peuvent avoir des trous; ne pas réutiliser une référence. |

## Décisions prises dans ce document

- Pas de montant tarifaire fictif, de rôle Régisseur déjà déclaré, ni de module financier personnalisé inventé.
- Le POS reste une extension optionnelle tant que D10 n’est pas tranchée.
- Les termes « reçu justificatif », « reçu comptable », « pièce vérifiée » et « paiement confirmé » restent distincts.
- Le statut global demeure **B — Partiellement validé**.

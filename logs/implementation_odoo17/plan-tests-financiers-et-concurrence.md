# Plan d'exécution — authentification, finances, rapports et concurrence

Date de préparation : 2026-11-06 00:52 EAT (+03:00). Cible prévue : base synthétique neuve uniquement, Odoo 17.0, Python 3.14.4, PostgreSQL 18.6; modules `etat_civil`, `etat_civil_auth_email`, `etat_civil_account`. Aucun scénario ci-dessous n'a été exécuté dans le cadre de ce plan. Environnement dédié non créé.

## Règles communes

- Créer des données et comptes fictifs dans une base isolée; ne jamais utiliser une base active, de revue ou contenant des données réelles.
- Capturer les logs Odoo/PostgreSQL expurgés de secrets, les IDs synthétiques, heures, états avant/après, assertions et empreintes des preuves. Ne pas archiver mots de passe, cookies ou jetons.
- Réinitialiser la base ou les données synthétiques entre scénarios afin d'éviter les interactions.
- La règle de gratuité doit être identifiée comme configuration de test, sans prétention juridique. La nécessité du rapprochement bancaire pour valider un paiement requiert une décision métier avant d'en faire une condition.
- Pour chaque ligne, le résultat observé est **non exécuté**. Les statuts ne sont pas des validations.

## Scénarios

| ID / scénario | Préconditions et données synthétiques | Rôle(s) / action | Résultat attendu | Résultat observé / preuve à conserver |
|---|---|---|---|---|
| AUTH-1 Installation compatible | Base neuve; comptes de test dont les logins respectent la politique e-mail | Admin synthétique; installer le module d'auth e-mail puis ouvrir une session web | Installation complète; login conforme fonctionne | Non exécuté. Log d'installation et preuve d'auth sans secret |
| AUTH-2 Login incompatible | Base neuve séparée; compte actif technique/humain avec login non conforme clairement étiqueté synthétique | Admin synthétique; tenter l'installation | Installation bloquée avec diagnostic non sensible; aucune modification de login | Non exécuté. Log d'échec et comparaison d'état |
| AUTH-3 Mise à jour / retour arrière | Base synthétique à version antérieure, logins documentés; sauvegarde synthétique avant changement | Admin; mise à jour puis désactivation/retour selon mécanisme disponible | Aucun compte verrouillé; retour réversible démontré | Non exécuté. Versions, snapshot et tests de connexion |
| WEB-1 Accès par rôle | Comptes synthétiques Agent, Officier, Régisseur, Administrateur; centre et actes fictifs | Chaque rôle; login dans navigateur, menus, création/lecture autorisées et refusées | Menus et contrôle serveur concordent; erreurs/redirections attendues | Non exécuté. Captures expurgées, journal HTTP, assertions par rôle |
| FIN-1 Demande gratuite | Acte et demande fictifs; configuration de gratuité de test, identifiée comme non juridique | Agent soumet; Officier valide selon workflow; rôle habilité délivre | Pas de facture indue; une seule délivrance; historique cohérent | Non exécuté. IDs, états, règles de test et PDF |
| FIN-2 Paiement intégral | Demande payante fictive; produit, tarif, devise, partenaire et taxes définis dans la config de test | Agent crée; comptabilité poste facture et enregistre paiement; Régisseur confirme; rôle métier délivre | Facture liée correcte, total égal au dû, solde nul selon règle décidée; délivrance autorisée | Non exécuté. Facture, lignes, rapprochements, paiements, événements et PDF |
| FIN-3 Paiement partiel | Même configuration; facture valide et paiement inférieur au total | Régisseur tente confirmation puis rôle métier tente délivrance | Refus tant que le solde dû n'est pas nul si règlement intégral requis | Non exécuté. Solde, réponse et absence d'événement de délivrance |
| FIN-4 Facture incohérente | Demandes séparées; montants inférieur/supérieur, autre devise, mauvais partenaire, facture annulée/non postée; paiement annulé/non rapproché/autre facture; cas multi-factures et multi-demandes | Comptable puis Régisseur; lier, poster/payer ou confirmer selon le cas | Toute discordance bloque la confirmation; ne pas accepter un simple `account.payment` sans preuve liée à la facture | Non exécuté. IDs reliés, états, résidus et raison du rejet |
| FIN-5 Annulation / avoir / remboursement | Demande payée fictive; mécanismes standard `account` configurés; décision sur remboursement définie | Régisseur/comptable; annuler demande ou facture, créer avoir, rembourser, retenter délivrance | Traçabilité complète; pas de délivrance interdite après annulation; aucun remboursement simulé si feature absente | Non exécuté. Chaîne facture/avoir/paiement/remboursement et événements |
| PDF-1 Accès direct | Acte/demande fictifs; compte par rôle; URLs de rapports actuels et rapports de demande | Agent, Officier, Régisseur, Admin; requêter directement les URL PDF avant/après autorisation | Impression interne respecte permissions; PDF officiel indisponible avant contrôles et accessible seulement après workflow | Non exécuté. Statut HTTP, identité synthétique, hash PDF et journal serveur |
| CONC-1 Soumission concurrente | Même demande synthétique; deux sessions/transactions indépendantes synchronisées par barrière | Deux Agents soumettent simultanément | Une seule transition/événement; état final valide, pas de transaction partielle | Non exécuté. Horodatages, IDs de transaction et compte d'événements |
| CONC-2 Délivrance concurrente | Demande autorisée; deux connexions PostgreSQL/requêtes HTTP | Deux rôles autorisés délivrent simultanément | Une délivrance, un événement et un artefact officiel au plus | Non exécuté. Journal de concurrence et historique transactionnel |
| CONC-3 Première copie gratuite concurrente | Même acte; deux demandes synthétiques de première copie en transactions distinctes | Deux Agents soumettent à la fois | Une seule demande consomme la gratuité si telle est la règle de test; aucun double avantage | Non exécuté. État de réservation et historique |
| CONC-4 Confirmation financière concurrente | Facture liée, payée selon règle; deux sessions Régisseur | Confirmer simultanément la même demande | Une seule transition/écriture d'événement; pas de double effet | Non exécuté. États de facture/demande et événements |
| CONC-5 Annulation contre délivrance | Demande autorisée; requêtes synchronisées sur transactions séparées | Régisseur annule pendant qu'un rôle habilité délivre | Résultat sérialisé cohérent; la règle métier d'annulation prévaut sans délivrance post-annulation si exigé | Non exécuté. Ordre des verrous, état final et événements |

## Critères d'arrêt

Arrêter si l'identité de la base, le filestore ou l'instance n'est pas certaine; si une règle de délivrance/gratuité ou de rapprochement requiert une décision métier; si un scénario pourrait atteindre un service ou une donnée réelle; ou si les logs ne permettent pas de corréler transactions et requêtes. Les `ReadTimeout` de la régression doivent être diagnostiqués avant de relancer une suite HTTP complète.

**Statut global du plan : TERMINÉ MAIS NON TESTÉ.** Aucun résultat observé n'est revendiqué et aucune preuve d'exécution n'existe pour ces scénarios.

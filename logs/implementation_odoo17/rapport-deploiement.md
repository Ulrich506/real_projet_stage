# Évaluation de déploiement

## Décision

**NON PRÊT POUR PRODUCTION — statut B, partiellement validé.** Les modules sont présents et installés dans des bases synthétiques. La passerelle n’a pas reçu de configuration comptable communale et aucun paiement réel/synthétique complet n’a été exécuté.

## Conditions bloquantes avant déploiement

1. Inventorier les comptes réels, classifier les comptes techniques, confirmer les adresses auprès de leurs propriétaires et préparer une migration réversible. Ne pas installer la validation stricte dans une base dont l’admin n’a pas déjà un login e-mail accepté.
2. Décider si la première copie gratuite par acte est la règle métier approuvée et définir les exceptions; configurer les tarifs par prestation/centre/date sans montant codé en dur.
3. Définir devises, journaux, comptes de revenus/recevables, taxes, produits, fiscal positions et conditions de paiement; comparer le total facture au montant présenté et bloquer tout écart.
4. Clarifier la différence entre les rapports d’acte directement disponibles et la copie délivrée payante; protéger les routes directes ou définir leur usage interne de manière vérifiable.
5. Concevoir puis tester les avoirs, remboursements, paiements annulés, paiement partiel et contestation; un statut `paid` conservé dans Accounting ne doit pas suffire après remboursement.
6. Compléter les tests multi-transaction de gratuité/délivrance, tests HTTP/RPC des rapports, accès inter-centres, téléchargement d’images et une session Chromium authentifiée.
7. Installer/mettre à jour seulement dans une base de préproduction autorisée, avec sauvegarde PostgreSQL + filestore correspondant et restauration testée.

## Plan de déploiement futur

- Geler et identifier le commit/revision approuvé sans écraser le travail Git actuel.
- Construire une DB de préproduction isolée; appliquer d’abord le précontrôle des identifiants puis le plan de migration validé.
- Installer `etat_civil_auth_email`, `account`, puis `etat_civil_account` dans l’ordre des dépendances, après config comptable.
- Exécuter tests unitaires, intégration, sécurité, navigateur, PDF et restauration; recueillir les preuves.
- Obtenir acceptation métier et sécurité avant ouverture aux comptes humains.
- Retour arrière : basculer vers un nouveau nom de DB restauré depuis le couple sauvegarde+filestore cohérent; ne jamais restaurer par-dessus une base existante.

Aucune phase de déploiement réelle n’a été exécutée.

Environnement exécuté lors des essais : Python 3.14.4. La documentation d’installation source Odoo 17 indique Python 3.10 ou ultérieur; les tests réussis confirment l’exécution dans ce venv, sans valider les modules optionnels ni les dépendances propres à la commune.

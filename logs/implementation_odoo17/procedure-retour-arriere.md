# Procédure de retour arrière et sauvegardes effectivement créées

## Sauvegardes de test présentes

Les quatre ZIP listés dans `environnement-developpement.md` ont été générés par Odoo avec `dump_db(..., backup_format='zip')`, ce qui inclut dump PostgreSQL et filestore du même nom de base. Tous sont mode 600; `unzip -tq` a retourné « No errors detected ». Les SHA-256 sont documentés et recalculés dans `SHA256SUMS.txt` ou le journal de sauvegarde.

Ces opérations n'établissent pas qu'une restauration marche. Aucun ZIP n'a été restauré. Les sauvegardes ne concernent que des DB synthétiques. La base de revue et les données réelles n'ont pas été sauvegardées ou copiées par cette intervention.

## Retour arrière environnement de développement

1. Confirmer le nom exact de la base de test et le chemin de son filestore sous `data/implementation_odoo17_dev/filestore/<db>`.
2. Vérifier le SHA-256 de l'archive choisie, son mode d'accès et `unzip -tq`.
3. Restaurer exclusivement vers un nouveau nom PostgreSQL préalablement vérifié absent; jamais écraser une base existante. Le filestore correspondant doit être restauré par le mécanisme Odoo depuis la même archive.
4. Valider restauration avec Odoo isolé, modules, login de test synthétique, intégrité des pièces et tests ciblés.
5. Ne supprimer aucune DB/filestore source durant cette procédure; aucune suppression n'est autorisée dans cette mission.

## Rollback d'implémentation

- Une mise à jour de module sur une DB déjà utilisée doit utiliser un dump cohérent avant opération et une restauration vers une nouvelle DB. Ne jamais « désinstaller » Account ou supprimer ses écritures pour revenir en arrière.
- Une facture brouillon peut être annulée via le flux natif `account.move.button_cancel`; une facture postée nécessite l'avoir/remboursement standard approprié. Un paiement comptabilisé n'est pas supprimé.
- Pour annuler uniquement le correctif API, comparer le fichier avec `backups/source-before-auth-api/main.py` et réappliquer manuellement le hunk concerné en conservant les changements préexistants; ne pas copier le snapshot complet par-dessus le fichier courant.
- Pour les nouveaux addons, garder le code; ne pas lancer leur désinstallation sur une DB ayant des données métier sans plan de migration et sauvegarde validée.
- Aucune migration utilisateur n'a eu lieu; aucun mapping login/password/hash n'existe à inverser.

## Portée réelle

Aucune restauration, rollback de migration ni restauration de sauvegarde n'a été testée. Aucune opération de retour arrière n'a été nécessaire. Cette procédure est un runbook de développement, pas un runbook approuvé pour production.

## Retour arrière de l’audit final

- Le source initial de `custom_addons/etat_civil_account/models/copy_request.py` avant verrouillage est conservé exactement dans `backups/source-before-final-audit/copy_request.py`; empreinte à vérifier dans `SHA256SUMS.txt`. Pour rétablir ce seul fichier, comparer d’abord les deux versions puis recopier le snapshot après validation. Ne pas écraser les autres travaux.
- Les changements du code n’ont été installés/mis à jour que dans `etat_civil_final_audit_tests_20261105`, copie synthétique. Pour refaire une base de test antérieure, restaurer l’archive `backups/etat_civil_final_audit_tests_20261105_pre_update_verified.zip` vers un **nouveau** nom disponible et conserver son filestore restauré correspondant.
- La base `etat_civil_restore_validation_20261105_01` est un clone d’essai utilisé pour logins synthétiques; ne pas la confondre avec la source de l’archive.
- Aucune commande de retour arrière n’a été exécutée sur une base existante. Ne pas supprimer les bases/fichiers de test dans le cadre de cette procédure sans demande distincte.

## Retour arrière — phase de sécurisation finale (2026-11-05)

Les fichiers source avant cette intervention sont archivés sous `backups/source-before-phase-next/` avec empreintes conservées dans le rapport/journal de phase. Avant tout retour arrière, comparer le fichier exact courant à ce snapshot et réappliquer uniquement le hunk concerné; ne jamais restaurer un fichier complet par-dessus d’autres changements préexistants.

Les bases créées/restaurées dans cette phase sont `etat_civil_phase_next_auth_20261105_01` et `etat_civil_phase_next_finance_20261105_01`, toutes deux synthétiques. Aucune opération de suppression n’a été effectuée. Pour revenir à un état antérieur, utiliser l’archive synthétique indiquée dans le rapport et restaurer vers un nouveau nom PostgreSQL absent, avec le filestore contenu dans cette même archive. Ne pas restaurer par-dessus les bases de test existantes, et ne jamais réutiliser leur filestore sous un autre nom.

La mise à jour Auth e-mail comporte une pré-migration qui doit échouer avant changement si des logins actifs sont non conformes. Aucun login réel n’a été transformé. Ne pas rétrograder automatiquement le module ni supprimer l’index; préparer le retour sur une nouvelle base à partir d’un backup autorisé et faire vérifier l’authentification avant bascule.

Les factures/paiements comptabilisés ne se rollbackent pas par suppression. Une annulation après comptabilisation exige les mécanismes standards d’avoir/remboursement et une décision du responsable comptable. La présente intervention n’a généré aucune écriture financière.

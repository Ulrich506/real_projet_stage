# Environnements de développement isolés

Mise à jour : 2026-11-05. Aucun environnement de production ou de revue n'a été utilisé comme cible d'écriture.

## Instances présentes en fin d'intervention

| Base | Usage / modules installés | HTTP / gevent | État |
|---|---|---|---|
| `etat_civil_dev_email_account_20261105` | Base de développement initiale, `etat_civil`; sans données métier | 18171 / 18172 | Serveur laissé en fonctionnement |
| `etat_civil_dev_email_account_auth_20261105` | Validation email et `account`/passerelle; version d'installation intermédiaire | 18173 / 18174 | Serveur laissé en fonctionnement; conserver comme instance intermédiaire |
| `etat_civil_dev_finalcheck_20261105` | Version fonctionnelle précédente des deux addons | 18175 / 18176 | Serveur laissé en fonctionnement |
| `etat_civil_dev_regression_20261105` | Suite complète `etat_civil` et derniers tests auth/finance | 18177 / 18178 | Serveur laissé en fonctionnement après les tests |
| `etat_civil_dev_verify_final_20261105` | Code final de l'intervention, modules civil, auth email, account et passerelle | 18179 / 18180 | Serveur laissé en fonctionnement; cible recommandée pour inspection |
| `etat_civil_dev_latest_20261105` | Dernière révision après contrôle d'accès étroit des factures | 18181 / 18182 | Serveur final laissé en fonctionnement; cible la plus récente |

Chaque base utilise le filestore Odoo propre du même `data_dir` :
`/home/ulrich/tous_les_projet/stage_l3_odoo/data/implementation_odoo17_dev/filestore/<nom exact de base>`.
Aucun filestore d'une autre base n'a été associé.

## Configuration et logs

Configurations temporaires en mode 600 :

- `/tmp/etat_civil_dev_20261105.conf`
- `/tmp/etat_civil_dev_account_20261105.conf`
- `/tmp/etat_civil_dev_finalcheck_server_20261105.conf`
- `/tmp/etat_civil_dev_regression_server_20261105.conf`
- `/tmp/etat_civil_dev_verify_final_server_20261105.conf`
- `/tmp/etat_civil_dev_latest_server_20261105.conf`

Les journaux sont séparés dans `logs/implementation_odoo17/`: `odoo-dev.log`, `odoo-account-dev.log`, `odoo-finalcheck.log`, `odoo-finalcheck-server.log`, `odoo-regression.log`, `odoo-regression-server.log`, `odoo-verify-final.log`, `odoo-verify-final-server.log`, `odoo-latest.log`, `odoo-latest-server.log`. `max_cron_threads=0`. Les processus utilisent le checkout Odoo local et `custom_addons`.

Tous les ports de ces instances ont été vérifiés libres avant leur allocation. Les erreurs de collision initiales sur 18171 et 18173 se sont produites avant installation/arrêt d'un processus et ont été corrigées en donnant des ports distincts; aucun service préexistant n'a été arrêté.

## Source de données et sauvegardes

Les DB de développement sont neuves; aucune copie de la base de revue n'a été restaurée. Un dump préexistant `sauvegarde_avant_installation.dump` concerne une autre base et n'a pas été utilisé. Aucun test avec données personnelles réelles n'a été effectué.

Archives Odoo ZIP créées avec `odoo.service.db.dump_db` (base et filestore correspondants), mode 600, `unzip -tq` sans erreur :

- `backups/etat_civil_dev_email_account_20261105_pre_auth.zip` — SHA-256 `4f21cb7602fea08efdebcba94352a3783bd9b111e9fef1e0ba4c7872b323f901`.
- `backups/etat_civil_dev_email_account_auth_20261105_pre_account.zip` — SHA-256 `8a8f18b48c2bd4349d6f0b475be44cd71a7fcdc2751079d75e4743fed8c80357`.
- `backups/etat_civil_dev_finalcheck_20261105_pre_source_update.zip` — SHA-256 `be571b1640e890401e6602a778265e8f791b94506ca5459737b5379441fb5b34`.
- `backups/etat_civil_dev_regression_20261105_pre_finance_retest.zip` — SHA-256 `61ac9b97e9f32b4f622b45b58e524f8685009557c76c2b65e04d4269cc0903d6`.

Intégrité ZIP vérifiée. Aucune restauration de ces sauvegardes n'a été testée; ne pas présenter le contrôle ZIP comme un test de restauration.

## Protection des services existants

Les ports 8071, 18071/18072 et 18205 sont restés en place et n'ont pas été redémarrés. La base de revue `etat_civil_final_review_20261105_1304` n'a reçu aucune écriture. Aucune préproduction n'a été créée.

**Statut : TERMINÉ ET TESTÉ** pour les instances synthétiques et les ports dédiés. **PARTIEL** pour la restauration testée et les données de validation réelles.

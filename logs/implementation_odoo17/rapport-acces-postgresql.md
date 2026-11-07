# Rapport — accès PostgreSQL en lecture seule

Date/heure du relevé : 2026-11-06 00:52 EAT (+03:00). Odoo 17.0, Python 3.14.4, PostgreSQL 18.6 sur `127.0.0.1:5432`. Base de test citée pour la régression : `etat_civil_phase_next_finance_20261105_01`; aucune connexion d'écriture ni commande de création de base n'a été exécutée pendant ce diagnostic. Modules concernés : `etat_civil`, `etat_civil_auth_email`, `etat_civil_account`.

## Résultats

| Contrôle | Résultat |
|---|---|
| Accès au serveur/catalogue avec les paramètres PostgreSQL déjà configurés pour Odoo | Connexion de lecture seule réussie selon le contrôle précédent; aucune information d'authentification ou secret n'est reproduit. |
| Rôle utilisé | `odoo17`, d'après le paramétrage existant; rôle non-superutilisateur. |
| `CREATEDB` | `true`; capacité de création de base rapportée par l'inspection précédente des attributs de rôle. |
| Création de rôles | Non autorisée (`CREATEROLE=false` selon le relevé précédent). |
| Inventaire du catalogue | 41 bases connectables étaient visibles au relevé précédent. Leurs noms ne sont pas repris ici. |
| Version / écoute | PostgreSQL 18.6, écoute observée sur l'adresse loopback `127.0.0.1`, port 5432. |
| Authentification effective (`pg_hba.conf`) | Inconnue. La lecture de `pg_hba_file_rules` a été refusée (SQLSTATE `42501`); le fichier `/etc/postgresql/18/main/pg_hba.conf` est lisible seulement par `postgres` (mode 0640). |

La première tentative historique de lecture du catalogue a échoué avec un `ProgrammingError`, mais le message et le SQLSTATE n'ont pas été conservés; une nouvelle séquence de lecture seule a ensuite réussi. La cause exacte de cette erreur antérieure est donc **inconnue**, et elle n'a pas été reproduite dans ce diagnostic. L'accès actuellement démontré suffit à lire les métadonnées et le privilège `CREATEDB` est démontré; le mécanisme de validation du mot de passe/socket et les règles HBA ne le sont pas. Aucune permission n'a été contournée ni demandée.

## Portée et limites

- L'accès de l'application au rôle existant a déjà été observé; aucun mot de passe, DSN complet, paramètre secret ou contenu de configuration sensible n'est consigné.
- `CREATEDB` est un privilège disponible, pas une autorisation de créer une base pour ce run. Tout nouveau nom doit être contrôlé à nouveau immédiatement avant une création.
- Le candidat `etat_civil_validation_isolated_20261106_0034` avait été examiné dans le contrôle précédent. Son absence n'est pas certifiée à l'heure de ce rapport; la revalidation préalable à toute création reste obligatoire.
- Les noms des autres bases n'ont pas été publiés. Aucun catalogue n'a été modifié.
- Pas de test financier, migration, création, restauration ou écriture de base dans cette mission.

## Preuves et actions futures

Preuves disponibles : résultat de connexion au catalogue en lecture seule, résultat d'attribut du rôle, version PostgreSQL, et refus explicite de la vue HBA avec SQLSTATE `42501`. Les commandes exactes de connexion et la ligne SQL d'attribut n'ont pas été conservées dans le journal de mission; elles ne sont donc pas reconstituées a posteriori.

Si l'authentification PostgreSQL exacte est requise, l'administrateur PostgreSQL peut confirmer la règle correspondante sans divulguer de secret, ou accorder un accès de diagnostic minimal et temporaire. Ne pas essayer d'accéder au fichier HBA sous une autre identité.

**Statut : TERMINÉ MAIS NON TESTÉ** pour la possibilité d'utiliser le rôle `odoo17` afin de créer une base neuve; `CREATEDB` est visible, mais aucune création de base n'a été tentée. L'identification du mode d'authentification reste **BLOQUÉE** par les permissions de lecture de la configuration PostgreSQL.

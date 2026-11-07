# Tests de connexion — résultats et limites

Instance finale testée : Odoo 17, base synthétique `etat_civil_dev_latest_20261105`, HTTP 18181 / gevent 18182; module `etat_civil_auth_email` installé. Aucun identifiant réel ou mot de passe existant n'a été utilisé.

| ID | Vérification | Résultat | Statut |
|---|---|---|---|
| AUTH-01 | Normalisation d'un e-mail valide, trim et domaine en minuscules | Réussi; local-part conservée | VALIDÉ |
| AUTH-02 | Login simple | Rejeté par validation | VALIDÉ |
| AUTH-03 | E-mail mal formé (`agent@`, `@domaine`, vide) | Rejeté | VALIDÉ |
| AUTH-04 | Authentification `_login` avec syntaxe invalide | `AccessDenied` générique | VALIDÉ |
| AUTH-05 | Création ORM login invalide | `ValidationError` | VALIDÉ |
| AUTH-06 | Création ORM valide et normalisation domaine | Réussi | VALIDÉ |
| AUTH-07 | Modification vers login invalide | `ValidationError` | VALIDÉ |
| AUTH-08 | Doublon insensible à la casse | Rejeté; index unique présent | VALIDÉ |
| AUTH-09 | Formulaire HTTP `/web/login` | HTTP 200, champ e-mail vérifié dans DOM | VALIDÉ |
| AUTH-10 | Capture Chromium formulaire | Chrome 153.0.8010.52, label et champ visibles | VALIDÉ |
| AUTH-11 | Health API, DB filtrée | HTTP 200, DB annoncée = DB finale synthétique | VALIDÉ |
| AUTH-12 | API login syntaxe invalide et DB différente de `request.db` | Les deux réponses HTTP 401 et le même message générique; succès de connexion non soumis | PARTIEL |
| AUTH-13 | Identifiants invalides par import/RPC | Couverture de `res.users.create/write`; tests HTTP authentifiés import non exécutés | PARTIEL |
| AUTH-14 | Reset mot de passe, OAuth/SSO et comptes techniques | Non exécutés | NON TESTÉ |
| MIG-01 à MIG-09 | Migration réelle, conservation des groupes/centres/password et rollback | Aucun vrai compte importé ou modifié | EN ATTENTE |

Suite ciblée finale (journal `odoo-latest.log`) : module email indique 9 au compteur Odoo; résultat global : `0 failed, 0 error(s) of 12 tests`; le module finance indique 7. Tests HTTP sur 18181 : e-mail invalide → 401 générique; valeur `db` d'un autre nom que la DB filtrée → même 401. Les secrets de test synthétiques n'ont pas été conservés. Une première exécution antérieure avait une assertion échouée (`@example.org` accepté par le validateur tiers); le helper a été corrigé et la suite finale répétée sans erreur. Sans authentification réelle avec identifiants autorisés, le succès de connexion d'un humain reste distinct et non exécuté.

Preuve image : `proofs/login-email-18181.png`. Aucun mot de passe, hash, cookie ou session n'est conservé.

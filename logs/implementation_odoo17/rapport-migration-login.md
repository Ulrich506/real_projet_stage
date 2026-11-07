# Rapport migration des logins — aucune migration réelle

Base d'inventaire : `etat_civil_dev_verify_final_20261105`, installation neuve Odoo 17 sans données du projet. Les compteurs portent exclusivement sur les cinq comptes de base fournis par une DB Odoo vierge; ils ne doivent pas être attribués aux utilisateurs réels de la commune.

| Mesure | Résultat |
|---|---:|
| Utilisateurs inventoriés dans la DB synthétique | 5 |
| Actifs / archivés | 1 / 4 |
| Login déjà e-mail valide | 0 |
| Login non e-mail avec contact syntaxiquement valide | 2 |
| Login non e-mail sans contact valide | 3 |
| Collision de login après normalisation | 0 |
| Utilisateurs du projet migrés | 0 |
| Login, mot de passe/hash, groupe ou affectation modifiés | 0 |
| Utilisateurs supprimés / mots de passe réinitialisés | 0 / 0 |
| Adresse fabriquée | 0 |

Les cinq comptes Odoo par défaut ne sont pas classés comme utilisateurs humains, administrateurs réels ou services faute d'identification métier. Aucun mapping automatique n'est préparé. Le fichier `utilisateurs-a-migrer.csv` reste un gabarit sans adresse personnelle et sans ligne migrable.

## Décision de migration

La migration est **BLOQUÉE** tant que la base de développement cible ne contient pas les comptes réels autorisés et que les adresses e-mail réelles de chaque compte concerné ne sont pas fournies/vérifiées. Les deux contacts syntaxiquement valides des comptes de base ne sont pas adoptés comme login sans preuve d'attribution réelle. Aucun login non e-mail n'est converti.

Une sauvegarde cohérente DB+filestore a été créée pour les environnements synthétiques uniquement; aucune sauvegarde de la base active n'a été faite. Les mots de passe et hashes n'ont jamais été extraits ou écrits dans un rapport.

**Résultat : 0 utilisateur migré; 5 comptes Odoo synthétiques nécessitent une décision de classification; nombre de vrais utilisateurs nécessitant une adresse confirmée : inconnu, car annuaire réel non consulté.**

# Rapport — pièces justificatives, textes officiels et consultation agents

## Corrections
- Texte intégral généré automatiquement à la création des actes de naissance, mariage et décès à partir des données enregistrées.
- Le texte généré est actualisé lorsque les détails métier sont modifiés tant qu'il n'a pas été personnalisé manuellement.
- Les pièces obligatoires restent synchronisées automatiquement avec les actes, et une ligne supplémentaire peut être ajoutée au dossier.
- L'ajout manuel d'un document portant le même nom fusionne les fichiers joints dans la pièce existante au lieu de produire l'erreur « Ce document figure déjà... ».
- Les agents peuvent consulter les actes de naissance, mariage et décès de tous les centres en lecture seule; leurs droits d'écriture restent limités à leur centre.

## Vérifications
- Compilation Python des modèles et tests : réussie.
- Validation XML des vues et règles de sécurité : réussie.
- Contrôle `git diff --check` : réussi.

## Validation restante
- Mise à jour du module sur une base isolée ou autorisée.
- Exécution de tests serveur ciblés de pièces, textes et règles agent.

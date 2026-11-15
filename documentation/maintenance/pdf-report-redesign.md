# Refonte des rapports PDF d’état civil

## Périmètre réalisé

Le module `etat_civil` possède des actions et gabarits QWeb distincts pour les
actes de naissance, mariage, décès et les avis de mention marginale. Les actes
et avis utilisent A4 portrait. Le module `etat_civil_account` produit une
quittance séparée sur un format thermique provisoire de 80 × 130 mm.

Les quatre documents ODT de référence ont été convertis en PDF et examinés
visuellement. Ils sont en A4 portrait; leur composition place les références
du centre et du registre en colonne latérale, le texte du document dans la
colonne principale, et la signature/zone QR en partie basse. La conversion
LibreOffice montre des chevauchements de colonnes dans certains ODT; ces
artefacts de mise en page source ne sont pas repris. La photographie de la
quittance sert de référence de contenu et de format étroit; elle ne précise
pas de dimensions physiques vérifiables.

Les données personnelles figurant dans les exemples ne sont pas intégrées.
Les textes libres de l’acte sont affichés uniquement lorsqu’ils ont été saisis
manuellement; le texte généré automatiquement n’est pas repris comme
transcription officielle. Les informations facultatives absentes sont omises,
pas remplacées par une valeur fictive.

## Données, numéros et contrôles

- Les actes reprennent les personnes, dates, lieux, relations, mentions, statut,
  identité de validation, empreinte et QR depuis leurs enregistrements ORM.
- Les mentions affichent leur référence, leur texte, leur date, la personne et
  les actes réellement associés.
- Dans les gabarits antérieurs encore utilisés pour le mariage, le décès et
  l'avis de mention, les brouillons portent une mention d'impression non
  officielle. Depuis la reconstruction de naissance, le PDF officiel de
  naissance est refusé tant que l'acte n'est pas validé ou rectifié; l'action
  reste disponible depuis la fiche.
- L'extrait de naissance n'ajoute ni bandeau ni empreinte textuelle. Le contrôle
  d'intégrité est toujours effectué côté serveur et le QR reste dans la zone
  prévue par le modèle.
- Les actions de rapport et les vérifications Python appliquent les ACL, règles
  d’accès et restrictions territoriales. La mention reste réservée à l’officier
  et à l’administrateur d’état civil.
- Aucun rapport ne crée d’acte, de mention, de paiement ou de quittance et ne
  demande de nouveau numéro. Les séquences existantes ne sont pas modifiées.
- Une quittance affiche les copies, le tarif figé de la demande, le montant de
  cette opération, le moyen et la référence de transaction. Avant rendu, ce
  montant est recalculé depuis le rapprochement comptable/POS et doit
  correspondre à l’encaissement lié. Les opérations non rapprochées ou dont le
  montant ne concorde plus sont refusées.
- Le pipeline PDF natif Odoo 17 sépare les documents par leur classe `.article`.
  Les rapports fournissent cette classe et les attributs du modèle/enregistrement
  sur chaque document; leurs styles sont inclus dans l'article pour rester
  disponibles après cette séparation. Cela conserve la déclaration UTF-8 du
  layout Odoo et évite le mojibake observé quand le contenu était traité comme
  un fragment HTML sans encodage.
- Les quittances affichent les montants en format français avec le symbole de
  la devise et écrivent le montant réellement encaissé en lettres françaises.
  La conversion conserve l'unité et le sous-unité configurées sur la devise.

## Validation visuelle et technique — 9 novembre 2026 (version antérieure)

Les résultats ci-dessous concernent les gabarits antérieurs à la reconstruction
de l'acte de naissance décrite plus bas. Ils ne valident pas la nouvelle mise
en page de naissance.

Les PDF ont été rendus par la suite de tests Odoo 17 sur la base isolée
`etat_civil_odoo17_mga_generic_test_20261108`, puis extraits en images PNG à
120 dpi et inspectés visuellement. Le lancement ciblé final a exécuté
21 post-tests : 0 échec et 0 erreur. Le résumé Odoo ne donne pas de compteur
distinct d'éléments ignorés. Après les corrections, la suite complète des
modules `etat_civil`, `etat_civil_account` et `etat_civil_pos` a également
réussi : 119 post-tests, 0 échec et 0 erreur.

| Document | Pagination / format obtenu | Vérification visuelle et fonctionnelle | Statut |
|---|---|---|---|
| Naissance | 1 page A4 portrait | Données ORM et champs facultatifs affichés; texte lisible | Rendu vérifié |
| Naissance — nom long | 1 page A4 portrait | Nom composé, apostrophe et adresse longue visibles sans coupure | Rendu vérifié |
| Naissance validée | 1 page A4 portrait | Identité de validation, empreinte et QR visibles | Rendu vérifié |
| Mariage | 1 page A4 portrait | Deux conjoints et deux témoins présents | Rendu vérifié |
| Décès | 1 page A4 portrait | Défunt, déclarant et dates présents | Rendu vérifié |
| Avis de mention marginale | 1 page A4 portrait | Acte lié, personne, date et contenu de la mention présents | Rendu vérifié |
| Quittance — versement 1 | 1 page, 80 × 130 mm configuré | Numéro, payeur, transaction, montant encaissé et montant en lettres visibles | Rendu vérifié |
| Quittance — versement 2 | 1 page, 80 × 130 mm configuré | Deuxième numéro et second encaissement distincts; montant cohérent | Rendu vérifié |

Les quittances de démonstration présentent notamment un montant total de
`2 000,00 Ar`, un versement de `1 000,00 Ar` et le libellé français
« mille Ariary ». La répétition du rendu ne crée pas de nouveau paiement ni de
nouveau numéro de quittance.

Les fichiers PDF, les captures PNG et les journaux de validation sont conservés
dans les artefacts de session. Les journaux sont
`/tmp/etat_civil_pdf_visual_final_20261109.log` (ciblé) et
`/tmp/etat_civil_pdf_fullsuite_final2_20261109.log` (suite complète finale).

## Configuration et limites de conformité

Chaque centre peut renseigner son emblème, celui de sa région et la référence
légale confirmée par la commune. Ces informations restent vides tant qu’elles
ne sont pas validées; l’en-tête national fourni dans les références est utilisé
comme ressource graphique statique.

Le format 80 × 130 mm de la quittance est une proposition technique basée sur
la photographie, pas une certification d’imprimante. Vérifier le format réel
du rouleau et les marges non imprimables sur l’imprimante cible avant
déploiement. Les formulations malgaches des gabarits doivent aussi être
approuvées par l’autorité d’état civil locale avant usage officiel.

La vérification précédente a permis d'inspecter les rendus et la pagination,
mais ne certifie pas la conformité administrative ni l'impression physique.
Le format réel du rouleau, les marges non imprimables et la qualité sur
l'imprimante cible restent à confirmer par la commune. La photo ne permet pas
de mesurer le reçu original; la dimension thermique retenue reste donc
provisoire. Les formulations malgaches doivent aussi être approuvées par
l'autorité d'état civil locale avant usage officiel.

## Reconstruction de l'acte de naissance — 11 novembre 2026

La structure du modèle ODT est reprise dans un template dédié : référence
légale, emblème national, emblèmes du centre et de la région, colonne latérale,
narration, zone de signature et espace QR. Le papier naissance est un A4
portrait indépendant avec des marges de 20 mm; les autres rapports ne sont pas
modifiés par ce réglage. Les logos de référence sont utilisés uniquement comme
fixtures de test; en production, le rapport prend les emblèmes configurés sur
le centre.

Les données sont liées aux champs ORM et les champs facultatifs absents sont
omis. Le rendu officiel est refusé avant validation ou rectification afin de
ne pas imprimer un brouillon sans avertissement. La séquence, l'acte, les
mentions et les paiements ne sont pas modifiés par l'impression.

| Vérification | Résultat |
|---|---|
| Syntaxe XML du fichier QWeb | Réussie |
| Syntaxe Python des fichiers concernés | Réussie avec l'analyseur Python local |
| Diagnostics Pylance | Non disponibles : serveur MCP en échec d'initialisation |
| Tests Odoo ciblés | Non exécutés : échec du chargement du registre avant le démarrage des tests |
| PDF Odoo et comparaison visuelle de cette nouvelle version | Non générés |

Le lancement ciblé a utilisé uniquement la base de test
`etat_civil_odoo17_mga_generic_test_20261108` et s'est terminé avec le code 255.
Le chargement du module natif `web` a échoué parce que son import vient de
`/usr/lib/python3/dist-packages/odoo/addons/web`, alors que
`odoo.tools.translate` vient du checkout local; l'exception est
`ImportError: cannot import name 'LazyTranslate'`. Aucun test n'a donc été
comptabilisé comme réussi ou échoué. Les journaux du lancement sont conservés
dans `logs/odoo17.log` et dans les artefacts de session; aucun service Odoo
n'a été redémarré et aucune base active n'a été utilisée.

Avant d'approuver la mise en page ou de commencer le mariage, il reste à
exécuter la suite dans un environnement Odoo 17 cohérent, produire le PDF,
vérifier le nombre de pages et inspecter la comparaison avec l'ODT converti.

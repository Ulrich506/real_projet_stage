# État civil — Module principal Odoo 17

Ce module est le socle métier de l’application. Il dépend des modules Odoo
`base`, `mail` et `web`; les modules de facturation, POS et connexion par
adresse e-mail restent des extensions séparées.

Il gère les actes de naissance, mariage et décès, les individus, centres,
registres, pièces justificatives, mentions marginales, guichet, imports/exports,
rapports PDF et rôles métier. Les transitions d’état et contrôles d’accès sont
effectués côté serveur.

## Rôles métier

- **Agent** : gère les citoyens et les actes de ses centres, prépare les
  dossiers, reçoit les pièces, traite les demandes de copies et transmet les
  actes à un officier compétent.
- **Officier** : consulte uniquement les actes qui lui sont affectés, vérifie
  les pièces, valide ou retourne/refuse les dossiers. Il ne modifie pas les
  données personnelles et ne crée pas de mentions marginales.
- **Administrateur d’état civil** : gère les données et configurations de tous
  les centres, les utilisateurs et les rôles, les décisions administratives,
  ainsi que les imports et exports. Ce rôle n’exige ni le groupe Odoo
  `base.group_system` ni le rôle Officier.
- **Régisseur** : le module `etat_civil_account` lui donne l’accès aux demandes
  de copies, paiements et quittances de ses centres; `etat_civil_pos` fournit
  l’accès POS. Il ne reçoit pas pour autant les droits généraux de comptabilité.

## Importation, exportation et langues

L’import et l’export sont réservés au groupe Administrateur d’état civil et
contrôlés côté serveur. L’export propose XLSX par défaut, CSV, ODS, PDF, JSON et
XML. Les filtres d’âge, de sexe, de statut vital et de situation matrimoniale
sont distincts; la sélection peut porter sur tous les citoyens filtrés ou sur
des personnes choisies manuellement. Les champs exportables sont sélectionnables
et l’export peut être libellé en français ou en malagasy. Les deux présentations
PDF disponibles sont une liste tabulaire et une fiche par personne.

Chaque export enregistre dans le journal son auteur, sa date, son format, sa
langue, les critères et les champs. L’assistant d’import accepte CSV, XLSX, XLS,
JSON, XML, ODS et ZIP (les formats bureautiques nécessitent leurs bibliothèques
Python respectives). Il fournit un modèle CSV, le mappage de colonnes, la
prévisualisation et la correction en ligne. Les lignes avec erreurs bloquent
toute écriture jusqu’à leur correction et leur revalidation. Les doublons sont
signalés et traités selon la stratégie choisie.

Les traductions des écrans d’import/export sont fournies dans `i18n/fr.po` et
`i18n/mg.po`; le Malagasy utilise le code Odoo `mg_MG`. Pour tester les écrans
en malagasy, activer cette langue dans Odoo puis choisir la langue du fichier
dans l’assistant d’export.

Les rapports de naissance, mariage, décès et mention marginale ont des actions
et gabarits séparés. Les extraits A4 utilisent les données ORM et laissent les
références légales et emblèmes locaux configurables au niveau du centre. Un
brouillon est explicitement marqué non validé; l’impression ne crée ni acte ni
numéro. La quittance est associée à un encaissement rapproché et sa
réimpression ne crée pas de nouvelle transaction.

L’application mobile mentionnée dans les anciennes notes est un client
externe; son code source n’est pas présent dans ce dépôt. Les API restent
soumises aux contrôles d’accès Odoo.

Utilisez une base de développement isolée et suivez le guide racine
[README.md](../../README.md). Les migrations versionnées de ce module sont
conservées dans `migrations/`. Les noms et l’organisation Odoo
`tests/test_*.py` sont requis pour la découverte automatique des tests.

Voir le [rapport de refonte et de validation des PDF](../../documentation/maintenance/pdf-report-redesign.md)
pour les correspondances ORM, règles d'impression et limites restantes.

## Journal central d'audit

Le modèle `etat.civil.audit.log` centralise les créations, modifications et
suppression des individus, actes, centres, registres, pièces, mentions et
demandes au guichet, ainsi que les changements de rôles. Il trace également
les connexions/déconnexions, transitions d'actes, impressions, téléchargements
de rapports et de pièces, échanges import/export, événements de paiement,
avoirs comptabilisés et délivrances de copies. Les opérations financières
conservent aussi leur journal métier existant.

L'interface de consultation et l'export Odoo du journal sont limités à
l'Administrateur d'état civil. Les utilisateurs ne disposent pas des droits
ORM de création, modification ou suppression; les événements sont ajoutés
uniquement par le service interne. Les événements ne copient pas les champs
personnels : les écritures conservent les noms des champs modifiés et seules
les transitions d'état et métadonnées financières autorisées peuvent contenir
des anciennes/nouvelles valeurs. Les identifiants de session sont hachés.

Les consultations ordinaires ne sont pas journalisées. Le type
« consultation sensible » est disponible pour les futurs flux qui auront une
politique validée de confidentialité, de contrôle d'accès et de conservation.
Aucune durée de conservation légale n'étant configurée, elle doit être définie
avant d'activer une journalisation systématique des lectures. Les adresses IP
proviennent de la connexion directe vue par Odoo; derrière un proxy, il faut
configurer et documenter la confiance réseau avant de les interpréter comme
l'adresse du poste utilisateur. L'identifiant `X-Request-ID` est une valeur
de corrélation fournie par le client, pas une preuve d'identité.

Cette protection est append-only au niveau applicatif, mais ne résiste pas à
un administrateur PostgreSQL ou au propriétaire du serveur. Pour une preuve
externe, déployer séparément une réplication/export périodique vers un
collecteur SIEM ou stockage WORM, avec compte d'écriture dédié, chiffrement,
contrôle d'accès et politique de conservation/suppression documentée. Aucun
export externe automatique n'est activé par ce module. Les erreurs qui font
annuler la transaction Odoo ne peuvent pas laisser de trace dans cette même
transaction; les événements persistés décrivent donc les opérations validées,
pas un journal complet des tentatives échouées. Le remboursement tracé ici est
l'avoir client comptabilisé; tout flux de remboursement de trésorerie doit
également être relié au journal financier.

# Validation MedSemantic

Ce contrôle correspond aux exigences transmises dans le message de Mme Maha
Mallek et au sujet fourni. La grille de notation finale n'était pas jointe.

| Exigence | Preuve dans le projet |
| --- | --- |
| Thématique et ontologie | Pharmaceutique et santé ; `ontology/MedSemantic.owl`, 532 triplets. |
| Classes et individus | Dix classes racines ; 54 déclarations `owl:Class`, 34 individus nommés. |
| ObjectProperty et DataProperty | 27 propriétés d'objet et 19 propriétés de données. |
| Axiomes | Classes disjointes, inverses, équivalences, intersections, union et quatre restrictions OWL. |
| Front et back | React et FastAPI ; les dix collections et leurs profils utilisent Fuseki via le backend. |
| SPARQL CRUD, recherche et filtres | CRUD patients, conditions, médicaments, maladies et symptômes ; filtres, agrégations, OPTIONAL, parcours de sous-classes et FILTER NOT EXISTS. Études, résultats, molécules et module Oussema : consultation et recherche. |
| Communication front/back | Cartes, profils, relations et graphe ; contrôles réseau réels et tests d'interface. |
| NLP/TALN vers SPARQL | spaCy, modèle local `fr_core_news_sm`, lemmatisation, `PhraseMatcher`, reconnaissance d'intentions et patrons SPARQL paramétrés. Aucune API de LLM. |

## Démonstration au professeur

1. Ouvrir l'ontologie dans Protégé. Montrer une ObjectProperty avec son inverse,
   une DataProperty, un individu et une équivalence/restriction OWL.
2. Ouvrir les collections : 4 médicaments, 6 molécules, 4 maladies, 3 symptômes,
   3 effets secondaires, 3 contre-indications, 3 patients, 4 conditions,
   2 études et 2 résultats dans le jeu de données fourni.
3. Dans les effets secondaires, choisir `EffetDigestif`, puis fréquence `rare` :
   aucun résultat. Effacer les filtres : les trois effets reviennent.
   Ouvrir `TroublesGastriques` : symptôme `Nausee`, médicament `Glucophage`.
   Ouvrir son graphe et suivre les liens.
4. Créer un patient de démonstration dans l'interface, le modifier, le retrouver
   avec les filtres, puis le supprimer. Expliquer les requêtes INSERT et DELETE.
5. Dans la recherche, essayer les questions ci-dessous et ouvrir **View SPARQL
   query**. Expliquer les étapes NLP avant l'exécution sur Fuseki.

- `Quel est le dosage du Doliprane ?`
- `Composition du Doliprane`
- `Quels patients ont plus de 65 ans ?`
- `Quelles conditions sont physiologiques ?`
- `Quels effets secondaires du Glucophage ?`
- `Quelles contre-indications pour Advil ?`

Mentionner explicitement **spaCy**, **fr_core_news_sm**, **PhraseMatcher** et
**patrons SPARQL** dans la présentation. Le traducteur couvre des intentions
définies ; il ne comprend pas toutes les questions possibles.

Les axiomes OWL existent dans le fichier. Le backend utilise des parcours
SPARQL et des calculs applicatifs pour les catégories d'âge ; il ne faut pas
présenter ces calculs comme l'exécution d'un raisonneur OWL complet.
L'absence d'une contre-indication enregistrée ne prouve pas qu'un médicament
est sûr. Les données du projet sont des exemples pédagogiques.

## Vérifications reproductibles

Depuis la racine, Fuseki et FastAPI déjà lancés :

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend/tests -q
npm --prefix frontend test
npm --prefix frontend run build
.\backend\.venv\Scripts\python.exe backend/scripts/verify_project.py
.\backend\.venv\Scripts\python.exe backend/scripts/verify_clinical_crud.py
```

`verify_project.py` est en lecture seule et compare les dix collections et
tous leurs profils à l'ontologie. Il vérifie aussi les filtres et six questions
NLP dont le SPARQL retourné est réellement exécutable. La vérification CRUD
utilise un dataset temporaire supprimé à la fin et confirme que le dataset de
l'équipe n'a pas changé.

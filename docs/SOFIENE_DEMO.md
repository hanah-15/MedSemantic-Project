# Démonstration du module Sofiene

Patient et ConditionMedicale : ontologie → SPARQL → Fuseki → FastAPI → React.

## Parcours de démonstration

1. Démarrer Fuseki, FastAPI et React. Ouvrir les collections Patients et Medical conditions.
2. Ajouter une condition `Condition_Demo`, de type `Allergie`, avec une sévérité `modérée`.
3. Ajouter `Patient_Demo`, âge 17, sexe M. Cocher la condition créée et le médicament Glucophage. Ouvrir son profil pour montrer les liens.
4. Modifier son âge à 65 : sa catégorie devient PersonneAgee. Le filtre Minimum age = 65 doit le retrouver. La catégorie d'âge est calculée en Python, sans moteur d'inférence OWL.
5. Dans la recherche, demander « Quels médicaments prend Demo ? », puis « Quelles conditions a Demo ? ». Les réponses viennent des liens explicites enregistrés.
6. Demander « Quels patients ont au moins 65 ans ? », puis « Quelles conditions sont physiologiques ? ».
7. Dans Swagger (`http://127.0.0.1:8000/docs`), exécuter `/api/recherche/` avec la première question. Montrer les champs `analysis`, `sparql`, `records` et `tools` pour expliquer la traduction.
8. Supprimer Condition_Demo. Le patient reste présent et son lien vers cette condition disparaît. Supprimer ensuite Patient_Demo pour retrouver les données initiales.

## Outils à mentionner explicitement

- OWL/RDF pour les classes, propriétés, individus et axiomes.
- Apache Jena Fuseki pour stocker les triples et exécuter SPARQL SELECT/INSERT/DELETE.
- FastAPI pour les routes et la validation des données.
- React et TypeScript pour les interfaces.
- spaCy, le modèle français `fr_core_news_sm`, la lemmatisation et PhraseMatcher pour l'analyse linguistique. Les entités sont reconnues depuis les identifiants actuels de l'ontologie.
- Des modèles de requêtes SPARQL et l'analyse des comparateurs numériques pour produire des requêtes exécutables. Aucune API LLM externe.

Une relation absente signifie qu'aucun lien n'est enregistré, sans prouver l'absence d'une condition ou d'une maladie.

## Vérification automatisée

Depuis la racine du dépôt, avec Fuseki disponible :

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend/tests -q
.\backend\.venv\Scripts\python.exe backend/scripts/verify_clinical_crud.py
npm --prefix frontend test
npm --prefix frontend run build
```

Le script de vérification réelle utilise un dataset mémoire temporaire et vérifie que le dataset de l'équipe est inchangé. Les tests ordinaires utilisent des graphes RDF isolés.

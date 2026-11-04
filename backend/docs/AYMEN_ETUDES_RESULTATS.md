# Module Études Cliniques & Résultats Cliniques (Aymen)

Documentation technique des requêtes SPARQL et des routes FastAPI pour les classes **`EtudeClinique`** (`EssaiClinique`, `EtudeObservationnelle`) et **`ResultatClinique`** (`Efficacite`, `Securite`, `Tolerance`).

---

## 1. Architecture & Fichiers

| Fichier | Rôle |
| :--- | :--- |
| `backend/app/fuseki_client.py` | Client HTTP partagé vers Apache Jena Fuseki (`FUSEKI_URL`), timeout et gestion des erreurs `502`/`503`. |
| `backend/sparql_queries/queries_etude.py` | 11 fonctions de génération de requêtes SPARQL paramétrées et sécurisées pour `EtudeClinique`. |
| `backend/sparql_queries/queries_resultat.py` | 5 fonctions de génération de requêtes SPARQL paramétrées et sécurisées pour `ResultatClinique`. |
| `backend/app/routes/etudes.py` | Routeur FastAPI `/etudes` avec validation et modèles Pydantic. |
| `backend/app/routes/resultats.py` | Routeur FastAPI `/resultats` avec validation et modèles Pydantic. |
| `backend/tests/test_etudes_resultats.py` | Suite de tests `pytest` (mocks Fuseki + validation syntaxique SPARQL 1.1 `rdflib`). |

---

## 2. Choix Techniques (Web Sémantique)

1. **Absence de raisonneur dans Fuseki (TDB2 simple)** :
   - Utilisation systématique de `rdfs:subClassOf*` pour parcourir la hiérarchie de classes sans inférence implicite.
   - Exemple : rechercher les résultats de type `Securite` (`?sousClasse rdfs:subClassOf* :Securite`) remonte automatiquement les instances de `Tolerance` (`Tolerance ⊆ Securite`).
2. **Hypothèse du Monde Ouvert (OWA)** :
   - Les propriétés optionnelles (`:phaseEssai`, `:porteSurMaladie`, `:aPourResultat`) sont entourées de blocs `OPTIONAL` afin que `Etude_Paracetamol_Obs` (étude observationnelle sans phase, sans maladie et sans résultat) ne soit jamais exclue des listes.
   - La route `/etudes/sans-resultat` utilise `FILTER NOT EXISTS { ?etude :aPourResultat ?r . }`.
3. **Sécurité anti-injection SPARQL** :
   - Tous les identifiants sont validés par l'expression régulière stricte `^[A-Za-z0-9_]+$` (lève `HTTP 422` en cas de caractère invalide).
   - Les paramètres numériques (`phase`, `annee_min`, `annee_max`, `n`) sont typés `int` et bornés via FastAPI.

---

## 3. Routes FastAPI disponibles

### A. Études Cliniques (`/etudes`)

| Méthode | Route | Description |
| :--- | :--- | :--- |
| `GET` | `/etudes/` | Liste toutes les études cliniques (`EssaiClinique` et `EtudeObservationnelle`) avec `OPTIONAL`. |
| `GET` | `/etudes/{etude_id}` | Détail complet d'une étude avec la liste de ses résultats cliniques (`404` si absente). |
| `GET` | `/etudes/type/{type_etude}` | Filtre par sous-classe (`EssaiClinique` ou `EtudeObservationnelle`). |
| `GET` | `/etudes/medicament/{medicament_id}` | Études testant un médicament donné via `:testeMedicament` (ex: `Glucophage`, `Doliprane`). |
| `GET` | `/etudes/maladie/{maladie_id}` | Études portant sur une maladie donnée via `:porteSurMaladie` (ex: `DiabeteType2`). |
| `GET` | `/etudes/phase/{phase}` | Essais cliniques d'une phase donnée (`1` à `4`). |
| `GET` | `/etudes/sans-resultat` | Études n'ayant aucun résultat associé (`FILTER NOT EXISTS`). |
| `GET` | `/etudes/stats` | Nombre d'études et moyenne des participants par type (`COUNT`, `AVG`, `GROUP BY`). |
| `GET` | `/etudes/annee/recherche` | Filtre par plage d'années (`?annee_min=2023&annee_max=2024`). |
| `GET` | `/etudes/participants/minimum` | Études ayant au moins `n` participants (`?n=500`). |
| `GET` | `/etudes/comparatives/liste` | Études comparatives uniquement (`:estComparative true`). |

### B. Résultats Cliniques (`/resultats`)

| Méthode | Route | Description |
| :--- | :--- | :--- |
| `GET` | `/resultats/` | Liste tous les résultats cliniques avec leur type précis, valeur, unité, étude et médicament. |
| `GET` | `/resultats/{resultat_id}` | Détail d'un résultat clinique avec son étude et le médicament testé (`404` si absent). |
| `GET` | `/resultats/type/{type_resultat}` | Filtre par type : `efficacite`, `securite` (inclut `Tolerance` via `rdfs:subClassOf*`) ou `tolerance`. |
| `GET` | `/resultats/medicament/{medicament_id}` | Résultats associés à un médicament en traversant l'étude clinique. |
| `GET` | `/resultats/stats` | Nombre de résultats par sous-classe (`COUNT`, `GROUP BY`). |

---

## 4. Exemples de Réponses JSON

### `GET /etudes/Essai_Metformine_2024`
```json
{
  "iri": "http://www.semanticweb.org/medsemantic#Essai_Metformine_2024",
  "id": "Essai_Metformine_2024",
  "type_etude": "EssaiClinique",
  "medicament_id": "Glucophage",
  "medicament_iri": "http://www.semanticweb.org/medsemantic#Glucophage",
  "maladie_id": "DiabeteType2",
  "maladie_iri": "http://www.semanticweb.org/medsemantic#DiabeteType2",
  "phase": 3,
  "annee": 2024,
  "participants": 500,
  "comparative": true,
  "resultats": [
    {
      "iri": "http://www.semanticweb.org/medsemantic#Res_Efficacite_Glucophage",
      "id": "Res_Efficacite_Glucophage",
      "type_resultat": "Efficacite",
      "valeur": 1.2,
      "unite": "% HbA1c (baisse)"
    },
    {
      "iri": "http://www.semanticweb.org/medsemantic#Res_Tolerance_Glucophage",
      "id": "Res_Tolerance_Glucophage",
      "type_resultat": "Tolerance",
      "valeur": 85.0,
      "unite": "% patients sans effet gênant"
    }
  ]
}
```

### `GET /etudes/sans-resultat`
```json
[
  {
    "iri": "http://www.semanticweb.org/medsemantic#Etude_Paracetamol_Obs",
    "id": "Etude_Paracetamol_Obs",
    "type_etude": "EtudeObservationnelle",
    "medicament_id": "Doliprane",
    "medicament_iri": "http://www.semanticweb.org/medsemantic#Doliprane",
    "maladie_id": null,
    "maladie_iri": null,
    "phase": null,
    "annee": 2023,
    "participants": 1200,
    "comparative": false
  }
]
```

### `GET /resultats/type/securite`
```json
[
  {
    "iri": "http://www.semanticweb.org/medsemantic#Res_Tolerance_Glucophage",
    "id": "Res_Tolerance_Glucophage",
    "type_resultat": "Tolerance",
    "valeur": 85.0,
    "unite": "% patients sans effet gênant",
    "etude_id": "Essai_Metformine_2024",
    "etude_iri": "http://www.semanticweb.org/medsemantic#Essai_Metformine_2024",
    "medicament_id": "Glucophage",
    "medicament_iri": "http://www.semanticweb.org/medsemantic#Glucophage"
  }
]
```


# Module Effets Secondaires & Contre-Indications (Oussema)

Documentation technique des requêtes SPARQL et des routes FastAPI pour les classes **`EffetSecondaire`** (`EffetDigestif`, `EffetNeurologique`, `EffetCardiovasculaire`, `EffetAllergique`) et **`ContreIndication`** (`ContreIndicationAbsolue`, `ContreIndicationRelative`).

---

## 1. Architecture & Fichiers Créés

| Fichier | Rôle |
| :--- | :--- |
| `backend/sparql_queries/queries_effet_secondaire.py` | 8 fonctions SPARQL sécurisées avec parcours de sous-classes (`rdfs:subClassOf*`) et filtres. |
| `backend/sparql_queries/queries_contre_indication.py` | 7 fonctions SPARQL sécurisées incluant la vérification sémantique patient-médicament. |
| `backend/app/models/effet_secondaire.py` | Modèles Pydantic pour la sérialisation des effets secondaires (`Resume`, `Detail`, `Stats`). |
| `backend/app/models/contre_indication.py` | Modèles Pydantic pour la sérialisation des contre-indications (`Resume`, `Detail`, `Alerte`, `Stats`). |
| `backend/app/routes/effets_secondaires.py` | Routeur FastAPI `/effets-secondaires` (et `/api/effets-secondaires`). |
| `backend/app/routes/contre_indications.py` | Routeur FastAPI `/contre-indications` (et `/api/contre-indications`). |
| `backend/tests/test_effets_contre_indications.py` | 20 tests unitaires et d'intégration validant la syntaxe SPARQL 1.1, la sécurité anti-injection et les endpoints. |

---

## 2. Principes du Web Sémantique Appliqués

1. **Parcours Hiérarchique sans Raisonneur (`rdfs:subClassOf*`)** :
   - Permet d'inclure toutes les sous-classes sans dépendre d'un raisonneur lourd dans Jena Fuseki.
   - Exemple : la recherche de tous les effets secondaires remonte automatiquement `EffetDigestif`, `EffetCardiovasculaire`, `EffetAllergique`.
2. **Propriétés Inverses & Modélisation Ouverte (OWA)** :
   - Détection des médicaments liés à la fois via `?medicament :provoque ?effet` et `?effet :estProvoquePar ?medicament`.
   - Détection des contre-indications via `?medicament :aPourContreIndication ?ci` et `?ci :estContreIndicationDe ?medicament`.
3. **Sécurité Anti-Injection SPARQL** :
   - Validation stricte des identifiants via regex `^[A-Za-z0-9_]+$`.
   - Tout caractère suspect lève immédiatement une exception HTTP `422 Unprocessable Entity`.
4. **Vérification Croisée Patient / Médicament** :
   - Requête sémantique reliant : `Patient -> Condition/Maladie <- ContreIndication <- Médicament`.

---

## 3. Endpoints FastAPI

### A. Effets Secondaires (`/effets-secondaires` ou `/api/effets-secondaires`)

| Méthode | Route | Description |
| :--- | :--- | :--- |
| `GET` | `/effets-secondaires/` | Liste tous les effets secondaires (filtres optionnels : `?type_effet=`, `?gravite=`, `?frequence=`). |
| `GET` | `/effets-secondaires/{effet_id}` | Détail complet d'un effet secondaire (gravité, fréquence, symptômes, médicaments associés). |
| `GET` | `/effets-secondaires/medicament/{medicament_id}` | Effets secondaires provoqués par un médicament (ex: `Glucophage`, `Amlor`). |
| `GET` | `/effets-secondaires/symptome/{symptome_id}` | Effets secondaires se manifestant par un symptôme donné (ex: `Nausee`). |
| `GET` | `/effets-secondaires/type/{type_effet}` | Effets filtrés par sous-classe (ex: `EffetDigestif`, `cardiovasculaire`, `allergique`). |
| `GET` | `/effets-secondaires/gravite/{gravite}` | Effets filtrés par gravité (ex: `légère`, `modérée`, `sévère`). |
| `GET` | `/effets-secondaires/frequence/{frequence}` | Effets filtrés par fréquence (ex: `fréquent`, `rare`). |
| `GET` | `/effets-secondaires/stats` | Répartition statistique des effets par sous-classe. |

### B. Contre-indications (`/contre-indications` ou `/api/contre-indications`)

| Méthode | Route | Description |
| :--- | :--- | :--- |
| `GET` | `/contre-indications/` | Liste toutes les contre-indications (filtre optionnel `?type_ci=absolue`). |
| `GET` | `/contre-indications/{ci_id}` | Détail complet d'une contre-indication (type, description, conditions et médicaments liés). |
| `GET` | `/contre-indications/medicament/{medicament_id}` | Contre-indications associées à un médicament (ex: `Advil`, `Glucophage`, `Doliprane`). |
| `GET` | `/contre-indications/condition/{condition_id}` | Contre-indications pour une condition ou maladie (ex: `Grossesse_T3`, `InsufRenaleSevere`). |
| `GET` | `/contre-indications/type/{type_ci}` | Contre-indications filtrées par type (`absolue` ou `relative`). |
| `GET` | `/contre-indications/verifier/{patient_id}/{medicament_id}` | **Vérification de sécurité** : croise les conditions du patient et les contre-indications du médicament. |
| `GET` | `/contre-indications/stats` | Statistiques du nombre de contre-indications absolues vs relatives. |

---

## 4. Démarrage et Vérification

1. **Activer le venv** :
   ```powershell
   .\backend\venv\Scripts\activate
   ```
2. **Lancer le serveur FastAPI** :
   ```powershell
   cd backend
   python main.py
   ```
3. **Tester sur Swagger UI** :
   Ouvrez `http://127.0.0.1:8000/docs` dans votre navigateur.
4. **Lancer les tests** :
   ```powershell
   python -m pytest tests -q
   ```

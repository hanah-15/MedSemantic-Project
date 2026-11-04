# Patient & ConditionMedicale — Sofiene's backend

This branch contains read-only SPARQL routes for the two assigned ontology classes. **They require Apache Jena Fuseki 5.0.0 and Java 17** on the developer's PC. Load the supplied `MedSemantic.owl` into a TDB2 dataset named `medsemantic` before calling the API.

## Start in Windows CMD

```cmd
cd backend
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
python main.py
```

Use http://127.0.0.1:8000/docs for Swagger. The application also serves `GET /` for health checking.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/patients` | All patients, attributes and explicit outgoing relationships |
| GET | `/api/patients/{id}` | Patient by ontology individual identifier |
| GET | `/api/patients/{id}/conditions` | Only conditions actually linked via `aPourCondition` |
| GET | `/api/conditions` | Medical conditions, including individuals typed as subclasses |
| GET | `/api/conditions/{id}` | Medical condition by ontology identifier |

Response records match React's existing `Entity` type: `id`, `name`, `domain`, `type`, `description`, `properties`, `relations`. The `properties.ageCategory` label is computed in Python from the specification's age bands (under 18, 18–64, 65+) — it does **not** claim that Fuseki has performed OWL reasoning. No `aPourCondition` links exist for the sample patients in the supplied ontology; an empty array is expected and is not a bug.

**Testing:** `python -m pytest tests -q` (install `pytest` and `httpx` if not present). The unit/integration tests use a real parse of `MedSemantic.owl` when it is provided at the project root or via `MEDSEMANTIC_OWL_PATH`; no live Fuseki instance is necessary for those tests.

**Safety & scope:** All data is fictional coursework ontology data. Do not expose real patient data without appropriate authentication, access controls and privacy protections. This module only reads semantic records; it does not diagnose, prescribe or infer medication safety.

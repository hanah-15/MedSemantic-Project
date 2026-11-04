# Patient & ConditionMedicale — Sofiene's backend

This branch contains read-only SPARQL routes for the two assigned ontology classes. **They require Apache Jena Fuseki 5.0.0 and Java 17** on the developer's PC. Load the supplied `MedSemantic.owl` into a TDB2 dataset named `medsemantic` before calling the API.

## Start with an existing installation in Windows CMD

```cmd
cd backend
.venv\Scripts\activate.bat
if not exist .env copy .env.example .env
python main.py
```

Use http://127.0.0.1:8000/docs for Swagger. The application also serves `GET /` for health checking.

Only if `.venv` does not exist, create it with `py -3.12 -m venv .venv` and install `requirements-dev.txt` using that environment. Do not recreate an existing environment. `GET /` checks that FastAPI is running; the clinical endpoints check Fuseki by executing SELECT queries.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/patients` | All patients, attributes and explicit outgoing relationships |
| GET | `/api/patients/{id}` | Patient by ontology individual identifier |
| GET | `/api/patients/{id}/conditions` | Only conditions actually linked via `aPourCondition` |
| GET | `/api/conditions` | Medical conditions, including individuals typed as subclasses |
| GET | `/api/conditions/{id}` | Medical condition by ontology identifier |

Response records match React's existing `Entity` type: `id`, `name`, `domain`, `type`, `description`, `properties`, `relations`. The `properties.ageCategory` label is computed in Python from the specification's age bands (under 18, 18–64, 65+) — it does **not** claim that Fuseki has performed OWL reasoning. No `aPourCondition` links exist for the sample patients in the supplied ontology; an empty array is expected and is not a bug.

Condition records also include `incomingRelations`: a list of `{predicate, source, sourceDomain}` objects. These come only from explicit `Patient → aPourCondition → ConditionMedicale` or `ContreIndication → concerneCondition → ConditionMedicale` triples. The query follows asserted `rdfs:subClassOf` paths to include subclass instances. It does not infer inverse properties or new patient conditions. Incoming links for Patient are outside the current query scope.

## Automated tests and live verification

Run `python -m pytest tests -q`. By default these tests evaluate SPARQL on the small committed Turtle fixture. To use the supplied official ontology instead, set `MEDSEMANTIC_OWL_PATH` to its absolute path before running pytest. These tests do not require Fuseki. Some installed Starlette versions emit a TestClient/httpx deprecation warning.

With Fuseki and FastAPI running, from `backend` run:

```cmd
python scripts\verify_live.py --ontology "C:\path\to\MedSemantic.owl"
```

The script reads the Fuseki default graph and compares it with the supplied ontology, accounting for RDF 1.1 string-literal equivalence and blank-node identifiers. It then compares API collections and every detail response with direct SPARQL results from that file, verifies patient condition links, checks 404/422 responses, and checks Swagger and Vite CORS. Optional `--fuseki` and `--api` flags select other local servers. It never creates a dataset or uploads/modifies triples. A mismatch is reported for inspection.

Verified on 2026-11-04 with Java 17 and Fuseki 5.0.0: 532 triples, 3 patients, 4 conditions, all detail routes, explicit links, identifier errors and CORS. A separate real failed connection to an unavailable local Fuseki endpoint returned HTTP 503. Both the fixture and official-ontology test runs passed 22 tests.

## Frontend integration

From the repository root, open another terminal:

```cmd
cd frontend
npm run dev
```

Use the URL Vite prints. On the verified workstation `5173` was occupied by an older template and this checkout ran at `http://localhost:5174`. Both ports are allowed by the API's local CORS configuration. The frontend defaults to `http://127.0.0.1:8000`; `VITE_API_BASE_URL` can override that base URL.

Patient and condition collections, profiles, search results and the record graph use API data. Filters expose computed patient age categories and asserted condition groups. Condition profiles show type, group, explicit severity when available, and incoming links. Clinical relationship navigation includes the target domain so records absent from the preview catalog can still load. The graph page also preserves the shared specification-level class map.

Loading and successful empty results do not show preview records. A live 404 stays missing. Connection failures/503 responses offer labeled preview records where available and a retry control; other API errors are displayed without substituting previews. Requests have a 15-second timeout. Search labels each live/preview result. Related profiles in teammates' collections remain labeled previews, even when a clinical relationship itself is live.

From `frontend`, run `npm test` for the clinical UI regression suite and `npm run build` for TypeScript and the production build. Tests cover loading, empty datasets, filters, missing records, service failures/retry, source labels, live incoming links, graph provenance, connection counts and stale requests.

**Safety & scope:** All data is fictional coursework ontology data. Do not expose real patient data without appropriate authentication, access controls and privacy protections. This module only reads semantic records; it does not diagnose, prescribe or infer medication safety.

# Patient & ConditionMedicale — Sofiene's backend

This branch implements SPARQL CRUD, filtering, relationship editing and French NLP for Patient and ConditionMedicale. **They require Apache Jena Fuseki 5.0.0 and Java 17** on the developer's PC. Load the official `ontology/MedSemantic.owl` from the repository root into a TDB2 dataset named `medsemantic` before calling the API.

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
| POST | `/api/patients`, `/api/conditions` | Create a clinical individual |
| PUT | `/api/patients/{id}`, `/api/conditions/{id}` | Replace the editable clinical attributes and links |
| DELETE | `/api/patients/{id}`, `/api/conditions/{id}` | Delete the individual and links to it |
| GET | `/api/patients/options` | Actual diseases, conditions, symptoms and medications available for linking |
| GET | `/api/conditions/types` | Condition classes from the asserted ontology hierarchy |

Response records match React's existing `Entity` type: `id`, `name`, `domain`, `type`, `description`, `properties`, `relations`. The `properties.ageCategory` label is computed in Python from the specification's age bands (under 18, 18–64, 65+) — it does **not** claim that Fuseki has performed OWL reasoning. No `aPourCondition` links exist for the sample patients in the supplied ontology; an empty array is expected and is not a bug.

Condition records also include `incomingRelations`: a list of `{predicate, source, sourceDomain}` objects. These come only from explicit `Patient → aPourCondition → ConditionMedicale` or `ContreIndication → concerneCondition → ConditionMedicale` triples. The query follows asserted `rdfs:subClassOf` paths to include subclass instances. It does not infer inverse properties or new patient conditions. Incoming links for Patient are outside the current query scope.

## Automated tests and live verification

Run `python -m pytest tests -q`. By default these tests evaluate SPARQL on the small committed Turtle fixture. To use the supplied official ontology instead, set `MEDSEMANTIC_OWL_PATH` to its absolute path before running pytest. These tests do not require Fuseki. Some installed Starlette versions emit a TestClient/httpx deprecation warning.

With Fuseki and FastAPI running, from `backend` run:

```cmd
python scripts\verify_live.py --ontology "C:\path\to\MedSemantic.owl"
```

The script reads the Fuseki default graph and compares it with the supplied ontology, accounting for RDF 1.1 string-literal equivalence and blank-node identifiers. It then compares API collections and every detail response with direct SPARQL results from that file, verifies patient condition links, checks 404/422 responses, and checks Swagger and Vite CORS. Optional `--fuseki` and `--api` flags select other local servers. It never creates a dataset or uploads/modifies triples. A mismatch is reported for inspection.

Verified on 2026-11-04 with Java 17 and Fuseki 5.0.0: 532 triples, 3 patients, 4 conditions, all detail routes, explicit links, identifier errors and CORS. A separate real failed connection to an unavailable local Fuseki endpoint returned HTTP 503. The latest clinical extension was verified on 2026-11-05: 75 backend tests passed against both the fixture and the official ontology. The frontend suite contains 28 passing tests.

## Frontend integration

From the repository root, open another terminal:

```cmd
cd frontend
npm run dev
```

Use the URL Vite prints. On the verified workstation `5173` was occupied by an older template and this checkout ran at `http://localhost:5174`. Both ports are allowed by the API's local CORS configuration. The frontend defaults to `http://127.0.0.1:8000`; `VITE_API_BASE_URL` can override that base URL.

Patient and condition collections, profiles, search results and the record graph use API data. Filters expose computed patient age categories and asserted condition groups. Condition profiles show type, group, explicit severity when available, and incoming links. Clinical relationship navigation includes the target domain so records absent from the preview catalog can still load. The graph page also preserves the shared specification-level class map.

Loading and successful empty results do not show preview records. A live 404 stays missing. Connection failures/503 responses offer labeled preview records where available and a retry control; other API errors are displayed without substituting previews. Requests have a 15-second timeout. Sample search results are labeled; successful loads do not display connection badges. Related profiles in teammates' collections remain labeled previews, even when a clinical relationship itself is live.

From `frontend`, run `npm test` for the clinical UI regression suite and `npm run build` for TypeScript and the production build. Tests cover loading, empty datasets, filters, missing records, service failures/retry, source labels, live incoming links, graph provenance, connection counts and stale requests.

**Safety & scope:** All data is fictional coursework ontology data. Do not expose real patient data without appropriate authentication, access controls and privacy protections. This module reads and edits educational ontology individuals; it does not diagnose, prescribe or infer medication safety.

## Hana pharmacology integration

The merged application also registers Hana's medication CRUD and French NLP routes:

| Method | Path | Purpose |
| --- | --- | --- |
| GET, POST | `/api/medicaments/` | List or create medications |
| GET | `/api/medicaments/details/{uri}` | Medication profile and molecule composition |
| GET | `/api/medicaments/{nom_medicament}` | Active ingredients and excipients by commercial name |
| PUT, DELETE | `/api/medicaments/{uri}` | Update or delete a medication |
| GET | `/api/recherche/?q=...` | Answer French composition, dosage and dosage-form questions |

All modules use the same `FUSEKI_URL` dataset. Pharmacology also accepts explicit `FUSEKI_QUERY_URL` and `FUSEKI_UPDATE_URL` overrides. Local Vite CORS supports GET, POST, PUT and DELETE.

Install the merged `requirements.txt` into the existing `.venv` if these dependencies are missing; it includes spaCy and a pinned French language-model wheel. The medication collection preserves Hana's create, edit and delete forms. Medication profiles show live molecule composition and link back to patients with explicit `prend` relationships. The shared search includes live clinical and medication records alongside Hana's NLP answers.

The integrated regression suites contain 75 backend tests and 28 frontend tests. Medication write tests evaluate SPARQL updates on an isolated RDFLib graph and never alter the running Fuseki dataset. The live integration verification script remains read-only.

## Clinical editing and SPARQL filters

Patient writes accept `age` (a non-negative integer), `sexe` and optional identifier lists for `aPourMaladie`, `aPourCondition`, `ressentSymptome` and `prend`. POST additionally requires `id`. PUT replaces the clinical fields and these links while preserving unrelated attributes. Linked individuals must belong to the expected ontology class. Condition writes accept an existing condition `type` and optional `severite`; POST also requires `id`. Clearing severity removes that assertion. Existing identifiers return 409, invalid values or wrong-class links return 422, missing records return 404, and unavailable storage returns 503.

The collection pages provide add/edit/delete forms and actual ontology choices. Editing and deletion are disabled for fallback samples. Deleting an individual also removes incoming links; it does not delete related individuals or schema classes.

Patient GET filters: `q`, `min_age`, `max_age`, `age_category`, `sexe`, `condition_id`. Condition GET filters: `q`, `category`, `condition_type`, `severity`. These become SPARQL FILTERs or graph patterns on Fuseki, rather than relying on browser filtering alone.

Clinical NLP shares Hana's local spaCy French pipeline (`fr_core_news_sm`). It uses lemmatization, a PhraseMatcher built from current patient/class identifiers, numeric comparison parsing, and bounded SPARQL templates. It supports patient medications, diseases, conditions and symptoms; patient age bands/ranges; and physiological/pathological or typed condition queries. New patient names are recognized from the current dataset. Unsupported or negative questions request clarification rather than interpreting missing data as medical absence. No hosted LLM API is used.

Examples: `Quels médicaments prend Karim ?`, `Quels symptômes ressent Sarah ?`, `Quels patients ont au moins 65 ans ?`, `Quelles conditions sont physiologiques ?`. The NLP response includes `records`, the executed `sparql`, analysis and named tools for the professor's API demonstration. Normal pages show records and plain user feedback without infrastructure badges.

## Real Fuseki write verification

With Fuseki running, from the repository root:

```powershell
.\backend\.venv\Scripts\python.exe backend/scripts/verify_clinical_crud.py
```

This creates a uniquely named temporary memory dataset, loads the bundled official ontology into it, verifies clinical CRUD, link maintenance, filters and NLP, then removes that dataset. It reads the team's `medsemantic` graph before and after and verifies it is unchanged. Fuseki administrative access on localhost is needed for this optional check. It does not launch a second backend server.

A short presentation walkthrough is available in `docs/SOFIENE_DEMO.md` from the repository root.

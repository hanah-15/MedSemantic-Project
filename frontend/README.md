# MedSemantic — Shared frontend

A carefully designed medical ontology research interface built with React, TypeScript, Vite and Lucide icons.

## Get started

Requires Node.js 20.19+ or 22.12+.

```powershell
cd frontend
npm install
if (!(Test-Path .env)) { Copy-Item .env.example .env }
npm run dev
```

Open the URL printed by Vite, usually http://localhost:5173. If that port is occupied, Vite may choose http://localhost:5174. Confirm the terminal belongs to this checkout when another template is running.

## Production checks

```powershell
npm run typecheck
npm test
npm run build
```

## Pages and ownership

The shared shell, typography, search, graph explorer, and reusable entity cards are common to the whole team.

- `/catalog/medications` and `/catalog/molecules` — Hana
- `/catalog/diseases` and `/catalog/symptoms` — Mari
- `/catalog/side-effects` and `/catalog/contraindications` — Oussema
- `/catalog/patients` and `/catalog/conditions` — Sofiene
- `/catalog/studies` and `/catalog/results` — Aymen
- `/search` — shared search interface
- `/graph` — live patient/condition record graph and shared ontology class map
- `/entity/:id` — reusable detail page

Patient and ConditionMedicale collections provide add/edit/delete forms, explicit relationship choices and SPARQL-backed filters. Their profiles and record graph fetch ontology data through FastAPI. Medication collections and profiles use Hana’s pharmacology API, and the shared search combines these records with French natural-language questions. The default API is available at `http://127.0.0.1:8000`. Set `VITE_API_BASE_URL` in an optional local `.env` to override it. Follow `../backend/README_SOFIENE.md` to start the backend and verify its real Fuseki connection. Browser requests go to FastAPI, never directly to Fuseki.

Disease and symptom collections, profiles, relationship links and shared search use Mariem's API. Studies and clinical results use Aymen's API, including filters and statistics. Molecules, side effects and contraindications now load from Fuseki through FastAPI. All ten collections use the backend. The record graph supports all ten domains; shared search also uses these records. Medication composition, including active ingredients, excipients and formulas, comes from the pharmacology API. Clinical pages offer visibly labeled preview records if the API or Fuseki is unavailable; loading, live 404 responses and successful empty collections do not substitute preview records. Sample records and related sample profiles are labeled. Successful loads do not display connection badges or developer notes. The live graph uses explicit triples only; the separate class map describes the specification. Age categories are calculated from age, without claiming OWL reasoning. Do not use these records for clinical decisions.

`npm test` runs the clinical, pharmacology, research, disease and symptom UI regression suites with Vitest and Testing Library. Medication creation, editing and deletion are available from `/catalog/medications`; natural-language questions are available on `/search`. Backend requirements include spaCy and its French language model. Clinical questions include “Quels médicaments prend Karim ?”, “Quels patients ont plus de 65 ans ?” and “Quelles conditions sont physiologiques ?”. Returned clinical records link to their profiles; no hosted LLM API is used.

## Design palette

| Token | Hex |
| --- | --- |
| Deep clinical navy | `#071C2B` |
| Medical navy | `#132E43` |
| Clinical teal | `#068C8A` |
| Bright mint | `#24C5B0` |
| Soft canvas | `#F5F8FB` |
| Neutral white | `#FFFFFF` |

Typography: Manrope for headings, DM Sans for the interface with system-font fallbacks. The interface is responsive and has a Ctrl/Cmd+K search dialog.

See `../docs/VALIDATION_PROJET.md` for the university requirements, NLP tools, demo steps and full-project verification commands.

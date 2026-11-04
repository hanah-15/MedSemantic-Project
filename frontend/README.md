# MedSemantic — Shared frontend

A carefully designed medical ontology research interface built with React, TypeScript, Vite and Lucide icons.

## Get started

Requires Node.js 20.19+ or 22.12+.

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Then open http://localhost:5173.

## Production checks

```powershell
npm run typecheck
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
- `/graph` — shared ontology class graph
- `/entity/:id` — reusable detail page

The frontend currently renders illustrative records, not data fetched from Fuseki. The backend exposes its health endpoint at `http://127.0.0.1:8000/` and the shared API adapter is in `src/lib/api.ts`. Replace the local records with FastAPI data when the team's endpoints are implemented. Avoid direct calls from browsers to Fuseki. Do not use these records for clinical decisions.

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

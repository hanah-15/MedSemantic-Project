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

The Diseases and Symptoms collections, their detail pages, and global search load live records from the FastAPI endpoints. Other collections continue to use illustrative local records. The API base defaults to `http://127.0.0.1:8000`; set `VITE_API_BASE_URL` in a frontend `.env` file to point to a different FastAPI server. The browser calls FastAPI, never Fuseki directly. Local sample records are not clinical guidance.

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

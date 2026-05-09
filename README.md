# Switchboard

> Voice-first AI receptionist for Swedish hantverkare — VVS, el, snickeri. Answers calls 24/7 in natural Swedish, triages, books work directly into the firm's affärssystem, escalates emergencies in seconds.

Built on **Gemini 3.1 Flash Live**. Swedish-native. Trade-specific. EU data residency.

See [`PRD.md`](./PRD.md) for the full product spec.

## Repo layout

```
backend/   FastAPI + Realtime Bridge + Tool Catalog + ADK agent
web/       Next.js owner dashboard (Nordic-styled)
scripts/   Exploration scripts (gem_live.py reference impl)
docs/      Architecture, design system, data model, dev guide
PRD.md     Product Requirements Document
```

## Getting started

```bash
# backend
cd backend && uv sync --extra dev
uv run uvicorn switchboard.app:create_app --factory --reload --port 8000

# web (separate shell)
cd web && pnpm install
pnpm dev   # http://localhost:3000
```

Full guide: [`docs/development.md`](./docs/development.md).

## Status

Closed-beta foundation (PRD Phase 1 scaffolding). Provider adapters (46elks/Twilio) and real CRM integrations are stubbed — see `docs/architecture.md` "MVP gaps" for the deferred surfaces.

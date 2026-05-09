# Backend

Python 3.13 / FastAPI / Pydantic v2 / SQLModel. Managed by `uv`. Lives in `backend/`.

## Layout

```
backend/src/switchboard/
├── core/         config, structlog, ULIDs, time, tenant context, middleware
├── db/           SQLModel engine, session factory, dev seed
├── models/       Pydantic + SQLModel tables (PRD §8.6 + audit_log)
├── tools/        12 function-calling tools — schemas, declarations, dispatch + client
├── services/     Triage, customer, booking, escalation, notification, ROT, audit
├── bridge/       Realtime bridge — audio transcode, Gemini session, WS endpoint
├── agents/       Post-call summarizer (ADK + heuristic fallback)
├── api/          Owner REST routes + live inbox WS + /api/tools/dispatch
├── integrations/ External systems (placeholder; mock impls live in services)
├── scripts/      uv entrypoints (dump_openapi)
├── app.py        Application Backend factory — REST + dashboard WS
└── bridge_app.py Realtime Bridge factory — telephony WS + health
```

Two FastAPI factories share the same package per PRD §2 (single language, two services). Dev runs the umbrella `switchboard.app:create_app` which mounts everything; prod runs them as separate Cloud Run services with `Settings.tool_dispatch_mode = "http"`.

`tests/` mirrors the modules above. `conftest.py` isolates each session into a tmpdir SQLite and seeds the demo firma.

## Conventions

### Typing

- `from __future__ import annotations` at the top of every module.
- Public APIs are Pydantic models (request/response). Internal pure logic uses dataclasses or plain typed functions.
- IDs are `NewType` aliases (`FirmaId`, `CallId`, …) in `core.ids`. Generated via `python-ulid` in `new_id()` so they sort lexicographically by creation time.
- `pyright` is strict in CI — see root `pyproject.toml`.

### Logging

`structlog` everywhere. Use `from switchboard.core.logging import get_logger; log = get_logger("switchboard.<mod>")`. Bound contextvars (`call_id`, `firma_id`) propagate via `merge_contextvars`. JSON output behind `SWITCHBOARD_LOG_JSON=true` for prod.

### Configuration

All settings come from `Settings` in `core.config` — populated from `.env` then `.env.local` (see `.env` precedence in this repo). Keys are prefixed `SWITCHBOARD_*` except `GEMINI_API_KEY`. Never read `os.environ` directly outside `core.config`.

Production-relevant flags:

- `SWITCHBOARD_TOOL_DISPATCH_MODE=http` — bridge calls Application Backend over HTTPS instead of in-process
- `SWITCHBOARD_APPLICATION_BACKEND_URL=https://app.switchboard.se` — target for HTTP dispatch
- `SWITCHBOARD_BRIDGE_INTERNAL_TOKEN=<secret>` — verified by `/api/tools/dispatch`

### Tenant context

Every request binds `firma_id` via `core/middleware.TenantMiddleware` → `core/tenant.firma_context`. structlog merges it into every log line. Inside services that touch tenant data, prefer `require_firma_id()` over receiving `firma_id` as a parameter when the call site is HTTP-driven — it surfaces missing-context bugs as crashes, not silent leaks.

See [`multi-tenancy.md`](./multi-tenancy.md) for the full policy.

### Pydantic vs. SQLModel split

- **Table models** (e.g. `Call(SQLModel, table=True)`) are persistence concerns. They live in `models/`.
- **Read/Write models** (e.g. `CallRead`, `CallDetailRead`) are API concerns. They also live in `models/` but are pure Pydantic. Routes return Read models, never table models.
- A handler converts the table row to the read model. Don't dump table models with `.model_dump()` from a route — fields will leak.

### Adding a new tool

1. Define Args + Result Pydantic models in `tools/schemas.py`. Use `Annotated[…, Field(pattern=…)]` for Swedish constraints (E.164 +46, org-nummer).
2. Add an entry to `TOOL_DESCRIPTIONS` in `tools/declarations.py` with the Swedish description for Gemini.
3. Implement the handler in `tools/handlers.py`. Validate via `<Args>.model_validate(raw)`, call into a service, return `result.model_dump()`.
4. Register a service in `services/` — keep handlers thin.
5. Test in `tests/test_tools_handlers.py` — at least the happy path and one error path.

### Adding a new service

A service is a module under `services/`. Public functions take a `Session` (or pure values) and return Pydantic models or domain objects. Don't import FastAPI symbols. Don't talk to `Settings` directly — accept config via parameters when needed.

### Adding a new route

1. Create `api/routes_<area>.py`. Use `APIRouter(prefix="/api/<area>", tags=["<area>"])`.
2. Inject deps from `api.deps` (`get_db`, `get_current_firma`).
3. Always return Pydantic models (`response_model=…` on the decorator).
4. Mount in `app.create_app()`.
5. Run `uv run dump-openapi && cd ../web && pnpm gen:api` so the dashboard sees the new shapes.

## Running locally

```bash
cd backend
uv sync --extra dev
uv run uvicorn switchboard.app:create_app --factory --reload --port 8000
```

OpenAPI is at `http://127.0.0.1:8000/docs`. Health check is `/health`. The bridge WebSocket is at `/ws/bridge/{firma_id}/{call_id}`.

## Tests

```bash
uv run pytest -q
```

26 tests in MVP. Triage rules, ROT truth table, audio round-trip, model serialization, API smoke. New code without a test is a planning failure.

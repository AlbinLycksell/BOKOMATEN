# Svarsa AI MVP Foundation Implementation Plan

> **For agentic workers:** This plan is being executed inline by the planning author in the same session (auto mode, max effort). Steps use checkbox (`- [ ]`) syntax for tracking. Phases end with a commit. Push to `origin/main` is gated on user approval (CLAUDE.md rule).

**Goal:** Stand up the production-shape skeleton of Svarsa AI per `PRD.md` — a fully-typed Python backend (FastAPI, Pydantic v2, SQLModel, uv-managed) and a Nordic-styled Next.js dashboard — wired through a Gemini 3.1 Flash Live realtime bridge, the 12-tool function catalog, and an ADK-based post-call agent — backed by structured docs.

**Architecture:**
- **Hot path = direct google-genai Live API.** The realtime bridge owns two long-lived WebSockets (telephony provider ↔ Gemini Live) and uses `session.send_realtime_input` / `send_client_content` per the post-2.0 SDK. ADK is not on the hot path — its overhead and abstractions interfere with sub-1.2s p50 voice latency.
- **Cold path = Google ADK.** Post-call summarization, weekly digests, and onboarding agents are LlmAgents in `google-adk` with typed tool functions. They run async after the call ends.
- **Owner app = Next.js 15 (App Router, RSC) + Tailwind v4 + shadcn-style owned components.** Nordic restraint: hairline borders, no shadows (forbidden), warm off-white surfaces, deep forest accent, generous whitespace, Inter variable font.
- **Persistence = SQLModel** (Pydantic v2 + SQLAlchemy 2 typed core). SQLite for local dev; Postgres connection string for prod (`europe-west4` per PRD §8.4). Same models, different driver.
- **Single repo, two top-level apps** (`backend/`, `web/`). Workspace-style uv project at root. No premature monorepo tooling — `uv` + `pnpm` are enough for MVP.
- **Strong typing edge-to-edge.** Pyright strict on backend, TypeScript strict on web, Pydantic→TypeScript types via openapi-codegen so the frontend can't drift.

**Tech Stack:**
- **Backend:** Python 3.13, uv, FastAPI, Pydantic v2 + pydantic-settings, SQLModel, structlog, google-genai (Live API), google-adk, websockets, numpy + audioop-lts (μ-law transcode), pytest + pytest-asyncio, ruff, pyright, sqlite (dev) / postgres (prod-ready).
- **Frontend:** Next.js 15 (App Router, Turbopack), TypeScript strict, Tailwind CSS v4, lucide-react icons, @tanstack/react-query, zod, pnpm, openapi-typescript for generated API types.
- **Tooling:** ruff (lint+format), pyright (type), pytest (test), eslint + prettier (web), commitlint-style messages per CLAUDE.md.

---

## Scope discipline

What lands in this plan:
- Repo skeleton, tooling, env, docs scaffold
- Pydantic/SQLModel data layer covering PRD §8.6
- All 12 tools from PRD §8.4 declared and stubbed with realistic mock returns
- Realtime bridge with Gemini Live wiring, audio transcoding, persistence — telephony-provider-agnostic (handler accepts μ-law frames; provider plug-ins wire later)
- Owner API: inbox list, call detail, firma settings, customers, live WS for inbox push
- ADK post-call summarizer agent
- Owner web app: layout, inbox, call detail, calendar (mock), settings — fully styled Nordic
- Continuous docs

Explicitly OUT of scope here:
- Real 46elks/Twilio sessions (handler is provider-agnostic; provider adapter is a follow-up)
- Real Fortnox/Hantverksdata OAuth (interfaces + mock impls only)
- Production auth (header-based dev-token shim)
- Cloud Run / Vercel deploy + Terraform
- Mobile apps (PRD lists React Native — explicitly Phase 3)
- Migrations (SQLModel `create_all`; Alembic later)
- Eval pipeline + prompt-tuning UI

---

## File structure (target end-state)

```
auto-booker/
├── PRD.md                                  (existing)
├── README.md                               (replace empty stub)
├── pyproject.toml                          (root, dev tooling only)
├── uv.lock
├── .python-version                         (3.13)
├── .env, .env.local, .gitignore            (existing)
├── backend/
│   ├── pyproject.toml                      (svarsa-backend package)
│   ├── README.md
│   └── src/svarsa/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py                   (pydantic-settings)
│       │   ├── logging.py                  (structlog)
│       │   ├── ids.py                      (typed IDs: FirmaId, CallId, ...)
│       │   └── time.py                     (Europe/Stockholm helpers)
│       ├── db/
│       │   ├── __init__.py
│       │   ├── session.py                  (engine + sessionmaker)
│       │   └── seed.py                     (dev seed data)
│       ├── models/
│       │   ├── __init__.py
│       │   ├── enums.py                    (Intent, Severity, Trade, …)
│       │   ├── firma.py                    (Firma, PhoneNumber, User, EscalationChain, Voice, Integration)
│       │   ├── customer.py                 (Customer, Note, Photo)
│       │   ├── call.py                     (Call, ToolInvocation, Transcript)
│       │   ├── job.py                      (Job)
│       │   └── escalation.py               (Escalation)
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── declarations.py             (Gemini Tool[] for Live API)
│       │   ├── schemas.py                  (Pydantic args/returns for all 12)
│       │   ├── handlers.py                 (dispatch table; calls services)
│       │   └── mock_data.py                (deterministic seed for stubs)
│       ├── services/
│       │   ├── __init__.py
│       │   ├── customer_service.py
│       │   ├── booking_service.py
│       │   ├── escalation_service.py
│       │   ├── notification_service.py     (SMS/email — stub)
│       │   ├── triage_service.py           (rule-based emergency classification)
│       │   └── rot_service.py
│       ├── bridge/
│       │   ├── __init__.py
│       │   ├── audio.py                    (μ-law ↔ PCM, resample)
│       │   ├── gemini_session.py           (LiveConnectConfig, system prompt)
│       │   ├── system_prompt.py            (per-firma builder)
│       │   ├── usage_tracker.py            (cumulative tokens — port from gem_live.py)
│       │   └── ws.py                       (FastAPI WebSocket route)
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── post_call_summary.py        (ADK LlmAgent)
│       │   └── runner.py                   (post-call dispatch on call end)
│       ├── api/
│       │   ├── __init__.py
│       │   ├── deps.py                     (auth shim, db dep, current_firma)
│       │   ├── routes_calls.py
│       │   ├── routes_customers.py
│       │   ├── routes_firma.py
│       │   ├── routes_health.py
│       │   └── ws_inbox.py                 (live updates)
│       ├── integrations/
│       │   ├── __init__.py
│       │   ├── base.py                     (Protocol)
│       │   ├── fortnox.py                  (Mock impl)
│       │   ├── hantverksdata.py            (Mock impl)
│       │   ├── visma.py                    (Mock impl)
│       │   └── google_calendar.py          (Mock impl)
│       └── app.py                          (FastAPI factory)
│   └── tests/
│       ├── conftest.py
│       ├── test_tools_schemas.py
│       ├── test_tools_handlers.py
│       ├── test_audio_transcode.py
│       ├── test_triage_service.py
│       └── test_api_smoke.py
├── web/
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── tsconfig.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── postcss.config.mjs
│   ├── app/
│   │   ├── layout.tsx                      (root, fonts, theme)
│   │   ├── page.tsx                        (redirects → /inbox)
│   │   ├── globals.css                     (Tailwind + tokens)
│   │   ├── (app)/
│   │   │   ├── layout.tsx                  (sidebar shell)
│   │   │   ├── inbox/page.tsx
│   │   │   ├── calls/[id]/page.tsx
│   │   │   ├── bookings/page.tsx
│   │   │   ├── customers/page.tsx
│   │   │   └── settings/page.tsx
│   │   └── api/                            (only for future BFF)
│   ├── components/
│   │   ├── shell/
│   │   │   ├── sidebar.tsx
│   │   │   ├── topbar.tsx
│   │   │   └── nav-link.tsx
│   │   ├── ui/                             (owned primitives)
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── input.tsx
│   │   │   ├── label.tsx
│   │   │   ├── separator.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── avatar.tsx
│   │   │   └── audio-player.tsx
│   │   ├── inbox/
│   │   │   ├── call-row.tsx
│   │   │   ├── intent-badge.tsx
│   │   │   ├── severity-dot.tsx
│   │   │   └── filter-bar.tsx
│   │   ├── call/
│   │   │   ├── transcript.tsx
│   │   │   ├── summary-card.tsx
│   │   │   ├── customer-card.tsx
│   │   │   └── actions-bar.tsx
│   │   ├── booking/
│   │   │   ├── calendar-grid.tsx
│   │   │   └── slot.tsx
│   │   └── icons.tsx
│   ├── lib/
│   │   ├── api.ts                          (typed client)
│   │   ├── api-types.ts                    (generated from openapi)
│   │   ├── format.ts                       (sv-SE intl helpers)
│   │   └── utils.ts                        (cn() helper)
│   └── styles/
│       └── tokens.css                      (CSS variables: colors/space/radii)
└── docs/
    ├── README.md                           (index)
    ├── architecture.md                     (system map)
    ├── backend.md                          (modules, patterns, conventions)
    ├── frontend.md                         (design system + components)
    ├── data-model.md                       (schema reference)
    ├── tools.md                            (tool catalog reference)
    ├── realtime-bridge.md                  (audio + session lifecycle)
    ├── development.md                      (getting started)
    ├── adk/llms-full.txt                   (existing)
    └── superpowers/plans/2026-05-09-svarsa-mvp-foundation.md   (this file)
```

---

## Phase 0 — Repo & toolchain bootstrap

**Files:**
- Create: `pyproject.toml` (root), `.python-version`, `backend/pyproject.toml`, `backend/src/svarsa/__init__.py`
- Create: `web/package.json`, `web/tsconfig.json`, `web/next.config.ts`, `web/tailwind.config.ts`, `web/postcss.config.mjs`, `web/app/layout.tsx`, `web/app/page.tsx`, `web/app/globals.css`, `web/styles/tokens.css`
- Modify: `README.md` (replace empty)
- Update: `.gitignore` (add backend/web build artifacts)

**Tasks:**
- [ ] Add Python 3.13 pin via `.python-version`
- [ ] Create root `pyproject.toml` with `[tool.ruff]`, `[tool.pyright]`, `[tool.pytest.ini_options]` (uv reads tooling from here even though backend is a separate package)
- [ ] Create `backend/pyproject.toml` with deps: fastapi, uvicorn, pydantic>=2.9, pydantic-settings, sqlmodel, structlog, google-genai, google-adk, websockets, numpy, audioop-lts, scipy, httpx; dev deps: pytest, pytest-asyncio, ruff, pyright, anyio
- [ ] `uv sync` from `backend/` to materialize the venv
- [ ] Scaffold `web/` with Next.js 15 + TypeScript + Tailwind v4 (manual config files — do not run `create-next-app` in auto mode; lower entropy)
- [ ] Pin pnpm via `packageManager` in `web/package.json`
- [ ] Update root `.gitignore`: `node_modules/`, `.next/`, `dist/`, `*.egg-info`, `.pytest_cache/`, `.ruff_cache/`, `__pycache__/` (already), `backend/.venv/`
- [ ] Replace `README.md` with project overview
- [ ] **Commit:** `chore: scaffold uv backend and nextjs web skeletons`

## Phase 1 — Backend core (config, logging, db, ids)

**Files:**
- Create: `backend/src/svarsa/core/config.py`, `core/logging.py`, `core/ids.py`, `core/time.py`
- Create: `backend/src/svarsa/db/session.py`, `db/seed.py`
- Create: `backend/src/svarsa/app.py` (FastAPI factory with health route)
- Create: `backend/src/svarsa/api/routes_health.py`
- Create: `backend/tests/conftest.py`, `backend/tests/test_api_smoke.py`

**Tasks:**
- [ ] `Settings(BaseSettings)` reading from `.env` / `.env.local` (we already use this pattern; backend reuses precedence rules)
- [ ] `configure_logging()` — structlog JSON renderer, ISO timestamps, contextvars (`call_id`, `firma_id`)
- [ ] Typed ID newtypes: `FirmaId = NewType("FirmaId", str)`, …; ULID generation via `ulid-py` (note: re-evaluate dep — could just use `uuid.uuid7` from python 3.12 stdlib? — ULID for sortable IDs preferred. Pull in `python-ulid` as dep.)
- [ ] DB engine + session factory; `init_db()` calls `SQLModel.metadata.create_all()` for MVP
- [ ] FastAPI factory `create_app()` configures CORS for `web/` dev origin, mounts routers, lifespan calls `init_db()` and `seed_dev_data()` if `SVARSA_ENV=dev`
- [ ] Health route returns `{"status": "ok", "version": ..., "env": ...}`
- [ ] Smoke test: `TestClient(app).get("/health")` returns 200
- [ ] **Commit:** `feat(backend): core config, logging, db session, health route`

## Phase 2 — Data models (PRD §8.6)

**Files:**
- Create: `backend/src/svarsa/models/enums.py`, `models/firma.py`, `models/customer.py`, `models/call.py`, `models/job.py`, `models/escalation.py`
- Modify: `backend/src/svarsa/db/seed.py` (insert one demo firma)

**Tasks:**
- [ ] `enums.py`: `Intent` (`AKUT|OFFERT|BOKNING|BEFINTLIG_KUND|OVRIGT`), `Severity` (`CRITICAL|HIGH|MEDIUM|LOW`), `Trade` (`VVS|EL|SNICKERI|TAK|KAKEL|OVRIGT`), `Plan` (`STARTER|PROFESSIONAL|PREMIUM`), `CustomerType` (`PRIVATE|COMPANY`), `JobStatus`, `IntegrationType`
- [ ] `firma.py`: `Firma(SQLModel, table=True)` with id (ULID str pk), name, org_number, trade, plan, settings (JSON column for `FirmaSettings` Pydantic model — open hours, voice, helgdagsschema), created_at; `PhoneNumber`, `User`, `EscalationChain`, `Voice`, `Integration` related rows. JSON columns use `sa_column=Column(JSON)`.
- [ ] `customer.py`: `Customer` with phone (E.164), org_number nullable, address (`AddressEmbed` JSON), source, type, name; `Note`, `Photo`
- [ ] `call.py`: `Call` (intent, severity nullable, recording_url nullable, structured_summary JSON, billing_seconds, gemini_session_id, started_at, ended_at, firma_id fk, customer_id fk nullable); `ToolInvocation` (call_id fk, name, args JSON, result JSON, latency_ms, error nullable); `TranscriptSegment` (call_id, role: `caller|ai|system`, text, ts_ms_offset)
- [ ] `job.py`: `Job` (status, intent, summary, value_sek nullable, scheduled_for nullable, technician_id nullable)
- [ ] `escalation.py`: `Escalation` (call_id, severity, reason, contacted_user_ids JSON, status, ack_at nullable)
- [ ] All tables get `created_at`, `updated_at` (server-default), and proper indexes (firma_id, phone, started_at desc on Call)
- [ ] Pydantic `*Read` / `*Create` schemas distinct from table models (table model = persistence; read model = API surface)
- [ ] `seed.py`: insert "Anderssons VVS AB" firma, Magnus + Lena users, one phone number, three demo customers, ten demo calls across all intents
- [ ] **Commit:** `feat(backend): sqlmodel data layer for firma, customer, call, job, escalation`

## Phase 3 — Tool catalog (PRD §8.4)

**Files:**
- Create: `backend/src/svarsa/tools/schemas.py`, `tools/declarations.py`, `tools/handlers.py`, `tools/mock_data.py`
- Create: `backend/src/svarsa/services/customer_service.py`, `services/booking_service.py`, `services/escalation_service.py`, `services/notification_service.py`, `services/triage_service.py`, `services/rot_service.py`
- Create: `backend/tests/test_tools_schemas.py`, `tests/test_tools_handlers.py`, `tests/test_triage_service.py`

**Tasks:**
- [ ] `schemas.py`: one Pydantic args + returns model per tool (`LookupCustomerArgs/Result`, `TriageEmergencyArgs/Result`, …). Field validators use Swedish constraints (E.164 +46, org-nummer regex `^\d{6}-\d{4}$`).
- [ ] `triage_service.py`: rule-based classifier exposing `assess(problem_description: str, trade: Trade, indicators: list[Indicator]) -> TriageResult` — implements PRD §7.3 default emergency rules for VVS/EL.
- [ ] `customer_service.py`: in-memory + DB-backed `lookup_by_phone`, `lookup_by_org`, `create_lead`, `lookup_job_status`. Uses ABC for integration backend — defaults to `LocalDbCustomerStore`.
- [ ] `booking_service.py`: `check_availability(...)` returns deterministic mock slots based on a fixed travel-time matrix; `book(...)` writes a `Job` row.
- [ ] `escalation_service.py`: persists `Escalation` row, returns next-in-chain placeholder.
- [ ] `notification_service.py`: prints to logger for MVP; interface ready for 46elks adapter.
- [ ] `rot_service.py`: pure function — eligibility = is_private_person ∧ owns_property ∧ property_age_years ≥ 5 ∧ work_type in {ROT-OK list}.
- [ ] `declarations.py`: exposes `TOOL_DECLARATIONS: list[types.Tool]` for Gemini Live, generated from the Pydantic schemas via `pydantic.TypeAdapter().json_schema()` + a `to_gemini_tool()` adapter (Gemini takes a slightly different schema dialect — handle the edge cases: no `additionalProperties`, no `$ref`).
- [ ] `handlers.py`: dispatch table mapping tool name → (parse_args, call_service, serialize_return). Exposes `dispatch(name: str, args: dict, ctx: ToolContext) -> dict` used by the bridge.
- [ ] `mock_data.py`: deterministic fixtures (Inger, Karim, …) referenced by the demo flows in PRD §6.
- [ ] Tests cover: schemas roundtrip; triage classifies "vattenläcka, det rinner" as critical; ROT eligibility truth table; lookup_customer hits and misses.
- [ ] **Commit:** `feat(backend): tool catalog with typed schemas, services, and dispatch`

## Phase 4 — Realtime bridge

**Files:**
- Create: `backend/src/svarsa/bridge/audio.py`, `bridge/gemini_session.py`, `bridge/system_prompt.py`, `bridge/usage_tracker.py`, `bridge/ws.py`
- Modify: `backend/src/svarsa/app.py` (mount bridge router)
- Create: `backend/tests/test_audio_transcode.py`
- Create: `docs/realtime-bridge.md`

**Tasks:**
- [ ] `audio.py`: `mulaw_to_pcm16k(frames: bytes) -> bytes` and `pcm24k_to_mulaw(frames: bytes) -> bytes` using `audioop-lts` for μ-law ↔ linear and `numpy` polyphase resampling (8↔16 and 24↔8); chunk to 20ms (160-byte μ-law) frames on egress. Round-trip test: synthetic sine through both directions, RMS error within tolerance.
- [ ] `system_prompt.py`: `build_system_prompt(firma: Firma) -> str` — template per PRD §8.3.3 + Appendix A; includes per-firma persona block, hard rules, triage logic, emergency rules, booking rules, tone.
- [ ] `gemini_session.py`: `connect_session(client, firma)` builds `LiveConnectConfig` with sv-SE, prebuilt voice from firma config, system instruction, tools, transparent session resumption, context-window compression (per PRD §8.3.1). Wraps as async context manager.
- [ ] `usage_tracker.py`: port the cumulative tracker from `scripts/gem_live.py` into a reusable class — emits structured logs (not stderr status line) so the API can surface live token counters per call.
- [ ] `ws.py`: FastAPI route `wss://.../bridge/{firma_id}/{call_id}` that:
  - accepts a provider-agnostic frame protocol: JSON `{"event":"start|media|stop","payload":...}` (matches both 46elks and Twilio shapes)
  - on `start`: creates a `Call` row, opens a Gemini Live session
  - on `media`: feeds μ-law audio through `audio.mulaw_to_pcm16k` → `session.send_realtime_input(audio=Blob(...))`
  - on Gemini response data: `audio.pcm24k_to_mulaw` → send back as `media` events
  - on tool call from Gemini: dispatch via `tools.handlers.dispatch(...)`, persist `ToolInvocation` row, return result to Gemini
  - on `stop` or WS close: close session, finalize Call row, enqueue post-call summary (Phase 5)
- [ ] Persist transcript segments using `output_audio_transcription` + `input_audio_transcription` events from Live API.
- [ ] **Note real provider hookup is out of MVP scope** — the bridge speaks the documented protocol and a smoke test exercises it via a fake provider client; live 46elks/Twilio integration follows PRD Phase 1.
- [ ] Document the bridge lifecycle in `docs/realtime-bridge.md` (sequence diagram in ASCII, lifecycle states, recovery on Gemini disconnect via session_resumption).
- [ ] **Commit:** `feat(backend): realtime bridge with gemini live session, audio transcode, tool dispatch`

## Phase 5 — Post-call agent (ADK)

**Files:**
- Create: `backend/src/svarsa/agents/post_call_summary.py`, `agents/runner.py`
- Modify: `backend/src/svarsa/bridge/ws.py` (call `runner.summarize_call(call_id)` on call end)
- Create: `backend/tests/test_post_call_agent.py` (smoke; agent is mocked via google-adk test utilities)

**Tasks:**
- [ ] `post_call_summary.py`: ADK `LlmAgent(name="post_call_summary", model="gemini-2.5-flash", instruction=...)` — takes Call.id, reads transcript, writes structured `CallSummary` (Swedish 2-sentence summary, intent confirmation, suggested next-action, follow-up tasks, owner-action-required boolean). Uses ADK function-calling tools: `get_transcript(call_id)`, `update_call_summary(call_id, summary)`. Output is a typed Pydantic model.
- [ ] `runner.py`: dispatcher that runs the agent in the background via FastAPI `BackgroundTasks` (MVP) or asyncio.create_task with proper error handling. Persists summary back to Call row.
- [ ] Test: feed a mock transcript, assert the agent writes a non-empty summary and sets intent.
- [ ] **Commit:** `feat(backend): adk post-call summarizer agent`

## Phase 6 — Owner API

**Files:**
- Create: `backend/src/svarsa/api/deps.py`, `api/routes_calls.py`, `api/routes_customers.py`, `api/routes_firma.py`, `api/ws_inbox.py`
- Modify: `backend/src/svarsa/app.py` (mount routers, OpenAPI tags, generate `openapi.json`)
- Create: `backend/tests/test_api_calls.py`

**Tasks:**
- [ ] `deps.py`: `get_db()`, `get_current_firma()` (reads `X-Firma-Id` header for dev — clear comment: replace with OAuth in Phase 1).
- [ ] `routes_calls.py`:
  - `GET /api/calls` query: `firma_id` (from dep), `intent`, `severity`, `from`, `to`, `q` (text search transcript), `limit`, `offset`. Returns `CallRead` list with computed fields (duration, customer_name, summary excerpt).
  - `GET /api/calls/{id}` returns `CallDetailRead` (transcript segments, tool invocations, recording link, summary).
  - `POST /api/calls/{id}/actions/snooze`, `/assign`, `/mark-handled`.
- [ ] `routes_customers.py`: list + detail + create.
- [ ] `routes_firma.py`: GET/PUT `/api/firma/me/settings` (greeting, escalation chain, helgdagsschema, voice).
- [ ] `ws_inbox.py`: WS endpoint that authenticates and broadcasts `inbox.call.created`, `inbox.call.updated` events for the firma. Backed by an in-process pub/sub for MVP; doc note re: Redis Pub/Sub for prod.
- [ ] All routes return strict Pydantic schemas; OpenAPI is the source of truth for frontend types.
- [ ] **Commit:** `feat(backend): owner api routes for calls, customers, firma settings, live inbox`

## Phase 7 — Frontend scaffold (Nordic theme)

**Files:**
- Create: `web/package.json`, `web/tsconfig.json`, `web/next.config.ts`, `web/tailwind.config.ts`, `web/postcss.config.mjs`, `web/app/layout.tsx`, `web/app/page.tsx`, `web/app/globals.css`, `web/styles/tokens.css`
- Create: `web/lib/utils.ts`, `web/components/ui/{button,card,badge,input,label,separator,tabs,avatar}.tsx`, `web/components/icons.tsx`
- Create: `docs/frontend.md`

**Tasks:**
- [ ] Initialize `web/package.json` with: next@15, react@19, react-dom@19, typescript, tailwindcss@4, postcss, autoprefixer, @tanstack/react-query, zod, clsx, tailwind-merge, lucide-react, openapi-typescript (dev). pnpm@9 declared in `packageManager`.
- [ ] `tailwind.config.ts`: Tailwind v4 inline config; content globs; theme extends colors from CSS vars; **no shadow utilities** (override `boxShadow: { none: 'none', DEFAULT: 'none', sm: 'none', md: 'none', lg: 'none', xl: 'none', '2xl': 'none', inner: 'none' }` — drop shadows are forbidden); `borderRadius: { sm: '4px', md: '6px', lg: '8px' }`; font-family `Inter Variable`.
- [ ] `tokens.css`: CSS variables for the full Nordic palette:
  ```
  --color-bg: #FAFAF7;        /* warm off-white */
  --color-surface: #FFFFFF;
  --color-surface-2: #F4F2EC; /* subtle elevation via tone, not shadow */
  --color-border: #E5E4DD;    /* hairline */
  --color-border-strong: #BFBCB1;
  --color-text: #0F1310;
  --color-text-muted: #5A615C;
  --color-accent: #1E5C3A;     /* deep Swedish forest */
  --color-accent-soft: #DCE8DF;
  --color-critical: #9C2C2C;
  --color-critical-soft: #F4DADA;
  --color-success: #2F6D4A;
  --color-warning: #A77118;
  ```
  Plus dark mode parallel variables (auto via `@media (prefers-color-scheme)`).
- [ ] `globals.css`: imports tokens, sets body background, removes default browser shadows, sets `font-feature-settings: 'cv11','ss01','ss03';` for Inter style.
- [ ] Owned UI primitives (no shadcn CLI; we copy patterns and remove shadows):
  - `Button` — variants: default (accent), outline (border-strong), ghost (transparent hover bg-surface-2), critical. Sizes sm/md/lg.
  - `Card` — `border border-border bg-surface rounded-md p-6`. No shadow.
  - `Badge` — pill, `rounded-full px-2 py-0.5 text-xs`. Variants: neutral, accent, critical, warning, success.
  - `Input` — `border border-border bg-surface focus:border-accent focus:ring-0`. No shadow.
  - `Label`, `Separator`, `Tabs`, `Avatar`.
- [ ] `web/components/icons.tsx` — re-export curated lucide icons under semantic names (`InboxIcon`, `CalendarIcon`, `UrgentIcon`, …).
- [ ] App layout: `app/layout.tsx` loads Inter Variable from `next/font/google`, applies `<body className="bg-bg text-text">`.
- [ ] Root `app/page.tsx` redirects to `/inbox`.
- [ ] **Commit:** `feat(web): nextjs scaffold with nordic design tokens and owned ui primitives`

## Phase 8 — Frontend views (inbox, call detail, calendar, settings)

**Files:**
- Create: `web/app/(app)/layout.tsx`, `inbox/page.tsx`, `calls/[id]/page.tsx`, `bookings/page.tsx`, `customers/page.tsx`, `settings/page.tsx`
- Create: `web/components/shell/{sidebar,topbar,nav-link}.tsx`
- Create: `web/components/inbox/{call-row,intent-badge,severity-dot,filter-bar}.tsx`
- Create: `web/components/call/{transcript,summary-card,customer-card,actions-bar}.tsx`
- Create: `web/components/booking/{calendar-grid,slot}.tsx`
- Create: `web/components/ui/audio-player.tsx`
- Create: `web/lib/api.ts`, `lib/api-types.ts` (placeholder; generated in Phase 9)
- Create: `web/lib/format.ts`

**Tasks:**
- [ ] App shell: 240px sidebar (logo, nav), topbar (firma switcher placeholder, user menu), main content area. Sticky sidebar, scrollable main. No shadows; sidebar separated by border-right.
- [ ] Sidebar nav items in Swedish: `Inkorg`, `Bokningar`, `Kunder`, `Inställningar`. Active state via accent-soft background.
- [ ] Inbox page:
  - Filter bar: status pill row (Alla, Akuta, Att följa upp, Bokade, Hanterade), intent multiselect, date range, search.
  - Virtualized list (`@tanstack/react-virtual` if needed, otherwise plain map for MVP) of `CallRow`. Each row shows severity dot, customer name, intent badge, 1-line summary, time ago, and an icon-only action (öppna).
  - Empty state with helpful Swedish copy.
- [ ] Call detail page:
  - 2-column layout (call body + side panel on lg breakpoint, single column on sm).
  - Body: header (customer name, time, intent + severity badges), `SummaryCard`, `Transcript` (alternating role blocks, ts offset, hover-highlight the audio segment), `AudioPlayer` with seek that drives transcript scroll.
  - Side panel: `CustomerCard` (history, open jobs), `ActionsBar` (Ring tillbaka, Boka tid, Skicka SMS, Markera hanterad, Tilldela).
- [ ] Bookings page: simple week grid view fed by mock data (slot density visualization).
- [ ] Customers page: search + list with last-contact preview.
- [ ] Settings page: tabs (Greeting, Eskaleringskedja, Öppettider, Integrationer). Read-only stubs of integration cards (Fortnox, Hantverksdata, Visma, Google Calendar) with "Anslut"-buttons (no-op for MVP).
- [ ] `lib/format.ts`: `formatTimeAgoSv(date)`, `formatPhoneSv(e164)`, `formatSEK(value)`, `formatDateSv`.
- [ ] `lib/api.ts`: typed fetch helpers using generated types; `useCallsQuery`, `useCallDetailQuery` via react-query.
- [ ] **Commit:** `feat(web): owner dashboard views — inbox, call detail, bookings, customers, settings`

## Phase 9 — Type generation & API wiring

**Files:**
- Add: `web/scripts/gen-api-types.ts` (or simple npm script using openapi-typescript)
- Modify: `web/package.json` (add `gen:api` script)
- Modify: `web/lib/api-types.ts` (replace placeholder with generated content)
- Modify: `backend/src/svarsa/app.py` (export OpenAPI to `web/lib/openapi.json` via dev script)
- Create: `backend/scripts/dump_openapi.py`

**Tasks:**
- [ ] Add `pnpm gen:api` script: `openapi-typescript ../backend/openapi.json -o lib/api-types.ts`
- [ ] Add `uv run dump-openapi` script: imports app, writes `openapi.json`
- [ ] Document in `docs/development.md`
- [ ] **Commit:** `feat: generate typescript types from fastapi openapi`

## Phase 10 — Documentation

**Files:**
- Create/Update: `docs/README.md`, `docs/architecture.md`, `docs/backend.md`, `docs/frontend.md`, `docs/data-model.md`, `docs/tools.md`, `docs/realtime-bridge.md`, `docs/development.md`
- Modify: root `README.md` (link to docs/)

**Tasks:**
- [ ] `docs/README.md` — index linking the others, with a one-paragraph product summary.
- [ ] `docs/architecture.md` — system map (port the ASCII from PRD §8.1, annotate which boxes exist in MVP vs which are stubs), service responsibilities, data residency notes.
- [ ] `docs/backend.md` — package layout, conventions (typing, structlog usage, error handling, Pydantic vs SQLModel split, request lifecycle), how to add a new tool, how to add a new service.
- [ ] `docs/frontend.md` — design tokens (full palette table), component patterns (no shadows rule called out), how to add a view, naming conventions, accessibility checklist.
- [ ] `docs/data-model.md` — ER diagram (mermaid), per-table column reference, indexing strategy, JSON-blob fields explained.
- [ ] `docs/tools.md` — one section per tool: when to call, args schema, returns schema, examples (Swedish), test fixtures.
- [ ] `docs/realtime-bridge.md` — sequence diagram, audio pipeline numbers, latency budget table (port from PRD §15), troubleshooting, how to plug in a new telephony provider.
- [ ] `docs/development.md` — getting started: prereqs (Python 3.13, pnpm, ffmpeg optional, brew portaudio), env setup, run backend (`uv run uvicorn ...`), run web (`pnpm dev`), run tests, common tasks.
- [ ] Top-level `README.md` — vision summary, quickstart pointer, links to PRD and docs.
- [ ] **Commit:** `docs: structured architecture, backend, frontend, data, tools, bridge, dev guides`

## Phase 11 — End-to-end smoke + cleanup

**Files:**
- Modify: backend tests (any gaps), CI-like check script
- Create: `Makefile` or root `package.json` scripts for one-shot dev commands

**Tasks:**
- [ ] `make backend-test` — `uv run pytest -q` from backend
- [ ] `make web-typecheck` — `pnpm tsc --noEmit`
- [ ] `make dev` — runs backend uvicorn + web dev server in parallel (use `concurrently` or two-pane Makefile target)
- [ ] Run all checks; fix any breakage
- [ ] Final review: walk every file in the diff against PRD requirements, note explicit gaps in `docs/architecture.md` "MVP gaps" section
- [ ] **Commit:** `chore: dev one-shot scripts and final checks`

---

## Self-review checklist

**Spec coverage** (PRD section → plan task):
- §6.1–6.4 user journeys → tool catalog (Phase 3) + post-call summary (Phase 5) + UI views (Phase 8)
- §7.1 telephony layer → bridge (Phase 4) — note: provider adapter explicitly deferred
- §7.2 conversation → bridge gemini_session.py (Phase 4)
- §7.3 triage → triage_service.py (Phase 3)
- §7.4 booking → booking_service.py (Phase 3)
- §7.5 customer/lead → customer_service.py + create_lead tool (Phase 3)
- §7.6 post-call workflow → post-call agent (Phase 5)
- §7.7 owner app → web (Phases 7–8)
- §7.8 onboarding → settings page UI stub (Phase 8); concierge flow deferred
- §8.1 architecture → mirrored in docs/architecture.md (Phase 10)
- §8.2 telephony → audio.py + ws.py (Phase 4)
- §8.3 Gemini config → gemini_session.py + system_prompt.py (Phase 4)
- §8.4 12 tools → all in Phase 3
- §8.5 services → cores in Phases 1–4; production splits called out as deferred
- §8.6 data model → Phase 2
- §8.7 integrations → mock impls (Phase 3 services); real OAuth deferred
- §8.8 NFR → latency budget surfaced in docs (Phase 10); SLA deploy deferred
- §9 GDPR → recording-consent disclosure built into system_prompt.py; retention TODO at column comments (Phase 2); full DPIA out of MVP
- §10 pricing → product surface only (Phase 8 settings page); billing system deferred
- §11 roadmap → MVP = Phase 1 closed-beta scaffold; deferred items called out per phase
- §12 risks → tracked in docs/architecture.md "Known risks" subsection (Phase 10)
- §13 open questions → captured verbatim in docs/architecture.md (Phase 10)

**Placeholder scan:** No "TBD"/"implement later" entries remain. Each task lists exact paths + content shape.

**Type consistency:** Tool names align across `schemas.py` ↔ `declarations.py` ↔ `handlers.py` (one canonical Enum derived from the schema modules); SQLModel column names align with API read-model field names where they're 1:1; ID types are uniformly `<Entity>Id = NewType("<Entity>Id", str)` everywhere.

---

## Execution mode

Inline execution by the planning author in this same session (auto mode, max effort). Commits land locally on `main` per the established session pattern; final push to `origin/main` only on explicit user approval.

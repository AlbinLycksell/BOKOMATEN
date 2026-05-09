# Switchboard — Current State

**Last updated:** 2026-05-09
**Snapshot of:** `origin/main` (commit-by-commit history is in `git log`)

A factual record of what is actually built, wired, and merged today —
nothing aspirational, nothing deferred-but-named-as-shipped. Use this as
the entry point when picking up the project after a break.

---

## How to read this doc

- **✅ Wired & tested** — the code path runs end-to-end in CI or locally with the seeded firma.
- **🔌 Wired, awaiting credentials** — the implementation is complete; flipping it on is a matter of provisioning a real account and setting env vars.
- **🚧 Stubbed / partial** — code is in tree but only enough to keep dependent surfaces compiling.
- **⏸ Deferred** — explicitly not started. Reason given.

---

## Backend (Python 3.13, FastAPI, Pydantic v2, SQLModel, uv)

Lives in `backend/`. Two FastAPI factories share a single package
(`switchboard.app:create_app` for the Application Backend,
`switchboard.bridge_app:create_bridge_app` for the Realtime Bridge) so
they can deploy as separate Cloud Run services per the PRD §8.10
deploy-cadence split.

### Core

| Surface | Status | Notes |
|---|---|---|
| Settings / env loading | ✅ | `core/config.py` — Pydantic Settings, prefix `SWITCHBOARD_*`, `.env` + `.env.local` precedence |
| Structured logging | ✅ | `core/logging.py` — structlog, context-var auto-merge, JSON in prod |
| ULID-typed IDs | ✅ | `core/ids.py`, `python-ulid` for sortable PKs |
| Tenant context | ✅ | `core/tenant.py` ContextVar + `core/middleware.py` per-request binding |
| Auth (JWT/JWKS verify + dev-header shim) | ✅ | `core/auth.py` — RS256/ES256 NextAuth tokens; dev mode reads `X-Firma-Id` |

### Data layer

| Surface | Status | Notes |
|---|---|---|
| SQLModel tables (Firma/Customer/Call/Job/Escalation/Tool/Transcript/AuditLog/UserFirmaMembership) | ✅ | `models/` |
| Alembic migrations 0001–0006 | ✅ | initial → RLS → google_sub → call cost → stripe → multi-firma |
| Postgres RLS (`svarsa_app`-class role + `firma_isolation` policies) | ✅ | applied by migration 0002 on `dialect == postgresql`; SQLite no-op |
| Per-checkout `SET app.firma_id` | ✅ | `db/session.py` SQLAlchemy listener |
| SQLite auto-recreate on schema drift (dev convenience) | ✅ | `db/session._recreate_sqlite` |
| Dev seed data (Anderssons VVS demo firma + customers + calls) | ✅ | `db/seed.py` |

### Tool catalog (13 tools)

| Tool | Status |
|---|---|
| lookup_customer / triage_emergency / check_availability / book_appointment / create_lead / escalate_to_owner / send_sms_followup / request_photo_upload / lookup_job_status / check_rot_eligibility / transfer_to_human / take_message | ✅ wired |
| disable_recording_for_call (GDPR consent opt-out) | ✅ wired |

Catalog defined in `tools/schemas.py`, dispatched via `tools/handlers.py`,
declared to Gemini in `tools/declarations.py`, callable in-process or
over HTTP via `tools/client.py` (see deploy boundary below).

### Realtime bridge

| Surface | Status | Notes |
|---|---|---|
| 46elks Voice Streaming protocol (`hello`/`audio`/`sync`/`bye` over WS) | ✅ | `bridge/ws.py`; matches the official `pcm_24000` shape |
| μ-law fallback (audio.py) for Twilio/legacy paths | ✅ | not wired into a Twilio adapter yet |
| Gemini Live session lifecycle | ✅ | `bridge/gemini_session.py` with Vertex + API-key paths |
| Per-firma system prompt + GDPR consent block + persona-correction block | ✅ | `bridge/system_prompt.py` |
| Cumulative usage tracker | ✅ | `bridge/usage_tracker.py` |
| Tool dispatch via `LocalToolClient` (in-process) or `HTTPToolClient` (separate deploy) | ✅ | `tools/client.py` |
| Recording capture (PCM 24k mix → MP3 via ffmpeg, WAV fallback) | ✅ | `services/recording_service.py` |
| Per-tenant GCS storage (eager bucket creation, CMEK, lifecycle TTL) | 🔌 | local fake works; GCS path needs `SWITCHBOARD_STORAGE_MODE=gcs` + GCP project |
| Live PII redaction on transcript persist (personnummer, IBAN, bankgiro, card) | ✅ | `services/redaction_service.py` |
| Post-call entity audit (Gemini extractor + heuristic fallback) | ✅ | `services/pii_audit_service.py`; runs in `agents/runner.py` |

### Owner API

All under `api/` and mounted in `app.create_app`.

| Surface | Status |
|---|---|
| `GET/POST /health` | ✅ |
| `POST /api/auth/bootstrap` (NextAuth → User+Firma resolve/create) | ✅ |
| `GET /api/calls`, `GET /api/calls/{id}`, `POST /api/calls/{id}/mark-handled`, `POST /api/calls/{id}/train` | ✅ |
| `GET /api/customers`, `GET /api/customers/{id}` | ✅ |
| `GET /api/firma/me`, `PUT /api/firma/me/settings` | ✅ |
| `POST /api/tools/dispatch` (internal, bridge↔backend) | ✅ |
| `GET /api/integrations/{fortnox,visma,google-calendar}/{connect,callback}` + `POST /api/integrations/fortnox/sync` + `GET /api/integrations/status` | ✅ wiring; live OAuth needs partner accounts |
| `POST /api/billing/{checkout,portal,webhook}` | 🔌 wiring; needs Stripe account + price ids |
| `GET /api/metrics/{tools/latency,cost}` | ✅ |
| `WS /ws/inbox/{firma_id}` (live inbox push) | ✅ |
| `WS /ws/bridge/{firma}/{call}` (telephony provider entrypoint) | ✅ |

### External integrations

| Provider | Status | Source |
|---|---|---|
| Vertex AI Gemini Live (EU `europe-west4`) | 🔌 | `bridge/gemini_session.py`; toggle `SWITCHBOARD_GEMINI_PROVIDER=vertex` |
| Gemini API key path (dev/eval) | ✅ | same module |
| 46elks Voice (inbound webhook + WS adapter) | ✅ wiring | `integrations/elks_voice.py`; needs 46elks account + dialed-number config |
| 46elks SMS | 🔌 | `integrations/elks_sms.py` |
| Fortnox (OAuth + customer sync, KMS-encrypted refresh tokens) | 🔌 | `integrations/fortnox.py`; needs Fortnox developer app |
| Visma eEkonomi (OAuth + customer sync) | 🔌 | `integrations/visma_eekonomi.py` |
| Google Calendar (OAuth + bidirectional events) | 🔌 | `integrations/google_calendar.py` |
| Stripe Billing (Checkout + Portal + webhook + plan-aware ingress gate) | 🔌 | `integrations/stripe_billing.py` |
| Hantverksdata Next | ⏸ | partneravtal-gated; ~2–4 mo lead time |
| Bolagsverket org-number lookup | ⏸ | not started |

### Observability

| Surface | Status |
|---|---|
| Per-call structured trace (`firma_id`, `call_id`, `gemini_session_id` bound) | ✅ |
| Sentry (FastAPI integration, only initialized when DSN set) | 🔌 |
| Cost telemetry per call (Vertex tokens × rate + 46elks minutes + SMS) | ✅ |
| Per-tool latency SLO (p50/p95/p99 + breach detection) | ✅ |

### Tests

54 backend tests under `backend/tests/`. Cover: triage rules, ROT
eligibility truth table, audio round-trip, Pydantic round-trip,
multi-tenant context guards, audit-service refusal-without-context,
storage isolation + path-traversal rejection, recording finalization,
tool dispatch (local + HTTP), eval pipeline, redaction patterns, post-call
agent, onboarding bootstrap (returning + new + domain-blocked), tenant
erasure (dry-run + full).

---

## Web (Next.js 15, React 19, TypeScript, Tailwind v4)

Lives in `web/`. Standalone build for Cloud Run (`output: "standalone"`).

| Surface | Status |
|---|---|
| Nordic design tokens (warm off-white, deep forest accent, hairlines, no shadows — globally overridden) | ✅ |
| Owned UI primitives (Button, Card, Badge, Input, Label, Separator, Avatar, AudioPlayer) | ✅ |
| App shell (sidebar + topbar) | ✅ |
| `/inbox` with live WS reconciliation + react-query | ✅ |
| `/calls/[id]` (transcript, audio player, customer card, actions) | ✅ |
| `/bookings` (week-grid mock) | ✅ |
| `/customers` (list + search) | ✅ |
| `/settings` (firma + greeting + integrations cards) | ✅ |
| `/onboarding` (6-step concierge wizard scaffold) | ✅ |
| `/login` (NextAuth Google sign-in) | ✅ |
| Generated TypeScript types from backend OpenAPI | ✅ |
| react-query providers + typed hooks | ✅ |
| Live inbox WebSocket subscriber with backoff reconnect | ✅ |
| Production build (`pnpm build`) | ✅ green |

---

## Infrastructure

### Containers

| File | Purpose |
|---|---|
| `backend/Dockerfile.app` | Application Backend, runs `alembic upgrade head` then uvicorn |
| `backend/Dockerfile.bridge` | Realtime Bridge, ffmpeg baked in for MP3 encoding |
| `web/Dockerfile` | Next.js standalone on distroless `nodejs22-debian12` |

### Terraform (`terraform/`)

Cost-efficient single-region (`europe-west4`) deploy at ~80–100 SEK-equivalent/mo for pre-pilot.

| Module | Status |
|---|---|
| `project` (15 APIs + Artifact Registry) | ✅ |
| `network` (VPC + subnet + Serverless VPC Access connector + service-networking peering) | ✅ |
| `postgres` (Cloud SQL Postgres 16, `db-custom-1-3840`, private IP, 7-day PITR) | ✅ |
| `storage` (KMS keyring; per-tenant CryptoKey created at firma onboarding) | ✅ |
| `secrets` (Secret Manager skeleton) | ✅ |
| `workload_identity` (GitHub OIDC pool + provider + 2 service accounts with least-privilege roles) | ✅ |
| `cloud_run` (reusable per service: min/max instances, env, secret-mount, domain mapping) | ✅ |

Top-level `envs/prod/main.tf` orchestrates the two Cloud Run services
(svarsa-app at min=0, switchboard-bridge at min=2 per PRD §8.10) with
the right env shape per service.

### CI/CD

| Workflow | Trigger | Purpose |
|---|---|---|
| `.github/workflows/ci.yml` | every push/PR | ruff + pyright (warn-only) + pytest on SQLite + Alembic upgrade against ephemeral Postgres + web typecheck + web build |
| `.github/workflows/deploy-app.yml` | push to main, paths `backend/**` | build → push → Cloud Run rolling deploy |
| `.github/workflows/deploy-bridge.yml` | manual dispatch | build → push → canary 5% → 25% → 100% over 30 min |
| `.github/workflows/deploy-web.yml` | push to main, paths `web/**` | build → push → Cloud Run rolling deploy |
| `.github/workflows/eval-weekly.yml` | Sunday 06:00 UTC + manual | runs eval pipeline, posts Slack digest, fails on accuracy regression or any emergency false-negative |

Workload Identity Federation, no JSON keys.

---

## Documentation (`docs/`)

All currently in tree:

- `README.md` — index
- `architecture.md` — system map, hosting, deploy discipline, failure isolation, risks
- `backend.md` — module conventions, type discipline, tenant context patterns
- `frontend.md` — design tokens table, component patterns, Nordic rules (no shadows)
- `data-model.md` — table reference + ER + multi-tenancy notes
- `tools.md` — per-tool catalog reference
- `multi-tenancy.md` — five-layer isolation policy
- `realtime-bridge.md` — protocol, audio pipeline, lifecycle, latency budget
- `gcp-setup.md` — first-time GCP bootstrap (project, Terraform state, secrets, migrations, image push, DNS, GitHub Actions)
- `deployment.md` — steady-state runbook, rollback, secrets rotation, observability filters, SLO targets, tenant erasure
- `auth.md` — NextAuth + JWKS flow + dev-header shim
- `recording.md` — pipeline lifecycle, per-tenant isolation, retention, signed URLs
- `integrations.md` — per-provider setup steps for 46elks, Vertex, Fortnox, Visma, Google Calendar, Stripe, Hantverksdata
- `migrations.md` — Alembic commands + two-phase forward-only discipline
- `eval.md` — dataset format, weekly digest, regression investigation
- `current-state.md` — this file

Plan files were removed in commit `[remove-plans]` since they had drifted
from reality. Add new feature ideas as GitHub issues, not plan documents.

---

## What blocks production launch

1. **GCP project provisioning** — Terraform applies cleanly; needs founder credentials + billing.
2. **Domain DNS** — `switchboard.se` (or final brand domain) → Cloud Run domain mapping records.
3. **46elks production account** — number provisioning, Voice URL config, sender id verification (3–5 business days).
4. **Google OAuth client** — for NextAuth + Calendar.
5. **Stripe account + Products/Prices** — Starter/Professional/Premium recurring monthly prices in the dashboard, ids set in env.
6. **Fortnox developer account approval** — 1–3 business days; first pilot firma's OAuth consent.
7. **Eval dataset** — 500 labeled Swedish calls. Sample shipped at `backend/eval/sample.jsonl`; expand from pilot history.
8. **Legal sign-off** — DPA, sub-processor list, recording-consent disclosure copy reviewed by counsel.

Each item is documented in [`gcp-setup.md`](./gcp-setup.md) and [`integrations.md`](./integrations.md). No code changes required — flip env vars, run Terraform, push to main, deploy.

---

## Active branches and recent commits

```
$ git log --oneline -10  (run yourself for the latest)
```

Use `git log --oneline` for the canonical activity log; this doc is
intentionally stable.

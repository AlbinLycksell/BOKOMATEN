# Architecture

## System map

```
                                                  ┌──────────────────────┐
                                                  │ Gemini 3.1 Flash     │
                                                  │ Live API (EU)        │
                                                  └──────────▲───────────┘
                                                             │
                                                       PCM 16kHz in
                                                       PCM 24kHz out
                                                       JSON tool calls
                                                             │
┌──────────┐   PSTN   ┌──────────────┐   WebSocket   ┌──────▼──────────┐
│  Caller  │◄────────►│ 46elks (SE)  │◄─────────────►│ Realtime Bridge │
│  (Inger) │  G.711   │ or Twilio    │ G.711 μ-law   │ FastAPI · uvicorn│
└──────────┘  μ-law   │              │ 8kHz mono     │ - audio xcode   │
              8kHz    └──────────────┘  base64       │ - tool router   │
                                                     │ - barge-in      │
                                                     └──────┬──────────┘
                                                            │
                                                            ▼
                                       ┌─────────────────────────────────────────┐
                                       │ Backend services (single deployable)    │
                                       │ - Tool dispatch                          │
                                       │ - Owner REST + WS API                    │
                                       │ - Post-call agent (ADK)                  │
                                       │ - Notification (SMS/email — stubbed)     │
                                       │ - Persistence (SQLModel + Postgres)      │
                                       └────────────────┬────────────────────────┘
                                                        │
            ┌──────────────┬──────────────┬─────────────┼────────────┐
            ▼              ▼              ▼             ▼            ▼
        Fortnox       Hantverksdata   Visma         Google       46elks SMS
        (mock)        Next (mock)     (mock)        Calendar     (stub)
                                                    (mock)
```

The owner-facing dashboard (Next.js) talks REST + WebSocket to the same backend.

## Service responsibilities

| Service | Owns |
|---|---|
| **Realtime Bridge** (`backend/src/svarsa/bridge/`) | μ-law ↔ PCM transcoding, Gemini Live session lifecycle, tool dispatch, transcript persistence, post-call summary scheduling. |
| **Tool catalog** (`tools/`) | The 12 typed function declarations the AI calls. Each tool is a Pydantic args + result model and a thin handler routing to a service. |
| **Services** (`services/`) | Pure-ish business logic — triage rules, customer lookup, booking, escalation, ROT eligibility. No FastAPI imports here; testable in isolation. |
| **Owner API** (`api/`) | REST routes for the dashboard (calls, customers, firma settings) plus a live inbox WebSocket. Pydantic schemas are the OpenAPI source of truth. |
| **Post-call agent** (`agents/`) | ADK LlmAgent (real path) + heuristic fallback. Runs after `Call.ended_at` is set; writes a structured `CallSummary` back to the row. |
| **DB layer** (`db/`, `models/`) | SQLModel tables. SQLite in dev, Postgres in prod. JSON columns for nested settings/summaries. |

## Hot path vs. cold path

Two distinct latency regimes.

**Hot path** (per-call, p50 budget 1.2 s, p95 2.0 s): caller speech → Gemini → caller ear. Implemented in `bridge/`. Direct `google-genai` SDK; ADK is **not** used here — its abstractions add latency we cannot afford.

**Cold path** (post-call): summary, classification, escalation reconciliation. Implemented in `agents/post_call_summary.py`. ADK fits here — typed tools, evaluation hooks, multi-agent fan-out for future work (eval, trainer-feedback).

## Data residency

EU-only. Vertex/Gemini endpoints in `europe-west4`. Cloud SQL/GCS planned in same region. 46elks is Swedish-hosted by design. Twilio is the fallback for international and explicitly disclosed in the DPA.

## MVP gaps (deferred surfaces)

Tracked for transparency. Each one is intentionally not in the foundation commit.

1. **Telephony provider adapters.** The bridge speaks a provider-agnostic frame protocol (`{event,payload}`). Real 46elks `<Stream>` and Twilio `<Stream>` adapters wrap that. PRD Phase 1.
2. **Real OAuth integrations** (Fortnox, Hantverksdata, Visma, Google Calendar). Service interfaces exist, mock implementations populate the data path. Each becomes a real client per integration partner agreement.
3. **Auth.** API uses an `X-Firma-Id` header for dev. Replace with OAuth or NextAuth-issued JWT before pilot.
4. **Migrations.** SQLModel `create_all` is fine for SQLite dev. Switch to Alembic before first prod write.
5. **Recording pipeline.** Transcription is persisted; raw audio capture + GCS upload + redaction is a follow-up.
6. **Mobile apps** (PRD §7.7). Web parity in Phase 3, native React Native after.
7. **Eval + prompt-tuning UI.** Listed in PRD §11 — Phase 1 closed-beta deliverable.
8. **CI/CD + Cloud Run / Vercel deploy.** Local-first MVP; pipelines come with production keys.

## Risks (carry-over from PRD §12)

We track these in the issue tracker, not just here:

- Gemini 3.1 Flash Live remains in preview at GA → fallback to 2.5 Native Audio + Vertex Enterprise reserved capacity.
- Hantverksdata partneravtal slip → Fortnox + generic webhook fallback unblocks launch.
- Triage false-negative on emergency → bias toward escalation, weekly held-out eval, hard ceiling 0.5%.
- GDPR incident → strict EU deployment, CMEK, pen-test pre-GA.

## Open questions

Ported from PRD §13 — none of these block the foundation commit.

- Voice library (single brand vs. per-firma choice).
- Recording consent default (opt-in vs. opt-out, B2C vs. B2B).
- Pricing model (flat vs. hybrid vs. PAYG).
- Outbound proactive callbacks — when to enable.
- White-label tier threshold.
- Multi-firma rollup data model.

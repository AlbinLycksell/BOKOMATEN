# Architecture

## Service topology — two services + workers

Per PRD §2 and §8.10. Two long-lived services share a single Python codebase.

```
                                ┌──────────────────────┐
                                │ Gemini 3.1 Flash     │
                                │ Live API (EU)        │
                                └──────────▲───────────┘
                                           │ PCM 16k in / 24k out
                                           │ JSON tool calls
                                           │
┌──────────┐ PSTN ┌──────────────┐ WebSocket ┌──────▼──────────┐
│  Caller  │◄────►│ 46elks (SE)  │◄─────────►│ Realtime Bridge │
│ (Inger)  │ μ-law│ or Twilio    │ μ-law base│ Cloud Run        │
└──────────┘      │              │ 64        │ min-instances ≥ 2│
                  └──────────────┘           │ 60-min timeout   │
                                             │ weekly canary    │
                                             └──┬──────────────┘
                                                │ HTTPS over VPC
                                                │ POST /api/tools/dispatch
                                                ▼
                                ┌──────────────────────────────┐
                                │  Application Backend         │
                                │  Cloud Run                   │
                                │  hourly biz-hours deploys    │
                                │  organized by bounded ctx:   │
                                │   /customers /calls          │
                                │   /bookings /integrations    │
                                │   /notifications /billing    │
                                │   /admin                     │
                                └──────────────┬───────────────┘
                                               │
                                ┌──────────────▼───────────────┐
                                │ Worker pool                  │
                                │ Cloud Run Jobs +             │
                                │ Cloud Tasks queues           │
                                │ same codebase, diff entries  │
                                └──────────────────────────────┘
```

The Realtime Bridge holds telephony + Gemini WebSockets; the Application Backend holds tool handlers, domain logic, integrations, owner API. They are **separate Cloud Run services** so the Application Backend can deploy hourly without dropping live calls. Tool dispatch crosses the boundary over HTTPS on a private VPC connector.

In dev (single-deployable mode) both factories live in the same codebase — `switchboard.app:create_app` mounts everything; `switchboard.bridge_app:create_bridge_app` is the prod-shape factory. Tool dispatch in dev defaults to in-process; in prod it's HTTP via `Settings.tool_dispatch_mode = "http"`.

## Service responsibilities

| Service | Owns | Source |
|---|---|---|
| **Realtime Bridge** | Telephony + Gemini WebSockets, μ-law↔PCM transcoding, session resumption, barge-in, **calls Application Backend over HTTPS for tools**. Stateless except in-flight call state. | `bridge/`, `bridge_app.py` |
| **Application Backend** | Tool handlers, domain services, integrations, notifications, owner REST/WS API, admin/billing. Internally organized by bounded context with public-interface-only cross-context calls so a future split is mechanical. | `api/`, `services/`, `tools/`, `agents/`, `app.py` |
| **Workers** | Post-call summarization, weekly digest, integration syncs, eval pipeline. Cloud Run Jobs for scheduled, Cloud Tasks for retried mutations. Same codebase, different entrypoints. | `agents/`, future `workers/` |

## Hot path vs. cold path

**Hot path** (per-call, p50 1.2 s / p95 2.0 s budget, PRD §15): caller speech → Gemini → caller ear. Implemented in `bridge/`. Direct `google-genai` SDK; ADK is **not** used here — its abstractions add latency we cannot afford.

**Cold path** (post-call, async): summary, classification, escalation reconciliation, weekly digest. Implemented in `agents/post_call_summary.py`. ADK fits here — typed tools, eval hooks, multi-agent fan-out for future work.

## Hosting topology (PRD §8.10)

| Layer | Choice |
|---|---|
| Cloud | GCP, EU regions only — Vertex Live latency to Sweden is the binding constraint. |
| Primary region | `europe-west4` (Netherlands). |
| DR region | `europe-north1` (Finland). Not active-active at launch; warm-standby. |
| Realtime Bridge | Cloud Run, min-instances ≥ 2, 60-min request timeout. **Non-negotiable** — cold-starting Python+FastAPI when a phone is ringing means 2–3 s of dead air. |
| Application Backend | Cloud Run, min-instances 1 off-hours / 2–4 business hours, autoscale on request rate. |
| Workers | Cloud Run Jobs + Cloud Tasks queues. No persistent worker fleet. |
| Postgres | Cloud SQL, single primary + read replica, EU. Start `db-custom-2-8`. |
| Redis | Memorystore, single small instance, region-local. |
| Recordings | Per-tenant GCS bucket, per-tenant CMEK keys (PRD §8.9). |
| Secrets | Secret Manager (platform-level) + per-tenant DEK-wrapped tokens in Postgres (tenant-level). |
| Networking | Private VPC, mTLS for inter-service. Bridge ↔ Backend over VPC connector, never public internet. External webhooks terminate at Cloud Armor + WAF + per-tenant rate limits. |
| Observability | Sentry (EU) + Cloud Logging + Cloud Monitoring. **Resist Datadog/New Relic until ~30 MSEK ARR.** |

## Deployment discipline (PRD §8.10)

- **Application Backend deploys hourly during business hours** via GitHub Actions → Cloud Build → Cloud Run. Tool calls are short HTTPS round-trips; transparent retry handles the deploy window.
- **Realtime Bridge deploys weekly (Sunday 04:00 CET)** with traffic-splitting canaries (5 % → 25 % → 100 % over 30 min). Rollback is gated on p95 audio latency and error rate.
- **DB migrations are forward-only, two-phase**: deploy code that tolerates both schemas → migrate → deploy code that uses new schema only. No coordinated rollouts.

## Failure isolation (PRD §8.10)

A Realtime Bridge pod crash kills its 10–50 in-flight calls. **We do not migrate active call state.** Distributed audio session state is hard, the failure mode is rare with `min_instances ≥ 2`, and graceful redial is the pragmatic choice. Application Backend pod crashes are invisible: the Bridge transparently retries the failing tool call, the dashboard reconnects.

## Multi-tenancy

Shared platform, logical isolation, defence in depth across five layers. See [`multi-tenancy.md`](./multi-tenancy.md) for the full policy.

Foundation commit ships:

- Tenant context bound at request entry (`core/middleware.py`, `core/tenant.py`)
- structlog auto-tags `firma_id` on every log line
- `firma_id` on every tenant-scoped table (incl. redundant on `tool_invocation`)
- `audit_log` table + `services.audit_service.record()` that refuses to write without a tenant context
- Bridge ↔ Backend boundary respects the tenant scope (forwarded as `X-Firma-Id` + verified against `X-Internal-Token`)

Production gaps (deferred): Postgres RLS hookup, repository linting, per-tenant GCS buckets (when recording pipeline lands), real OAuth.

## Per-call structured tracing (PRD §8 update)

Every call binds three contextvars at the bridge entry: `firma_id`, `call_id`, `gemini_session_id`. structlog merges them into every log line, so a single Cloud Logging filter `call_id="01J..."` returns the entire per-call trace: ingress event, audio transcoding latencies, every tool call (name, latency, ok/error), recording write, transcript publish.

Aggregated dashboards (Cloud Monitoring): p50/p95/p99 audio latency, calls/minute, function-call latency by tool, error rate by integration. Tool-latency SLO is 200 ms p95 (PRD §8.4).

## Risks register (PRD §12 — current cut)

| Risk | Impact | Probability | Mitigation |
|---|---|---|---|
| Gemini 3.1 Flash Live preview at GA | High | Medium | Vertex Enterprise reserved capacity, fallback to 2.5 Native Audio, abstracted LLM provider. |
| Hantverksdata partnership delay | High | Medium | Parallel Fortnox + Visma; generic webhook fallback. |
| **Hantverksdata partners with a competitor** | High | Medium | Phase 0 partnership conversations + concrete demo, build VVS-on-Hantverksdata customer base for inbound pressure, monthly job-posting monitoring. |
| **Hantverksdata or Fortnox builds in-house** | High | Low–Medium | Constellation playbook is buy-not-build; speed of execution is the only real defence. |
| **Demand hypothesis wrong** | High | Low–Medium | Phase 0 validation memo (Appendix C of PRD) gates Phase 1 build. |
| Triage false-negative on emergency | Catastrophic | Low | Bias toward escalation, weekly held-out eval, hard ceiling 0.5 %. |
| GDPR + cross-tenant data leak | Catastrophic | Low | EU-only deploy, CMEK, RLS, repository discipline, pen-test pre-GA. |
| Caller-experience "creepy AI" | High | Medium | Tonality eval in focus groups, barge-in working, smooth handoff. |
| **Premature architecture scaling** | Medium | Medium | Two-services-plus-workers ceiling until 30+ MSEK ARR; bounded-context modules in monolith preserve future split optionality. |

## Open questions (PRD §13)

Voice library, recording consent default, pricing model, outbound proactive callbacks, white-label tier, multi-firma rollup data model. None gate the foundation commit.

## MVP gaps (deferred surfaces)

1. Real telephony adapters (46elks `<Stream>` / Twilio `<Stream>`).
2. Real OAuth integrations (Fortnox, Hantverksdata, Visma, Google Calendar).
3. OAuth/JWT auth — currently `X-Firma-Id` dev header.
4. Alembic migrations — currently `create_all` against SQLite.
5. Recording capture + per-tenant GCS pipeline.
6. Mobile apps (Phase 3 in PRD).
7. Eval + prompt-tuning UI (Phase 1 deliverable).
8. Cloud Run deploy + Terraform.

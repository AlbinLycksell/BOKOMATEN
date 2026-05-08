# Svarsa AI — Next-Steps Implementation Plan

**Status:** Draft for review
**Last updated:** 2026-05-09
**Author:** Founding eng
**Predecessor plan:** [`2026-05-09-svarsa-mvp-foundation.md`](./2026-05-09-svarsa-mvp-foundation.md) (complete)

---

## How to read this plan

The MVP foundation is in `main`. This plan lists what to build next, in priority order, to reach the PRD's Phase 1 closed-beta gate (n=8–12 pilot firmor, ≥85 % triage accuracy, 0 GDPR incidents).

Each step is a self-contained increment of work — roughly a 1–2 person-week sprint — with:

- **Goal** — one sentence describing the deliverable.
- **Why now** — what depends on this and why it can't wait.
- **Required input** — concrete things needed before kickoff (credentials, decisions, partner sign-off, pilot data). If any are missing, the step is blocked.
- **Depends on** — earlier steps that must complete first.
- **Deliverable** — what the merge contains.
- **Acceptance** — how we know it's done.

Steps are tiered by milestone. Inside a tier, ordering is suggested but not strict — independent steps can run in parallel if staffing allows.

---

## Tier 1 — First real call end-to-end (weeks 1–3)

The foundation handles a synthetic provider; this tier flips on the real PSTN side.

### Step 1 · 46elks telephony adapter

- **Goal:** A real Swedish phone number rings → bridge picks up → AI answers in Swedish → caller hears AI → tools execute → call ends with a persisted `Call` row.
- **Why now:** Without this, the entire product is unverifiable. Every other tier-1 step gates on having a real call to test against.
- **Required input:**
  - 46elks production account (Founders to sign up; ~30 min)
  - 46elks API key (`VOICE_PROVIDER_46ELKS_API_KEY`)
  - One Swedish E.164 number, owned or porta-in (~SEK 39/mån, ~5 min in dashboard)
  - Decision: which firma id the test number routes to (use seeded `01J0000FIRM0ANDERSSONSVVS00` for dev)
  - Public HTTPS URL for the bridge (`ngrok` for dev, Cloud Run domain for prod)
- **Depends on:** Foundation. No predecessors.
- **Deliverable:**
  - `backend/src/svarsa/integrations/elks_voice.py` — adapter that maps 46elks Voice Streaming framing (`{event:"start|sound|hangup"}`) into the bridge's normalized `{event,payload}` protocol.
  - `backend/src/svarsa/api/routes_elks.py` — webhook endpoint returning the `voice_start` JSON pointing at our `wss://…/ws/bridge/{firma_id}/{call_id}`.
  - Provider-specific tests with a recorded media stream fixture.
  - `docs/realtime-bridge.md` updated with 46elks specifics.
- **Acceptance:**
  - Call to the test number completes a 30-second round-trip with audible Swedish replies.
  - Per-call structured trace in Cloud Logging shows `firma_id`, `call_id`, `gemini_session_id`.
  - At least one tool call (e.g. `lookup_customer`) fires and returns to Gemini.
  - `Call` row persists with non-null `started_at`, `ended_at`, intent, and at least 5 transcript segments.

### Step 2 · Real Gemini Live smoke + latency budget validation

- **Goal:** Confirm the PRD §15 latency budget on real audio (p50 < 1 200 ms, p95 < 2 000 ms) with a recorded eval set of 10 representative calls.
- **Why now:** The whole product hinges on the latency claim. We need to measure once we can drive the bridge with real audio (Step 1).
- **Required input:**
  - Step 1 working.
  - 10 representative recorded Swedish caller utterances spanning: vattenläcka emergency, OVK booking, offert request, befintlig-kund-fråga, dialect samples (skånska, göteborgska, finlandssvenska). Founders or first pilot firma to record (~2 hours).
  - Decision: Vertex AI vs `generativelanguage.googleapis.com` endpoint. PRD §8.3.1 says Vertex `europe-west4` for residency. Need GCP project with Vertex AI enabled.
  - GCP project id + service account with Vertex AI User role (`SVARSA_GCP_PROJECT`).
- **Depends on:** Step 1.
- **Deliverable:**
  - `backend/src/svarsa/bridge/gemini_session.py` updated to support Vertex AI (currently uses `v1beta` API key path).
  - `backend/scripts/latency_eval.py` — replays the 10 recordings through the bridge, measures end-to-end timing per stage, writes a CSV.
  - `docs/realtime-bridge.md` updated with measured numbers next to PRD targets.
- **Acceptance:** All 10 calls complete, p50/p95 inside PRD §15 budget. If they're not, decisions about model swap (Gemini 2.5 Native Audio fallback) get raised before further work.

### Step 3 · OAuth/JWT auth (replace `X-Firma-Id`)

- **Goal:** The dashboard authenticates a real human user; backend resolves `firma_id` from the verified session, not a header.
- **Why now:** Tier 2 steps (Recording, Fortnox OAuth, Cloud Run deploy) are unsafe to ship without real auth.
- **Required input:**
  - Decision: identity provider. Options: NextAuth.js (Google + email magic-link), Auth0, Clerk, or rolled-in (Authlib + Postgres). Recommendation: NextAuth.js with Google for owners (most hantverkare have a Google Workspace) + email magic-link fallback.
  - Google OAuth client_id + secret (5 min in GCP console once GCP project is set up).
  - Decision: session model — JWT in cookie (default for NextAuth), or backend session store. Recommendation: JWT signed by NextAuth, backend verifies via JWKS.
  - Decision: how a User row maps to a Firma — `User.firma_id` (single-firma per user) is in the foundation; multi-firma per user (PRD §13 open question) is deferred.
- **Depends on:** Foundation; can run parallel to Step 1.
- **Deliverable:**
  - `web/app/(auth)/login/page.tsx`, NextAuth config in `web/app/api/auth/[...nextauth]/route.ts`.
  - `backend/src/svarsa/core/auth.py` — JWKS verification, replaces `TenantMiddleware` dev path with header-injection from a verified JWT.
  - `User`-aware deps (`get_current_user`, `get_current_firma`) on backend.
  - Migration: dashboard switches from `X-Firma-Id` to bearer-token + cookie.
- **Acceptance:**
  - Logging in with Google lands on `/inbox`.
  - All API routes reject anonymous requests with 401.
  - `audit_log` rows now have a real user id in `actor`, not `"system"`.

### Step 4 · Alembic migrations + Postgres swap

- **Goal:** Backend runs against Cloud SQL Postgres; schema changes go through Alembic with the two-phase forward-only discipline (PRD §8.10).
- **Why now:** First prod write must hit Postgres, not SQLite. Migration discipline must exist before then.
- **Required input:**
  - GCP project id (also needed for Step 2).
  - Decision on initial Cloud SQL tier (PRD §8.10 says `db-custom-2-8`).
  - Cloud SQL admin credentials for the bootstrap (then app runs as low-privilege role for RLS).
  - Decision: keep SQLite for local dev, or use Postgres in Docker for parity? Recommendation: keep SQLite for fast iteration, run an integration-test job against ephemeral Postgres in CI.
- **Depends on:** Foundation; runs parallel to Steps 1–3.
- **Deliverable:**
  - `backend/alembic/` directory + initial migration capturing the foundation schema.
  - `backend/src/svarsa/db/postgres.py` — connection pool, low-privilege role, `SET app.firma_id` per-checkout hook.
  - CI job: spin up Postgres in a service container, run migrations, run `pytest` against it.
  - `docs/data-model.md` updated with migration commands.
- **Acceptance:**
  - `make migrate` applies all migrations cleanly.
  - `pytest` passes against Postgres in CI (not just SQLite locally).
  - A no-op alembic revision can be reverted then re-applied.

---

## Tier 2 — Production readiness (weeks 3–6)

Tier 1 unblocks one call. Tier 2 unblocks the platform.

### Step 5 · Recording capture pipeline (per-tenant GCS)

- **Goal:** Every call's audio (both legs) is captured, encoded MP3, written to a per-tenant GCS bucket with CMEK and a 7-day default TTL. Dashboard `AudioPlayer` plays a real recording via signed URL.
- **Why now:** PRD §7.6 requires recording for owner review. PRD §8.9 requires per-tenant bucket isolation. Cannot ship to pilots without this.
- **Required input:**
  - GCP project + billing.
  - Decision: per-firma bucket creation timing. Options: lazy (on first call), eager (on firma onboarding). Recommendation: eager — onboarding step creates `gs://svarsa-rec-{firma_id}-eu` with CMEK from `projects/{p}/locations/europe-west4/keyRings/svarsa/cryptoKeys/firma-{id}`.
  - Decision: encoding — MP3 (smaller, lossy, plays everywhere) vs Opus (smaller still, requires modern player). Recommendation: MP3 for owner playback, Opus archival.
  - Per-firma retention default (PRD §9.6 says 7 days; firma can extend).
- **Depends on:** Steps 1, 3, 4 (auth + Postgres + real call audio).
- **Deliverable:**
  - `backend/src/svarsa/services/recording_service.py` — buffers audio per call, writes MP3 to GCS on call end, generates signed URL on demand.
  - `backend/src/svarsa/integrations/gcs.py` — bucket lifecycle, CMEK, signed URLs.
  - Wire into `bridge/ws.py` so both legs are captured (caller via μ-law, AI via PCM 24kHz down-mixed).
  - `Call.recording_url` populated; dashboard plays via signed URL with 1h expiry.
- **Acceptance:**
  - Call ends → MP3 lands in firma's bucket within 5s.
  - Dashboard plays the recording from the call detail page.
  - 7-day TTL configured on the bucket; verified by a test object that gets pruned.
  - Cross-firma access is denied (negative test with mismatched firma id).

### Step 6 · Outbound SMS via 46elks SMS API

- **Goal:** `notification_service.send_sms(...)` actually sends an SMS through 46elks instead of just logging.
- **Why now:** PRD §6.1 (emergency_ack), §6.2 (booking confirmation), §6.4 (Lena's morning summary) all depend on real SMS. Pilot owners won't trust the system without it.
- **Required input:**
  - 46elks SMS plan + sender id (`SVARSA` sender or per-firma alias). 46elks supports custom sender ids with verification.
  - SMS templates in Swedish, signed off by Founders. Drafts in PRD §6 — needs final wording per template.
  - Decision: per-firma sender id or platform sender id? Recommendation: per-firma alias once verified; platform fallback while verifying.
- **Depends on:** Step 1 (46elks account).
- **Deliverable:**
  - `backend/src/svarsa/integrations/elks_sms.py` — POST to `https://api.46elks.com/a1/SMS`.
  - Template resolution in `services/notification_service.py` (5 templates from PRD §8.4.7).
  - Per-firma SMS event log in `audit_log` (`action="sms.sent"`).
  - Smoke test against a Founders' personal number.
- **Acceptance:**
  - End-to-end emergency call triggers SMS to owner phone within 15 s of "läcka" detection.
  - Failed SMS delivery is retried up to 3× via Cloud Tasks and logged.
  - Per-firma sender id verified in 46elks dashboard.

### Step 7 · Fortnox integration (real OAuth)

- **Goal:** Replace mocked customer + calendar service with real Fortnox API calls scoped per firma.
- **Why now:** Half the pilot pool runs Fortnox. PRD §11.2 names Fortnox as Phase 1's first real integration.
- **Required input:**
  - Fortnox developer account + partner application (~2 days, Founders).
  - OAuth client_id + secret (`SVARSA_FORTNOX_CLIENT_ID`, `_SECRET`).
  - Pilot firma consent — at least one firma running Fortnox who signs the OAuth flow during onboarding.
  - Decision: which Fortnox endpoints to surface in v1. Recommendation: `Customers` (read+write), `Invoices` (read), `BookingsCalendar` (if firma uses Fortnox kalender). Defer faktureringar.
- **Depends on:** Steps 3 (auth so OAuth callback resolves a user), 4 (Postgres for token storage).
- **Deliverable:**
  - `backend/src/svarsa/integrations/fortnox.py` — typed client wrapping the relevant endpoints.
  - Per-tenant DEK-encrypted token storage in `Integration.sync_state`.
  - 60-second polling for customer + calendar deltas.
  - Settings page → Integrations card → "Anslut Fortnox" actually completes OAuth.
- **Acceptance:**
  - Pilot firma connects in <2 minutes from settings page.
  - `lookup_customer` finds a real Fortnox customer.
  - Booking made via AI lands in Fortnox kalender within 60s.
  - Token refresh flows transparent (no re-consent needed).

### Step 8 · Cloud Run deploy + GitHub Actions CI/CD

- **Goal:** Pushing to `main` deploys Application Backend to Cloud Run within 10 min; pushing a tagged release to `bridge-*` deploys Realtime Bridge with canary.
- **Why now:** Cannot run pilots from a laptop. PRD §8.10 specifies separate Cloud Run services per the deploy-cadence split.
- **Required input:**
  - GCP project ready (Steps 2, 4).
  - GitHub Actions repo secrets: `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_SERVICE_ACCOUNT`.
  - Cloud Build → Artifact Registry repo set up (10 min in console).
  - Domain: `app.svarsa.se` for backend, `bridge.svarsa.se` for bridge. Founders to register if not done.
  - Decision: Terraform now or later? Recommendation: Terraform now — `terraform/` directory holds Cloud Run, Cloud SQL, GCS buckets, Cloud Tasks queues.
- **Depends on:** Steps 1, 3, 4, 5.
- **Deliverable:**
  - `Dockerfile` per service (`backend/Dockerfile.app`, `backend/Dockerfile.bridge`).
  - `.github/workflows/deploy-app.yml`, `deploy-bridge.yml`.
  - `terraform/` skeleton: project, networking, Cloud Run services, Cloud SQL, GCS, Secret Manager, Cloud KMS keyring.
  - `docs/deployment.md` — deploy ops handbook.
- **Acceptance:**
  - Merge to main → Application Backend rolls out, health check passes.
  - Manual `gh workflow run deploy-bridge.yml` triggers canary 5 % → 25 % → 100 % over 30 min.
  - Rollback works (`gcloud run services update-traffic --to-revisions=…`).

### Step 9 · Postgres RLS wiring

- **Goal:** Every tenant-scoped query at runtime is policy-blocked from cross-tenant reads, even if a developer forgets `WHERE firma_id = ...`.
- **Why now:** Defence in depth. PRD §8.9 makes this non-negotiable for GA. Cheaper to wire when the table list is small.
- **Required input:**
  - Step 4 complete (Postgres in CI + dev).
  - Decision: low-privilege application role name + grant template. Recommendation: `svarsa_app` role, owner of nothing, `GRANT SELECT, INSERT, UPDATE, DELETE` on tenant-scoped tables, no `BYPASSRLS`.
- **Depends on:** Steps 4, 8.
- **Deliverable:**
  - Alembic migration adding `ENABLE ROW LEVEL SECURITY` + `CREATE POLICY firma_isolation` for every tenant-scoped table.
  - `db/postgres.py` calls `SET app.firma_id = …` per connection checkout.
  - Negative test: query under tenant A using a wrong firma id returns no rows even on direct SQL.
- **Acceptance:**
  - Pen-test scenario: a SQL injection that omits the firma predicate still returns no cross-tenant data.
  - All 35 backend tests pass under RLS.

### Step 10 · Live inbox WebSocket — wire frontend to backend

- **Goal:** New calls and call-status changes appear in the dashboard without refresh.
- **Why now:** Owners' first impression depends on it. The backend WS exists; the frontend doesn't subscribe.
- **Required input:**
  - Decision on optimistic-update strategy when a tool action fires from the dashboard (e.g. "Markera hanterad"). Recommendation: optimistic + reconcile via WS event.
- **Depends on:** Step 3 (auth so the WS can authenticate the firma).
- **Deliverable:**
  - `web/lib/inbox-ws.ts` — typed wrapper around the WS.
  - `web/app/(app)/inbox/page.tsx` becomes a client boundary that subscribes; server still hydrates the first page.
  - Toast notification on incoming "akut" calls.
- **Acceptance:**
  - With two browser windows open and the pilot phone calling the test number, both inboxes show the new row within 1 s of `Call.started_at`.

---

## Tier 3 — Closed beta requirements (weeks 6–10)

These earn the Phase 1 launch (PRD §11.2).

### Step 11 · Eval pipeline + triage accuracy gating

- **Goal:** Weekly automated eval over 500 held-out Swedish calls reports triage accuracy per intent + emergency false-negative rate. CI fails if accuracy regresses below 85 % (PRD §11.2 goal).
- **Why now:** Without this, prompt or model changes are flying blind. Hard ceiling on emergency false-negatives is 0.5 %.
- **Required input:**
  - 500 recorded VVS calls with consent. Founders to harvest from 5 pilot firmor's 60 days of history (60 × 5 = 300 typical, padded with synthetic for edge cases).
  - Per-call ground-truth labels: intent, severity, expected actions. Manual annotation budget ~40 h.
  - Decision: eval framework. Recommendation: ADK eval support (`google.adk.evaluation`) since the tool catalog already lives in ADK shape.
- **Depends on:** Steps 1, 3.
- **Deliverable:**
  - `backend/src/svarsa/eval/` — dataset loaders, replay harness, metrics, report.
  - `.github/workflows/weekly-eval.yml` — runs Sunday 08:00, posts a summary to a Founders Slack.
  - `docs/eval.md` — how to add a labeled call, how to investigate a regression.
- **Acceptance:**
  - First eval run reports baseline numbers.
  - A deliberate prompt regression is caught (red CI).
  - Founder can read a per-call replay with the AI's chain of tool calls in a static HTML report.

### Step 12 · Concierge onboarding flow

- **Goal:** A new pilot firma signs up, picks a number, connects Fortnox, configures greeting, and answers a test call — all in <30 minutes.
- **Why now:** PRD §7.8 mandates a 30-min onboarding target. Without this, pilot expansion stalls.
- **Required input:**
  - Decision: voice library — single Svarsa voice or per-firma choice (PRD §13 open question). Recommendation: 3 default options (warm female, neutral male, energetic young) at launch.
  - Marketing copy in Swedish for each onboarding step. Founders to draft.
- **Depends on:** Steps 3, 6, 7, 8.
- **Deliverable:**
  - `web/app/(onboarding)/...` — multi-step flow: signup → number → integration OAuth → greeting wizard → eskaleringskedja → testringa → klart.
  - Backend orchestration: `services/onboarding_service.py` that creates Firma + provisions number via 46elks API.
  - `docs/onboarding.md` — operator playbook for concierge mode.
- **Acceptance:**
  - First pilot firma onboarded by a non-developer in under 30 minutes.
  - Test call from the firma's own phone reaches Magnus's mobile in <15 s.

### Step 13 · Recording PII redaction

- **Goal:** Personnummer-shaped sequences are masked in transcripts before they're stored or shown.
- **Why now:** PRD §9.5. Failure to redact a personnummer triggers an IMY incident path.
- **Required input:**
  - Decision: redaction strategy. Two options: (a) live in-stream regex over the running transcript (cheap, possible false-positives), (b) post-call diarization + entity extraction (better recall, adds 10–30 s of latency to summary). Recommendation: (a) live regex for instant masking + (b) post-call entity audit that flags any low-confidence misses.
- **Depends on:** Step 5.
- **Deliverable:**
  - `backend/src/svarsa/services/redaction_service.py`.
  - Hooked into `bridge/ws.py` before `_persist_text`.
  - Audit log row for every redaction event.
- **Acceptance:**
  - Test call with a fake personnummer pattern: transcript shows `[NN]NNNN-NNNN` redacted.
  - 0 false-negatives on a 100-call validation set with planted patterns.

### Step 14 · Hantverksdata Next integration

- **Goal:** Customers + arbetsorder + tekniker-resursplanering sync with Hantverksdata Next.
- **Why now:** Strategic moat (PRD §8.7.2). Phase 0 of the original PRD started this in June; the partner conversation runs in parallel to engineering.
- **Required input:**
  - Signed Hantverksdata partneravtal (Founders + legal, 2–4 month process per PRD).
  - Hantverksdata API credentials.
  - Decision on which Hantverksdata-running pilot firma is the integration design partner.
- **Depends on:** Step 7 (proves the integration shape).
- **Deliverable:**
  - `backend/src/svarsa/integrations/hantverksdata.py`.
  - Settings page card to connect.
  - Booking + customer sync semantics documented.
- **Acceptance:**
  - One Hantverksdata-running pilot firma connects and books a job from the AI.

### Step 15 · Visma + Google Calendar integration

- **Goal:** Cover the rest of the integration matrix (PRD §8.7.3, §8.7.4).
- **Why now:** ~30 % of pilot demand cluster runs Visma; Google Calendar serves the rest.
- **Required input:** Visma developer account + OAuth client; Google Calendar OAuth client (already covered if Step 3 used Google).
- **Depends on:** Step 7 (shape).
- **Deliverable:** `integrations/visma.py`, `integrations/google_calendar.py` + settings cards. Bidirectional sync on Calendar.
- **Acceptance:** Per-firma sync works for at least one firma per integration.

### Step 16 · Frontend polish for closed beta

- **Goal:** Dashboard feels production-grade — react-query for caching, virtualized inbox, audio scrubbing tied to transcript, accessibility pass, mobile-responsive.
- **Why now:** Lena (PRD §5.2) lives in this UI. If she abandons it, the firma cancels.
- **Required input:**
  - Founders' walkthrough notes from 2–3 pilot owners' first sessions.
  - Accessibility checklist (WCAG 2.1 AA target).
- **Depends on:** Steps 3, 5, 10.
- **Deliverable:**
  - `@tanstack/react-query` wired with optimistic updates.
  - Inbox virtualization (only when call count > 200).
  - Transcript ↔ audio cursor sync (hover-row scrubs to ts_ms_offset).
  - Keyboard nav, ARIA labels, focus management.
- **Acceptance:** Lighthouse mobile score ≥ 90, axe-core 0 critical issues.

---

## Tier 4 — GA / Phase 3 (Q4 2026 onward)

### Step 17 · Mobile apps (React Native, iOS + Android)

- **Goal:** Feature parity with the web dashboard, plus native push for emergency escalations (PRD §7.7).
- **Why now:** Owners are 80 % on a job site and have hands full (PRD §5.1). The web app is a stopgap.
- **Required input:**
  - Apple Developer account + team id (~$99/yr, 1–2 days for review).
  - Google Play developer account ($25 one-time).
  - Decision on the native push for "akut" escalations — does it bypass Do Not Disturb? (Apple critical alerts require a separate entitlement application, ~2 weeks).
- **Depends on:** Steps 3, 6, 8.
- **Deliverable:** `mobile/` — Expo + React Native, shared components where feasible.
- **Acceptance:** Emergency escalation push lands on owner's locked iPhone within 15 s.

### Step 18 · Multi-firma rollup

- **Goal:** A single owner can manage several AB:s under one login (PRD §13).
- **Why now:** Common pattern among Swedish hantverkare with separate AB:s per trade.
- **Required input:** Decision on plan-tier — multi-firma in Pro, or Premium-only?
- **Depends on:** Step 3, schema migration.
- **Deliverable:** `User ↔ Firma` becomes many-to-many; UI gets a firma-switcher in the topbar.
- **Acceptance:** Test owner with two firmor sees correct inbox per firma; cross-firma actions blocked.

### Step 19 · White-label theming

- **Goal:** Premium-tier firmor get firma-branded greeting, SMS sender id, and dashboard accent (PRD §13).
- **Required input:** Decision on tier threshold; brand asset upload UX.
- **Deliverable:** Per-firma theme tokens override `--color-accent`; greeting variables; SMS sender alias.
- **Acceptance:** Premium firma's dashboard looks visibly distinct; inbound SMS appears from their sender id.

---

## Cross-cutting workstreams (continuous, not gated)

### Validation research (PRD §16 / Appendix C)

- **Goal:** Phase 0 validation memo answers each demand-hypothesis with green/yellow/red before Phase 1 spends serious build budget.
- **Required input:**
  - 14-day call-tracking pilot with 10–15 friendly hantverkare (~5 kSEK + gift cards).
  - 30+ structured interviews with explicit willingness-to-pay laddering.
  - 5–8 bokföringsbyrå conversations, 2 branschorg meetings, 1 Hantverksdata meeting.
  - Public data triangulation: Skatteverket ROT-statistik, SCB SNI 43.21/43.22/43.39, Bolagsverket counts, Installatörsföretagen reports.
- **Owner:** Founders, not engineering. Engineering supports with the call-tracking pilot tooling (Step 1 is the substrate).
- **Acceptance:** Written memo signed by founders + 2–3 advisors before Phase 1 commits engineering to >50 % of capacity on closed beta.

### Risk monitoring

- **Goal:** Track PRD §12 risks proactively. Monthly review of Hantverksdata job postings (build-vs-partner signal); quarterly Vertex Live API roadmap check; weekly emergency false-negative rate sampled from the eval pipeline.
- **Owner:** Founding eng + Founders.

### Cost telemetry

- **Goal:** Per-call cost stays below 2.50 SEK median, 5 SEK p95 (PRD §3.1 goal 8).
- **Required input:** Vertex Live API GA pricing (currently preview-free), 46elks per-minute and per-SMS rates.
- **Deliverable:** Per-call cost row in the `Call` table, dashboard panel showing rolling 7-day median + p95.
- **Owner:** Wires in alongside Step 11 (eval pipeline).

---

## Summary of inputs by category

Consolidated from the steps above so they can be collected up front.

### Credentials / accounts to provision

| Item | Step | Owner |
|---|---|---|
| 46elks production account + API key | 1 | Founders |
| 46elks Swedish E.164 number | 1 | Founders |
| 46elks SMS sender id (verified) | 6 | Founders |
| GCP project + billing | 2 | Founders |
| GCP service account (Vertex AI User, Cloud Run admin) | 2, 8 | Founders |
| Google OAuth client_id + secret | 3 | Founders |
| Fortnox developer account + partner application | 7 | Founders |
| Hantverksdata partneravtal + API credentials | 14 | Founders + legal |
| Visma developer account + OAuth client | 15 | Founders |
| Apple Developer account ($99/yr) | 17 | Founders |
| Google Play developer account ($25) | 17 | Founders |
| Domain: `app.svarsa.se`, `bridge.svarsa.se` | 8 | Founders |
| GitHub Actions repo secrets (workload identity, SA) | 8 | Engineering |

### Decisions required

| Decision | Step | Recommendation |
|---|---|---|
| Identity provider for owner auth | 3 | NextAuth + Google + email magic-link |
| Session model | 3 | JWT cookie, JWKS-verified by backend |
| Multi-firma per user | 3 / 18 | Single in v1; multi in Premium tier later |
| SQLite local vs. Postgres in dev | 4 | Keep SQLite local; Postgres in CI |
| Recording encoding | 5 | MP3 for playback, Opus archival |
| Per-firma bucket creation timing | 5 | Eager at onboarding |
| Per-firma vs platform SMS sender id | 6 | Per-firma alias once verified |
| Fortnox endpoints in v1 | 7 | Customers, Invoices read, BookingsCalendar |
| Voice library scope | 12 | 3 default options; no clones at launch |
| PII redaction strategy | 13 | Live regex + post-call entity audit |
| Multi-firma plan-tier | 18 | Premium-only |
| White-label tier threshold | 19 | Premium-only |
| Recording consent default (B2B vs B2C) | (legal) | Disclosure-based opt-out for B2B; opt-in for B2C — confirm with legal pre-pilot |
| Outbound calling timeline | (regulatory) | Inbound-only at GA; revisit after 200 firmor |
| Pricing — flat vs hybrid vs PAYG | (commercial) | Hybrid as designed in PRD §10 |

### External data / artifacts to gather

| Artifact | Step | Source / owner |
|---|---|---|
| 10 representative recorded Swedish caller utterances | 2 | Pilot firmor with consent |
| 500 labeled Swedish calls for eval set | 11 | 5 pilot firmor's 60-day history |
| SMS template wording (5 templates) | 6 | Founders + UX writing |
| Onboarding copy in Swedish | 12 | Founders |
| Brand assets (logo, sender ids) | 19 | Founders |
| 10–15 friendly hantverkare for call-tracking pilot | Validation | Founders' network |
| 30+ structured interviews | Validation | Founders |

### Legal / compliance gates

| Gate | Step | Notes |
|---|---|---|
| DPA + sub-processor list signed | Pre-Step 5 | Recordings touch sensitive data |
| DPIA completed (Art. 35) | Pre-GA | Updated annually |
| Consent disclosure copy in Swedish reviewed | Pre-Step 1 | "Detta samtal kan spelas in…" |
| ROT-bedömning legal review | Step 7+ | Skatteverket terminology accuracy |
| Sender id verification with 46elks | Step 6 | ~3–5 business days |

---

## Suggested staffing & sequencing

If the team is one full-time engineer plus founders supporting on validation, integrations, and copy:

- **Weeks 1–3:** Steps 1, 3, 4 in parallel (eng can interleave; founders unblock auth provider + GCP).
- **Weeks 3–6:** Steps 2, 5, 6, 8 (Cloud Run by mid-tier so subsequent steps deploy automatically).
- **Weeks 6–10:** Steps 7, 9, 10, 11, 12 — closed-beta-ready surface.
- **Weeks 10+:** Steps 13–16, then Tier 4 work.

Validation research runs from week 1 in parallel; Hantverksdata partner conversation starts week 1 even though integration is week 8+.

---

## Document hygiene

- Edit this file inline as decisions land. Don't add a new doc per decision.
- When a step ships, mark it `Done · <commit-sha>` in the heading instead of deleting.
- New ideas that aren't on this list go into a `## Backlog` section at the bottom (none yet).

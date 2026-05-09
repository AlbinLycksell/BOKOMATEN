# Svarsa AI — Launch Readiness Plan

**Status:** Draft for review
**Last updated:** 2026-05-09
**Predecessor plans:**
- [`2026-05-09-svarsa-mvp-foundation.md`](./2026-05-09-svarsa-mvp-foundation.md) — complete
- [`2026-05-09-svarsa-next-steps.md`](./2026-05-09-svarsa-next-steps.md) — partly complete; this plan supersedes the open items

---

## What just shipped (carryover from production-posture work)

These items from the previous next-steps plan are now done in code; remaining work is **operational** (provisioning credentials, deploying, running smoke tests).

| Previous step | Status | Notes |
|---|---|---|
| Step 3 — OAuth/JWT auth | ✅ code | NextAuth + Google + JWKS backend; awaits live OAuth client |
| Step 4 — Alembic + Postgres + RLS | ✅ code | `alembic/versions/0001` + `0002`; awaits Cloud SQL |
| Step 5 — Recording pipeline | ✅ code | Per-tenant GCS storage + MP3 encode; awaits GCP deploy |
| Step 6 — Outbound SMS via 46elks | ✅ code | 5 Swedish templates wired; awaits 46elks creds |
| Step 8 — Cloud Run + Terraform | ✅ code | Modules + workflows; awaits `terraform apply` |
| Step 13 — PII redaction (live regex) | ✅ code | Live masking + audit log; post-call entity audit deferred |
| Vertex AI integration | ✅ code | Provider toggle; awaits Vertex enablement on the project |

**What's left to actually launch:** flip on real credentials, run the first deploy, prove the end-to-end loop with a real Swedish phone call.

---

## How to read this plan

Each step has:
- **Goal** — one-line outcome
- **Why now** — what milestone it unblocks
- **Required input** — credentials/decisions/data needed before kickoff
- **Depends on** — prior steps
- **Deliverable** — what the merge contains
- **Acceptance** — how we know it works

Tiered by milestone. Run independent steps in parallel if staffing allows.

---

## Tier A — Light up production (weeks 1–2)

The code is ready; this tier turns the keys.

### A1 · Provision GCP and run first deploy

- **Goal:** `https://app.svarsa.se/health` and `https://bridge.svarsa.se/health` return 200 from real Cloud Run services.
- **Why now:** Every other tier-A item depends on a live deploy.
- **Required input:**
  - **GCP project id** (recommend: `svarsa-prod`). Founders create at https://console.cloud.google.com/projectcreate. ETA 5 min.
  - **GCP billing account id** linked to the project.
  - **Domain access** for `svarsa.se` to add DNS records for `app` and `bridge` subdomains.
  - **Generated secrets** to populate Secret Manager: `bridge-internal-token`, `nextauth-secret`, `postgres app password`. ETA 1 min each (`openssl rand`).
  - **Sentry account** (EU region) — create projects `svarsa-app`, `svarsa-bridge`, `svarsa-web`. ETA 10 min.
- **Depends on:** Foundation + production-posture work (done).
- **Deliverable:**
  - `terraform apply` lands the full base stack (VPC, SQL, GCS keyring, Secret Manager, Workload Identity, two Cloud Run services).
  - First images pushed via `deploy-app.yml` + manual `deploy-bridge.yml`.
  - Domain mappings active.
  - Cost-monitoring budget alert configured.
- **Acceptance:**
  - Both `/health` endpoints reachable on TLS.
  - `gcloud sql connect svarsa-pg --user=svarsa_app` succeeds.
  - `alembic upgrade head` recorded in container logs on first cold-start.
  - Per-call structured logs visible via `gcloud logging tail` filter `resource.labels.service_name="svarsa-bridge"`.
- **Runbook:** [`docs/gcp-setup.md`](../../gcp-setup.md).

### A2 · 46elks number + first real call

- **Goal:** A real Swedish phone number rings → AI answers in Swedish → at least one tool call fires → `Call` row + recording in GCS.
- **Why now:** Without this, the product hasn't been demonstrated end-to-end.
- **Required input:**
  - **46elks production account** + API password. Founders sign up at https://46elks.com/sign-up. ETA 10 min.
  - **One Swedish E.164 number** from 46elks (~39 SEK/mån). ETA 5 min.
  - **46elks Voice URL** configured: `https://app.svarsa.se/api/integrations/elks/voice/inbound`.
  - **Decision:** route test calls to the seeded demo firma (`01J0000FIRM0ANDERSSONSVVS00`) until A4 lands.
- **Depends on:** A1.
- **Deliverable:**
  - Webhook configured in 46elks dashboard.
  - First call recording stored in `gs://svarsa-rec-{firma}-europe-west4/calls/{call_id}.mp3`.
  - Per-call trace visible end-to-end in Cloud Logging.
- **Acceptance:**
  - 30-second call: AI greets in Swedish, asks for problem, completes a `lookup_customer` tool call, ends gracefully.
  - Dashboard call detail page renders the recording with a working signed URL.
  - 0 PII leaks in the persisted transcript (test with a planted personnummer).

### A3 · Latency budget verification

- **Goal:** Confirm PRD §15 budgets on real audio: p50 < 1 200 ms, p95 < 2 000 ms.
- **Why now:** The whole product hinges on this. Measure as soon as A2 unlocks real audio.
- **Required input:**
  - **10 recorded Swedish caller utterances** spanning emergency, booking, offert, befintlig kund-fråga, dialect samples (skånska, göteborgska, finlandssvenska, invandrarsvenska), English, Karim B2B style.
  - **Source:** Founders or first pilot firma — Voice Memos / QuickTime, ~2 hours total.
  - **Storage:** `gs://svarsa-eval-recordings/v1/` (private GCS bucket, IAM-restricted).
- **Depends on:** A2.
- **Deliverable:**
  - `backend/scripts/latency_eval.py` — replays the 10 recordings through the bridge, measures per-stage timing, writes a CSV.
  - First measurement report committed under `docs/eval/latency-2026-05-09.md`.
- **Acceptance:** All 10 calls inside p50/p95 budget. If not, decisions about model swap (Gemini 2.5 Native Audio fallback) get raised before A4.

### A4 · Real signup → firma flow

- **Goal:** A new owner signs in with Google, lands on `/inbox`, sees their (empty) firma — not the seeded demo firma.
- **Why now:** Currently NextAuth stamps every user with the demo firma id. Opening even one pilot firma's account requires the real lookup.
- **Required input:**
  - **Decision:** sign-up trigger — auto-create a `Firma` row when a new email signs in (lazy), or require a separate "Skapa firma"-step? Recommendation: **auto-create on first sign-in** with placeholder name `${user.email.split('@')[0]} AB`, owner edits in settings.
  - **Decision:** allow-list of email domains during private alpha? Recommendation: **yes** — `Settings.allowed_signup_domains` env, defaulting to `["siftlab.com"]` until first pilot.
- **Depends on:** A1.
- **Deliverable:**
  - `User` table (currently the model exists; the auth path doesn't read it).
  - `services/onboarding_service.py:create_firma_for_user()` invoked from NextAuth `jwt` callback via a new backend endpoint `POST /api/auth/bootstrap`.
  - NextAuth callback queries the backend; stamp `firma_id` in JWT.
  - Migration: drop the hard-coded `DEMO_FIRMA_ID` fallback in production.
- **Acceptance:**
  - Two test logins from different Google accounts result in two distinct `Firma` rows.
  - Each user only sees their own calls in the inbox.
  - Cross-tenant access denied (verified via API smoke under each token).

### A5 · Tenant erasure CLI

- **Goal:** A founder can run `make erase-tenant FIRMA_ID=...` and have all rows + GCS bucket + KMS key version provably gone within minutes.
- **Why now:** GDPR Art. 17 SLA is 30 days. We don't want to scramble.
- **Required input:**
  - None beyond A1.
- **Depends on:** A1.
- **Deliverable:**
  - `backend/src/svarsa/scripts/erase_tenant.py` — single-transaction SQL DELETE in topo order, then `GCSStorage.delete_tenant`, then KMS key version destroy, then audit log entry.
  - `make erase-tenant` Makefile target.
  - `docs/gdpr.md` — SLA, evidence trail, who has access.
- **Acceptance:**
  - Test run on a synthetic firma: 0 rows remain, bucket deleted, KMS version destroyed, audit log captures the action and the operator.

---

## Tier B — Closed beta-ready (weeks 3–6)

Once Tier A is green, the pilot firmor land here.

### B1 · Concierge onboarding flow

- **Goal:** A new firma signs up → picks a number → connects Fortnox → configures greeting + escalation chain → answers a test call. Total time <30 min (PRD §7.8).
- **Why now:** Pilot expansion stalls otherwise.
- **Required input:**
  - **Voice library scope.** **Recommendation:** 3 default options (Aoede / Charon / Leda); no clones at launch.
  - **SMS templates final wording** (5 templates from `notification_service._TEMPLATES`); founders + UX writing.
  - **Eskaleringskedja default text.** Recommendation in [`docs/superpowers/plans/2026-05-09-svarsa-input-form.md`](./2026-05-09-svarsa-input-form.md).
- **Depends on:** A4.
- **Deliverable:**
  - `web/app/(onboarding)/...` — multi-step flow.
  - `services/onboarding_service.py` provisions number via 46elks API + creates KMS key + bucket eagerly.
  - Settings page → "Greeting" tab → voice preview, persona-overrides textarea.
- **Acceptance:** Non-technical user can complete onboarding in <30 min on first attempt; subsequent test call lands within 15 s.

### B2 · Live inbox WebSocket — frontend hookup

- **Goal:** New calls and call-status changes appear in the dashboard without refresh.
- **Required input:**
  - **Decision:** optimistic update strategy when an action fires from the dashboard. Recommendation: **optimistic + WS reconciliation**.
- **Depends on:** A4.
- **Deliverable:**
  - `web/lib/inbox-ws.ts` — typed WS wrapper.
  - Inbox page becomes a client boundary that subscribes; server still hydrates the first page.
  - Toast notification for incoming `akut`.
- **Acceptance:** Two browser windows open + the test phone calls in: both inboxes show the new row within 1 s.

### B3 · Fortnox integration (read+write)

- **Goal:** AI looks up real Fortnox customers; AI bookings land in Fortnox kalender.
- **Why now:** Half the pilot pool runs Fortnox. PRD §11.2.
- **Required input:**
  - **Fortnox developer account** + approved partner application (~1–3 business days). Founders sign up at https://developer.fortnox.se.
  - **OAuth client_id + secret**.
  - **One pilot firma running Fortnox** willing to be the integration design partner.
  - **Decision:** scope. Recommendation: **Customers (R+W), Invoices (R), BookingsCalendar (R+W)**. Defer Articles/Suppliers.
- **Depends on:** A4, B2.
- **Deliverable:**
  - `backend/src/svarsa/integrations/fortnox.py` — typed client + OAuth callback at `/api/integrations/fortnox/callback`.
  - Per-tenant DEK-encrypted token storage in `Integration.sync_state`.
  - 60-second polling for customer + calendar deltas.
  - Settings page card: "Anslut Fortnox".
- **Acceptance:** Pilot firma connects in <2 min; AI booking creates a Fortnox calendar event within 60 s; token refresh transparent.

### B4 · Eval pipeline + triage gating

- **Goal:** Weekly automated eval over a labeled dataset reports triage accuracy + emergency false-negative rate. CI fails if triage accuracy <85% (PRD §11.2 goal).
- **Required input:**
  - **500 labeled Swedish calls** (intent + severity + expected actions).
    - Source: 5 pilot firmor's 60-day history; ~100 calls each.
    - Consent: each firma signs an addendum (anonymized — caller-side stripped).
    - Annotation: Founders label first 50 to set the rubric, then outsource to a Swedish-speaking VA. ~40 hrs total.
    - Storage: `gs://svarsa-eval-dataset/v1/`.
  - **Slack webhook URL** for `#svarsa-eval` weekly digest.
  - **Decision:** eval framework. Recommendation: **ADK eval** (`google.adk.evaluation`), since the tool catalog already lives in ADK shape.
- **Depends on:** A2 (real call shape), A4.
- **Deliverable:**
  - `backend/src/svarsa/eval/` — dataset loaders, replay harness, metrics, HTML report.
  - `.github/workflows/eval-weekly.yml` — Sunday 08:00 CET, posts summary to Slack.
  - `docs/eval.md` — labeling rubric, how to add a labeled call, how to investigate a regression.
- **Acceptance:** First run reports baseline; an injected prompt regression turns the workflow red.

### B5 · GDPR consent disclosure

- **Goal:** Every call begins with the Swedish disclosure: *"Detta samtal kan spelas in för kvalitets- och utbildningsändamål. Vänligen säg till om du inte vill att samtalet spelas in."*
- **Why now:** PRD §9.2. Pre-pilot blocker.
- **Required input:**
  - **Disclosure copy reviewed by counsel.** Default suggested above; verify the wording.
  - **Decision:** opt-in vs. opt-out for B2C. Recommendation per PRD: **opt-out via verbal disclosure**, with a tool `disable_recording_for_call()` invoked if the kund objects.
- **Depends on:** A2.
- **Deliverable:**
  - System prompt extended to play the disclosure as the first utterance.
  - New tool: `disable_recording_for_call()` → drops the recording buffer, audit-logs the choice.
  - `Firma.settings.consent_disclosure` text editable per firma.
- **Acceptance:** Test call: AI plays the disclosure; saying "jag vill inte att det spelas in" → `Call.recording_url` stays null + `audit_log` row written.

### B6 · Cost telemetry per call

- **Goal:** Each `Call` row stores its measured cost (Gemini tokens × price + 46elks minute + SMS); dashboard surfaces per-firma rolling 7-day median + p95.
- **Why now:** PRD §3.1 goal 8 — median per-call cost < 2,50 SEK. Without measurement we can't enforce.
- **Required input:**
  - **Vertex Live API GA pricing** (currently preview-free) — Founders confirm before launch.
  - **46elks rate card** — already public; cache in `Settings.elks_inbound_minute_cost_sek` etc.
- **Depends on:** A2.
- **Deliverable:**
  - `Call.cost_breakdown_json` column.
  - `services/cost_service.py` finalizer.
  - Dashboard panel on the inbox.
- **Acceptance:** Cost telemetry within ±5 % of actual GCP/46elks invoices for one billing cycle.

### B7 · Outbound SMS sender id verification

- **Goal:** Every pilot firma's SMS appears from their firma name (not "Svarsa").
- **Why now:** Conversion uplift on `emergency_ack` and `booking_confirmation` is real; tracker blocker for the Phase 1 KPI of post-call CSAT ≥ 4,2.
- **Required input:**
  - **One per firma:** signed permission letter + org-nummer. Submit to 46elks (3–5 business days each).
- **Depends on:** A2, B1.
- **Deliverable:**
  - Settings page → "SMS sender id" — per-firma alias + verification status.
  - Falls back to platform `Svarsa` until verification completes.
- **Acceptance:** First pilot firma's SMS shows their alias on a real iPhone receive test.

---

## Tier C — Beta polish & moat (weeks 6–10)

### C1 · Frontend polish for closed beta

- **Goal:** Dashboard feels production-grade — react-query, virtualized inbox, audio scrubbing tied to transcript, accessibility, mobile-responsive.
- **Required input:**
  - **Walkthrough notes from 2–3 pilot owner sessions** — Loom recordings, friction points logged.
  - **Decision:** accessibility target. Recommendation: **WCAG 2.1 AA**.
- **Depends on:** B1, B2.
- **Deliverable:**
  - `@tanstack/react-query` wired with optimistic updates.
  - Inbox virtualization via `@tanstack/react-virtual` once call count > 200.
  - Transcript ↔ audio cursor sync.
  - Keyboard nav, ARIA labels, focus management; axe-core 0 critical issues.
- **Acceptance:** Lighthouse mobile score ≥ 90.

### C2 · Post-call PII entity audit

- **Goal:** Catch PII the live regex misses (e.g. spelled-out personnummer, partial bankgiro). Async audit fires after recording is encoded; flagged transcripts get a follow-up redaction pass.
- **Why now:** Strategy A from the input form (live regex now + post-call audit later) — this is the "later" half. Closes the loop on PRD §9.5.
- **Required input:**
  - **Decision:** entity extractor. Recommendation: **Gemini-based prompt** (cheap; reuse Vertex AI access we already have). Alternative: a Swedish NER model from HuggingFace.
- **Depends on:** A2.
- **Deliverable:**
  - `backend/src/svarsa/services/pii_audit_service.py` — runs in a Cloud Tasks queue after each call.
  - Re-redacts transcript + writes audit-log entry with the upgraded labels.
- **Acceptance:** 100-call validation set with planted obscure patterns: 0 false-negatives.

### C3 · Visma + Google Calendar integrations

- **Goal:** Cover the rest of the integration matrix.
- **Required input:**
  - **Visma developer account** + OAuth client. Founders sign up at https://developer.visma.com.
  - **Google Calendar OAuth scope** added to the same client used in A1.
- **Depends on:** B3 (proves the integration shape).
- **Deliverable:** `integrations/visma.py`, `integrations/google_calendar.py`, settings cards.
- **Acceptance:** One firma per integration syncs bookings bidirectionally.

### C4 · Eval expansion + per-tool latency SLO

- **Goal:** Eval coverage extends to all 12 tools (not just triage). p95 < 200 ms enforced per tool (PRD §8.4).
- **Required input:** None beyond B4.
- **Depends on:** B4.
- **Deliverable:**
  - Tool-level metrics in the weekly digest.
  - `Settings.tool_latency_p95_alert_ms` — exceedance triggers Sentry issue.
- **Acceptance:** A deliberate slow injection in `lookup_customer` triggers an alert within 10 minutes.

### C5 · Billing + plan enforcement

- **Goal:** Starter / Professional / Premium plan limits actually enforced (calls/mån, concurrent calls, integration count).
- **Why now:** Pricing only matters if plan limits are real.
- **Required input:**
  - **Decision:** payment processor. Recommendation: **Stripe Billing** (EU residency optional; standard for SaaS).
  - **Plan limits per tier** — already in PRD §10; needs operationalizing.
- **Depends on:** A1, A4.
- **Deliverable:**
  - `Firma.plan` enforced on call ingress (reject with friendly busy tone past plan limit).
  - Stripe webhook → updates `Firma.plan`.
  - Dashboard upgrade flow.
- **Acceptance:** Starter firma at 200 calls/mån sees the busy-tone path on call 201.

---

## Tier D — GA & scale (weeks 10+)

### D1 · Hantverksdata Next integration

- **Goal:** AI books work directly into Hantverksdata projekt.
- **Why now:** Strategic moat (PRD §8.7.2).
- **Required input:**
  - **Signed Hantverksdata partneravtal** (~2–4 months from first contact). Start the conversation in week 1 anyway — `partners@hantverksdata.se` with a 1-page deck + concrete demo offer.
  - **Hantverksdata API credentials** (delivered after avtal).
  - **Design-partner pilot firma running Hantverksdata.**
- **Depends on:** B3 (shape).
- **Acceptance:** One Hantverksdata-running pilot firma books an AI-handled job and it lands in their projektsystem.

### D2 · Multi-firma rollup

- **Goal:** A single owner manages several AB:s under one login (PRD §13).
- **Required input:**
  - **Decision:** plan-tier. Recommendation: **Premium-only**.
- **Depends on:** A4.
- **Deliverable:** `User ↔ Firma` many-to-many; topbar firma switcher; per-firma access checks tighten on the backend.
- **Acceptance:** Test owner with two firmor sees correct inbox per firma; cross-firma actions blocked.

### D3 · White-label theming

- **Goal:** Premium firmor get firma-branded greeting, SMS sender id, dashboard accent.
- **Required input:**
  - **Decision:** tier threshold. Recommendation: **Premium-only**.
  - **Brand-asset upload UX** — small image upload to GCS bucket, `Firma.settings.brand_assets`.
- **Depends on:** A4, B7.
- **Deliverable:** Per-firma theme tokens override `--color-accent`; greeting variables; SMS sender alias; dashboard logo override.
- **Acceptance:** Premium firma's dashboard looks visibly distinct; their inbound SMS appears from their sender id.

### D4 · Mobile apps (React Native + Expo)

- **Goal:** Feature parity with web + native push for emergency escalations (PRD §7.7).
- **Why now:** Owners are 80 % on a job site (PRD §5.1).
- **Required input:**
  - **Apple Developer account** + DUNS number ($99/yr, ~5 days).
  - **Google Play developer account** ($25 one-time).
  - **Apple critical alerts entitlement** for emergency push that bypasses DND (~2–4 weeks review).
- **Depends on:** A4, B1, B2, B7.
- **Deliverable:** `mobile/` Expo + RN; shared design tokens with web.
- **Acceptance:** Emergency escalation push lands on a locked iPhone within 15 s.

### D5 · Eval-driven prompt iteration loop

- **Goal:** "Träna AI"-knapp from PRD §7.7 — owner marks a call as wrong → adjustment lands in firma's persona prompt within 24 hours.
- **Required input:** None beyond B4.
- **Depends on:** B4.
- **Deliverable:** Few-shot examples per firma, persisted as part of `Firma.settings.persona_overrides` + eval runner uses them.
- **Acceptance:** 10 owner-corrections over a week visibly improve the firma's eval scores in the next weekly digest.

---

## Cross-cutting workstreams (run continuously)

### Validation research (PRD §16 Appendix C)

Required input:
- **14-day call-tracking pilot** with 10–15 friendly hantverkare (~5 kSEK + gift cards).
- **30+ structured interviews** with willingness-to-pay laddering.
- **5–8 bokföringsbyrå conversations**, **2 branschorg meetings**, **1 Hantverksdata meeting**.
- **Public data triangulation:** Skatteverket ROT-statistik, SCB SNI 43.21/43.22/43.39, Bolagsverket, Installatörsföretagen.

Owner: Founders. Phase ends with a written validation memo signed by founders + 2–3 advisors before Phase 1 commits >50 % of engineering capacity to closed beta build.

### Risk monitoring

- **Monthly:** review Hantverksdata job postings (build-vs-partner signal).
- **Quarterly:** Vertex Live API roadmap check.
- **Weekly:** sample emergency false-negative rate from the eval pipeline (B4); hard ceiling 0.5 %.

### Cost telemetry review

- **Weekly:** read the per-firma cost panel (B6); investigate any firma where median per-call cost > 5 SEK.
- **Monthly:** GCP + 46elks invoice reconciliation against the rolled-up `Call.cost_breakdown_json` total.

### Legal/compliance

- **Pre-Tier A:** consent disclosure copy reviewed by counsel.
- **Pre-pilot:** DPA template, sub-processor list (Google, 46elks, Postmark/Mailgun, Sentry, GCP, Vercel-style only if used).
- **Pre-GA:** DPIA (Art. 35) completed by external DPO; reviewed annually.

---

## Suggested staffing & sequencing

Assume one full-time engineer + founders supporting on validation, partner outreach, and copy.

- **Weeks 1–2 (Tier A):** A1 → A2 → A3 → A4 → A5 in serial order. Founders run validation calls in parallel.
- **Weeks 3–6 (Tier B):** B1 + B2 in parallel; B5 lands as soon as legal copy is signed off; B3 starts as Fortnox account approves; B4 + B6 + B7 round out closed-beta-ready.
- **Weeks 6–10 (Tier C):** C1 takes ownership; C2/C3/C4/C5 in parallel as inputs arrive.
- **Weeks 10+ (Tier D):** D1 unblocks once Hantverksdata avtal signs; D2/D3 as plan tier need surfaces; D4 ~6 weeks calendar (incl. Apple review); D5 builds on B4.

---

## Required inputs — consolidated by tier

### Tier A inputs (collect this week)

| Item | Source | ETA |
|---|---|---|
| GCP project + billing | Founders create | 5 min |
| Domain DNS access (`svarsa.se`) | Founders | already owned |
| Generated platform secrets (3) | `openssl rand` | 1 min |
| Sentry EU projects (3) | sentry.io | 10 min |
| 46elks production account + API password | 46elks dashboard | 10 min |
| 46elks Swedish phone number | 46elks dashboard | 5 min |
| Google OAuth client (web app) | GCP Credentials | 15 min |
| 10 recorded Swedish caller utterances (latency eval) | Founders or pilot caller | ~2 hrs |

### Tier B inputs (collect by week 3)

| Item | Source | ETA |
|---|---|---|
| Voice library scope decision | Founders | discussed |
| Final SMS template wording (5) | Founders + UX writing | 1–2 days |
| Eskaleringskedja default text | Founders | 1 day |
| 5 pilot firmor opted in for eval recording | Founders' network | 1–2 weeks |
| 500 labeled calls (with rubric) | Founders + VA annotator | 4–6 weeks |
| Slack webhook for `#svarsa-eval` | Slack admin | 5 min |
| Fortnox developer account approval | https://developer.fortnox.se | 1–3 business days |
| Pilot firma running Fortnox | Founders' network | 1–2 weeks |
| Consent disclosure copy reviewed | Legal counsel | 1 week |
| Per-firma SMS sender id submissions | 46elks dashboard | 3–5 business days each |
| Stripe Billing account | https://dashboard.stripe.com | 30 min |

### Tier C inputs (collect weeks 4–8)

| Item | Source | ETA |
|---|---|---|
| Pilot owner walkthrough sessions (2–3) | Founders | 1 hr each |
| Visma developer account + OAuth | https://developer.visma.com | 1–3 business days |
| PII entity extractor decision | Engineering call | discussed |

### Tier D inputs (long-running; start now)

| Item | Source | ETA |
|---|---|---|
| Hantverksdata partneravtal | Founders + legal | 2–4 months |
| Apple Developer account + DUNS | apple.com + dnb.com | ~5 days |
| Google Play developer account | play.google.com | same-day |
| Apple critical alerts entitlement | Apple Developer Portal | 2–4 weeks |
| Brand assets per Premium firma | Firma | per-firma |

---

## Decisions to lock now (before Tier A apply)

| Decision | Recommendation | Rationale |
|---|---|---|
| Auto-create firma on first sign-in vs. explicit step | **Auto-create with placeholder name** | Removes onboarding friction; owner edits in settings |
| Allow-list email domains for private alpha | **Yes, default `siftlab.com` only** | Stops random Google logins from creating firmor before pilot opens |
| GDPR consent — opt-in vs. opt-out for B2C | **Opt-out via verbal disclosure** | Swedish law tolerates; matches PRD §9.2 |
| Cost-monitoring monthly target (pre-pilot) | **500 SEK** | Stops accidental six-figure GCP bills if a misconfig lands |
| Cost-monitoring monthly target (pilot) | **1500 SEK** | Covers 5 firmor × ~2 SEK × 200 calls × overhead |
| First Cloud SQL tier | **`db-custom-1-3840`** | ~$30/mo; upgrade trigger at 50 firmor |
| Memorystore Redis | **Skip until needed** | Foundation uses in-process pub-sub for inbox WS; revisit at multi-pod load |
| Eval framework | **ADK eval** | Tool catalog already in ADK shape |
| Payment processor | **Stripe Billing** | EU optional; standard for SaaS |
| Mobile stack | **Expo + React Native** | Fastest to ship; OTA; web parity |
| White-label tier threshold | **Premium only** | Justifies Premium pricing; protects brand consistency |
| Multi-firma rollup tier | **Premium only** | Same reasoning |

---

## Document hygiene

- Edit this file inline as steps complete: change the heading to `### A1 · Provision GCP — Done · 7ad4165` (commit sha + date).
- New ideas not on this list go into `## Backlog` at the bottom.
- When all Tier-A items are done, update [`docs/superpowers/plans/2026-05-09-svarsa-input-form.md`](./2026-05-09-svarsa-input-form.md) and mark the corresponding rows green.

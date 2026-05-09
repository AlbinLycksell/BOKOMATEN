# Switchboard AI — Input Form

**Companion to:** [`2026-05-09-switchboard-next-steps.md`](./2026-05-09-switchboard-next-steps.md)
**For:** Founders to fill in. Engineering picks up each step once its inputs are green.

> Fill in inline. Commit each tier when complete. When Tier 1 is green, kickoff Step 1 of the next-steps plan.

## Legend

- `[ ]` not started · `[~]` in progress · `[x]` done · `[!]` blocked
- After "Value:" write the answer (or paste a 1Password reference like `op://Vault/Item/field` — never paste real secrets into git)
- For decisions: put `[x]` next to the option you choose. **Recommended option is bolded.**

---

## Tier 1 — first real call (highest priority)

### Step 1 · 46elks telephony adapter

#### Account & credentials

- [ ] **46elks production account**
  - How to create: Go to https://46elks.com/sign-up — fill in company name, org-nummer, email. Free tier exists; pay-as-you-go for traffic.
  - ETA: 10 minutes (immediate provisioning)
  - Cost: 0 SEK to create, ~0,40 SEK/inbound minute, ~0,30 SEK/SMS in Sweden
  - **Account email:** ____________________________________
  - **Login URL:** https://dashboard.46elks.com/

- [ ] **46elks API username + password**
  - How to find: 46elks dashboard → Account → API → "Show API credentials". Username is your auth username; password is the API password (not your dashboard password).
  - ETA: 1 minute
  - Store in 1Password as `Switchboard / 46elks API`. Reference here, not the value.
  - **Username:** ______________________________________
  - **API password (1Password ref):** ___________________

- [ ] **Swedish E.164 test number**
  - How to obtain: 46elks dashboard → Numbers → "Add number" → Country: Sweden → choose any available 010-/08- number.
  - ETA: 5 minutes; charged ~39 SEK/mån
  - Alternative: porta-in an existing number (slower; 5–10 business days)
  - **Number:** +46 _______________
  - **Plan:** [ ] new number   [ ] porta-in existing

#### Decisions

- [ ] **Public webhook URL for the bridge in dev**
  - **A. ngrok / Cloudflare Tunnel** (recommended)
    - Pros: Free tier, instant, auth-protected, works from a laptop
    - Cons: URL changes per session unless paid plan
  - **B. Cloud Run dev service**
    - Pros: Stable URL, mirrors prod
    - Cons: Requires GCP setup first (Step 4); slower iteration
  - **Choice:** [ ] A   [ ] B
  - **If A:** install with `brew install cloudflared` (Cloudflare) or `brew install ngrok` (ngrok)

- [ ] **Test-number routing target**
  - Options: route all calls to the seeded demo firma `01J0000FIRM0ANDERSSONSVVS00` for test, or to a real pilot firma.
  - **Recommendation:** seed firma until concierge onboarding (Step 12) lands.
  - **Choice:** [ ] seed firma   [ ] real pilot: ___________

---

### Step 2 · Gemini Live latency validation

#### Account & credentials

- [ ] **GCP project**
  - How to create: https://console.cloud.google.com/projectcreate — name `switchboard-prod` (or `switchboard-staging`), org `siftlab.com` if you want it under that org.
  - ETA: 5 minutes; verify billing is attached.
  - **Project ID:** _____________________________________
  - **Project number:** _________________________________
  - **Billing account:** ________________________________

- [ ] **Vertex AI enabled**
  - How: GCP console → "APIs & Services" → search "Vertex AI" → Enable. Same for "Cloud Run", "Cloud SQL Admin", "Secret Manager", "Cloud Storage", "Cloud KMS", "Cloud Logging".
  - ETA: 2 minutes per API
  - **Confirmed enabled:** [ ]

- [ ] **Service account for backend**
  - How: GCP console → IAM & Admin → Service Accounts → Create. Name `switchboard-backend`. Grant roles: `Vertex AI User`, `Cloud Run Invoker`, `Secret Manager Secret Accessor`, `Cloud SQL Client`, `Storage Object Admin`.
  - ETA: 10 minutes
  - For dev, generate a JSON key (Settings → Keys → Add); for prod, use Workload Identity Federation (Step 8).
  - **Service account email:** _________________________
  - **Dev JSON key (1Password ref):** _________________

#### Data artifacts to gather

- [ ] **10 representative recorded Swedish caller utterances**
  - How: Record yourself or pilot caller speaking each scenario for 10–20 s. Use Voice Memos on iPhone or QuickTime on Mac. Export as `.wav` or `.mp3`.
  - Scenarios needed:
    - [ ] Vattenläcka emergency ("det rinner ner på golvet")
    - [ ] OVK booking (B2B, multiple addresses)
    - [ ] Offert request for badrumsrenovering
    - [ ] Befintlig kund-fråga ("hur går det med mitt jobb?")
    - [ ] Telemarketing fellringd (handle gracefully)
    - [ ] Skånska dialect speaker (any topic)
    - [ ] Göteborgska dialect speaker
    - [ ] Finlandssvenska speaker
    - [ ] Heavy-accent invandrarsvenska
    - [ ] English speaker (Stockholm-based, common pattern)
  - Storage: drop into a private GCS bucket `gs://switchboard-eval-recordings/` (or share via Google Drive while waiting for GCS).
  - ETA: 2 hours total to record all 10
  - **Recordings location:** _____________________________

#### Decisions

- [ ] **Vertex AI vs `generativelanguage.googleapis.com`**
  - **A. Vertex AI in `europe-west4`** (recommended)
    - Pros: EU residency, enterprise terms, Customer Data Use commitments (no training on inputs), reserved-capacity option, audit logs
    - Cons: More setup, requires GCP project
  - **B. `generativelanguage.googleapis.com` with API key**
    - Pros: 5-minute setup, what `scripts/gem_live.py` already uses
    - Cons: US-hosted, no DPA, weaker GDPR posture, no reserved capacity
  - **Choice:** [ ] A (recommended for prod) [ ] B (only for dev/eval)

---

### Step 3 · OAuth/JWT auth

#### Decisions

- [ ] **Identity provider**
  - **A. NextAuth + Google + email magic-link** (recommended)
    - Pros: Free, MIT-licensed, Google handles MFA, hantverkare often use Google Workspace, 1-day to wire, EU-hostable
    - Cons: Less polished than Clerk; you own the session table
  - **B. Auth0**
    - Pros: Battle-tested, many providers, slick admin UI
    - Cons: ~$240/mo+ at our user volumes, vendor lock-in, US-hosted (DPA workable but friction)
  - **C. Clerk**
    - Pros: Best DX, great UI, fast
    - Cons: ~$100/mo+ at scale, US-hosted, we'd export their schema for portability
  - **D. Roll-your-own (Authlib + Postgres sessions)**
    - Pros: Full control, no vendor
    - Cons: 1+ week to do right; auth bugs are the worst kind of bugs
  - **Choice:** [ ] A [ ] B [ ] C [ ] D

- [ ] **Session model**
  - **A. JWT cookie, JWKS-verified by backend** (recommended; matches NextAuth default)
    - Pros: Backend stateless, easy horizontal scale, simple
    - Cons: Token revocation requires a denylist or short TTL
  - **B. Backend session store (Postgres or Redis)**
    - Pros: Instant revocation, classic
    - Cons: Extra round-trip per request; backend stateful
  - **Choice:** [ ] A [ ] B

- [ ] **Multi-firma per user**
  - Options: single firma per user (v1) vs many-to-many.
  - **Recommendation:** single in v1; multi as Premium feature (PRD §13 open question).
  - **Choice:** [ ] single   [ ] multi

#### Once "A. NextAuth + Google" is chosen

- [ ] **Google OAuth client**
  - How to create: GCP console → APIs & Services → Credentials → Create Credentials → OAuth client ID → Application type: Web → Authorized redirect URI: `https://app.switchboard.se/api/auth/callback/google` (and `http://localhost:3000/api/auth/callback/google` for dev). First time you'll be asked to set up the OAuth consent screen — pick "External", scopes "openid email profile".
  - ETA: 15 minutes
  - **Client ID:** ______________________________________
  - **Client secret (1Password ref):** _________________

- [ ] **NEXTAUTH_SECRET**
  - How to generate: `openssl rand -base64 32`
  - Store in `.env.local` (gitignored) and Cloud Run secret.
  - **Generated:** [ ]

---

### Step 4 · Alembic + Postgres

#### Account & credentials

- [ ] **Cloud SQL Postgres instance**
  - How to create: GCP console → Cloud SQL → Create Instance → Postgres 16 → Region `europe-west4` → Tier `db-custom-2-8` (PRD §8.10) → Public IP off, Private IP on, attach to default VPC. Set a strong root password (1Password it).
  - ETA: 10 min provisioning
  - Cost: ~$120/mo for `db-custom-2-8` 24×7. Stop the instance off-hours during pre-launch to halve.
  - **Instance name:** ___________________________________
  - **Connection name** (`project:region:instance`): _____________________
  - **Root password (1Password ref):** _________________

- [ ] **Database + low-privilege role**
  - How: Connect via Cloud SQL Proxy locally, run:
    ```sql
    CREATE DATABASE switchboard;
    CREATE ROLE switchboard_app LOGIN PASSWORD '<random>';
    GRANT CONNECT ON DATABASE switchboard TO switchboard_app;
    GRANT USAGE ON SCHEMA public TO switchboard_app;
    -- (RLS-friendly grants applied per-table by Step 9 migration)
    ```
  - **App password (1Password ref):** __________________

#### Decisions

- [ ] **Local dev database**
  - **A. SQLite (current)** (recommended)
    - Pros: Zero setup, fast tests, file-based
    - Cons: SQL features limited (no real RLS, JSONB → JSON), parity bugs possible
  - **B. Postgres in Docker locally**
    - Pros: Production parity, RLS testable
    - Cons: Slower iteration, requires `docker compose up` before every dev session
  - **C. SQLite locally + Postgres in CI** (recommended)
    - Pros: Fast local + parity gate at CI
    - Cons: Two configs to maintain
  - **Choice:** [ ] A [ ] B [ ] C

---

## Tier 2 — production readiness

### Step 5 · Recording capture pipeline

#### Decisions

- [ ] **Per-firma bucket creation timing**
  - **A. Eager (at firma onboarding)** (recommended)
    - Pros: Fail-fast on KMS / IAM misconfiguration before first call
    - Cons: Onboarding step has a network dependency on GCP
  - **B. Lazy (on first call)**
    - Pros: Onboarding is offline-friendly
    - Cons: First call can fail with cryptic GCS errors
  - **Choice:** [ ] A [ ] B

- [ ] **Recording encoding**
  - **A. MP3 64kbps mono** (recommended)
    - Pros: Plays everywhere, smallest "compatible" footprint, ~30 KB/min
    - Cons: Lossy; long-term archival quality lower
  - **B. Opus 24kbps mono**
    - Pros: Smaller (~20 KB/min), modern codec
    - Cons: Older browsers struggle, no native iOS share-sheet support
  - **C. Both — MP3 for playback, Opus archival**
    - Pros: Best of both
    - Cons: Storage 2× and a second encode step
  - **Choice:** [ ] A [ ] B [ ] C

- [ ] **Default retention (PRD §9.6)**
  - PRD default: 7 days, configurable 7–365.
  - **Choice:** [ ] 7 (PRD default)   [ ] other: _______ days

#### Configuration

- [ ] **Cloud KMS keyring**
  - How to create: GCP console → KMS → Create Keyring `switchboard` in `europe-west4`. CryptoKey per firma is created at onboarding by the recording service.
  - ETA: 2 minutes
  - **Keyring name:** ____________________________________

---

### Step 6 · Outbound SMS via 46elks

#### Decisions

- [ ] **SMS sender id**
  - **A. Per-firma alias** (recommended)
    - Pros: SMS appears from "Anderssons VVS" on caller's phone — trust signal
    - Cons: 46elks verification per firma (~3–5 business days)
  - **B. Platform `SWITCHBOARD` sender id**
    - Pros: One verification, instant for new firmor
    - Cons: Recipient sees "SWITCHBOARD" not the firma's name; weaker conversion
  - **C. Hybrid — platform fallback while per-firma verifies**
    - Pros: New firmor work immediately; verified ones get the upgrade
    - Cons: Two code paths
  - **Choice:** [ ] A [ ] B [ ] C

#### SMS template wording (5 templates from PRD §8.4.7)

Edit each below. Keep under 160 chars to stay single-segment. Use `{name}`, `{time}`, `{address}` etc. as variables.

- [ ] **`emergency_ack`** (sent right after AI escalates)
  - Suggested: `Tack {name}, vi har fått ditt ärende och Magnus ringer dig inom 15 minuter. Stäng av vattnet om du inte redan gjort det. /Anderssons VVS`
  - **Final:** _________________________________________

- [ ] **`booking_confirmation`** (sent right after AI books)
  - Suggested: `Hej {name}! Du är bokad {time} på {address}. Vi hör av oss om något ändras. /Anderssons VVS`
  - **Final:** _________________________________________

- [ ] **`photo_upload_link`**
  - Suggested: `Hej! Skicka gärna bild på problemet via denna länk (giltig 7 dagar): {url} /Anderssons VVS`
  - **Final:** _________________________________________

- [ ] **`callback_promise`**
  - Suggested: `Tack för samtalet, {name}. Vi ringer upp inom {window}. /Anderssons VVS`
  - **Final:** _________________________________________

- [ ] **`secure_form_link`**
  - Suggested: `För känslig info, fyll i säkert formulär här (giltigt 1 timme): {url} /Anderssons VVS`
  - **Final:** _________________________________________

#### Verification

- [ ] **Sender id verification submitted to 46elks**
  - How: 46elks dashboard → SMS → Senders → Add → submit firma name + org-nummer + a permission letter from firma owner.
  - ETA: 3–5 business days
  - **Submitted on:** ________________

---

### Step 7 · Fortnox integration

#### Account & credentials

- [ ] **Fortnox developer account**
  - How: https://developer.fortnox.se/ → Sign up → application type "Integrationspartner". Wait for approval (~1–3 business days).
  - ETA: 2 days
  - **Approved on:** ________________

- [ ] **Fortnox OAuth application**
  - How: Developer portal → Create application. Provide: name "Switchboard AI", redirect URL `https://app.switchboard.se/api/integrations/fortnox/callback`, scopes: `customer`, `bookkeeping`, `invoice` (read), and `connectfile` (for attachments). Skip `journalvouchers` for v1.
  - ETA: 5 minutes
  - **Client ID:** ______________________________________
  - **Client secret (1Password ref):** _________________

- [ ] **Pilot firma running Fortnox**
  - How: identify from Founders' network. Need ~30 min of their time to do the OAuth flow + a smoke test.
  - **Pilot firma:** _____________________________________
  - **Contact:** ________________________________________

#### Decisions

- [ ] **Fortnox endpoints to surface in v1**
  - **A. `Customers` (read+write), `Invoices` (read), `BookingsCalendar` (read+write)** (recommended)
    - Pros: Covers customer recognition, invoice-related questions, real bokning
    - Cons: Means we don't expose articles/products yet (firmor wanting to lookup material codes will wait)
  - **B. Add `Articles` + `Suppliers`**
    - Pros: AI can propose material lists during a quote
    - Cons: Tool catalog grows; eval coverage harder
  - **Choice:** [ ] A [ ] B

---

### Step 8 · Cloud Run deploy + Terraform

#### Account & credentials

- [ ] **Domain ownership**
  - Decide and register/move:
  - **`app.switchboard.se`** (Application Backend) — owned by: ____
  - **`bridge.switchboard.se`** (Realtime Bridge) — owned by: ____
  - **Recommendation:** register `switchboard.se` if not done; we'll add subdomain routing via Cloud Run domain mapping.
  - **Registrar:** _______________________________________
  - **DNS provider:** ____________________________________

- [ ] **GitHub Actions Workload Identity Federation**
  - How: GCP console → IAM & Admin → Workload Identity Federation → Create pool → Add provider for GitHub OIDC. Grant the `switchboard-backend` SA `Workload Identity User` role on the pool. (Saves dealing with JSON keys.)
  - ETA: 30 minutes (one-time)
  - **Pool name:** _______________________________________
  - **Provider name:** ___________________________________
  - **Repo bound to:** `AlbinLycksell/BOKOMATEN` (and any future repo names)

- [ ] **Artifact Registry repository**
  - How: GCP console → Artifact Registry → Create Repository → Format Docker → Region `europe-west4` → Name `switchboard`.
  - ETA: 1 minute
  - **Repository:** `europe-west4-docker.pkg.dev/<project>/switchboard`

#### Decisions

- [ ] **Terraform now or later**
  - **A. Now — `terraform/` skeleton lands with Step 8** (recommended)
    - Pros: Reproducible env, easy DR, peer-review of infra changes
    - Cons: ~2 day setup tax up front
  - **B. Click-ops first, Terraform later**
    - Pros: Faster to first deploy
    - Cons: Drift, manual recovery, harder onboarding
  - **Choice:** [ ] A [ ] B

---

### Step 9 · Postgres RLS

#### Decisions

- [ ] **Application role name**
  - **Recommendation:** `switchboard_app` (no `BYPASSRLS`, no `SUPERUSER`, only `LOGIN` + tenant-scoped grants)
  - **Choice:** [x] switchboard_app   [ ] other: _______

#### Verification (no input — just a checklist for Step 9)

- Pen-test scenario documented in `docs/multi-tenancy.md`
- Negative test runs in CI: query under wrong firma returns 0 rows even with raw SQL injection

---

### Step 10 · Live inbox WebSocket

#### Decisions

- [ ] **Optimistic update strategy**
  - **A. Optimistic UI + WS reconciliation** (recommended)
    - Pros: Instant feedback, robust to dropped connections
    - Cons: Brief flash if reconciliation differs
  - **B. Wait for WS confirm**
    - Pros: UI always reflects truth
    - Cons: Visible latency on every action
  - **Choice:** [ ] A [ ] B

---

## Tier 3 — closed-beta requirements

### Step 11 · Eval pipeline

#### Data artifacts to gather

- [ ] **500 labeled Swedish calls**
  - Source: 5 pilot firmor's 60-day call history. Roughly 100 calls/firma over 60 days.
  - Permissions: each firma signs an addendum allowing us to use their recordings for eval (anonymized — caller-side stripped to first name only).
  - Annotation: per-call labels for `intent`, `severity`, expected actions. Estimated 5 min per call → 40 hours total.
  - **Recommendation:** outsource annotation to a Swedish-speaking VA after Founders label the first 50 to set the rubric.
  - Storage: `gs://switchboard-eval-dataset/v1/` (private, IAM restricted).
  - **Pilot firmor opted in:**
    - [ ] firma 1: _____________________________
    - [ ] firma 2: _____________________________
    - [ ] firma 3: _____________________________
    - [ ] firma 4: _____________________________
    - [ ] firma 5: _____________________________
  - **Annotator(s):** _________________________________

- [ ] **Slack webhook for weekly eval reports**
  - How: Create a channel `#switchboard-eval` → Apps → Incoming Webhooks → Add → copy URL.
  - ETA: 5 minutes
  - **Webhook URL (1Password ref):** ___________________

#### Decisions

- [ ] **Eval framework**
  - **A. ADK eval (`google.adk.evaluation`)** (recommended)
    - Pros: Tool catalog already in ADK shape; aligns with the post-call agent infra
    - Cons: Newer surface; we'll occasionally hit rough edges
  - **B. Promptfoo or LangSmith**
    - Pros: Mature, language-agnostic
    - Cons: Adds a vendor surface; less integrated with our agents
  - **C. Custom replay harness**
    - Pros: Full control
    - Cons: We're rebuilding what ADK provides
  - **Choice:** [ ] A [ ] B [ ] C

---

### Step 12 · Concierge onboarding

#### Decisions

- [ ] **Voice library scope at launch**
  - **A. 3 default options — warm female (Aoede), neutral male (Charon), energetic young (Leda)** (recommended)
    - Pros: Choice without overwhelm; brand-consistent enough
    - Cons: Some firmor will want their own voice clone (not at launch)
  - **B. Single platform voice**
    - Pros: Strongest brand consistency
    - Cons: Doesn't fit every firma's tone
  - **C. Full per-firma voice cloning at launch**
    - Pros: Maximum perceived ownership
    - Cons: Legal+trust risk; delays launch ~1 month
  - **Choice:** [ ] A [ ] B [ ] C

#### Onboarding copy

- [ ] **Greeting wizard intro line in Swedish**
  - Suggested: `Vi hjälper dig sätta upp Switchboard AI på 30 minuter. Klart börjar AI:n svara dina samtal redan i kväll.`
  - **Final:** _________________________________________

- [ ] **Eskaleringskedja default text** (shown when an owner accepts the default)
  - Suggested: `Akut: ring jourtekniker → väntar 5 min → ring dig → väntar 5 min → extern jour. Kontorstid: ringer dig direkt.`
  - **Final:** _________________________________________

- [ ] **Walkthrough video for concierge onboarding** (optional but accelerates self-serve)
  - Tool: Loom or Screen Studio. ~3 minutes covering signup → number → integration → testringa.
  - **URL:** _____________________________________________

---

### Step 13 · PII redaction

#### Decisions

- [ ] **Redaction strategy**
  - **A. Live regex masking + post-call entity audit** (recommended)
    - Pros: Instant masking on dashboard; audit catches misses; fail-safe
    - Cons: Two systems
  - **B. Live regex only**
    - Pros: Simple
    - Cons: Misses non-canonical patterns (e.g. `850525-1234`)
  - **C. Post-call entity extraction only**
    - Pros: Higher recall
    - Cons: 10–30 s window where personnummer is visible in transcript
  - **Choice:** [ ] A [ ] B [ ] C

---

### Step 14 · Hantverksdata Next

#### Account & credentials

- [ ] **Hantverksdata partneravtal**
  - How: Email partners@hantverksdata.se requesting a partnership conversation. Include 1-page deck + concrete demo offer.
  - ETA: 2–4 months from first contact (per PRD §8.7.2)
  - **First contact sent:** ________________
  - **Avtal signed:** ________________

- [ ] **Hantverksdata API credentials** (delivered after avtal)
  - Store in 1Password.
  - **Credentials received:** [ ]

- [ ] **Design-partner pilot firma running Hantverksdata**
  - **Pilot firma:** _____________________________________

---

### Step 15 · Visma + Google Calendar

#### Account & credentials

- [ ] **Visma developer account**
  - How: https://developer.visma.com/ → Sign up. EU-resident.
  - **Client ID:** ______________________________________
  - **Client secret (1Password ref):** _________________

- [ ] **Google Calendar OAuth**
  - Already covered if Step 3 chose Google. Add scope `https://www.googleapis.com/auth/calendar` to the same OAuth consent screen.
  - **Confirmed scope added:** [ ]

---

### Step 16 · Frontend polish

#### Data artifacts

- [ ] **Walkthrough notes from 2–3 pilot owner sessions**
  - How: 30-minute screen-share with each owner using the inbox + call detail views. Record on Loom; transcribe key friction points.
  - **Sessions completed:**
    - [ ] firma 1
    - [ ] firma 2
    - [ ] firma 3

#### Decisions

- [ ] **Accessibility target**
  - **A. WCAG 2.1 AA** (recommended)
    - Pros: Legal default in EU, broadly testable, keeps Lighthouse honest
    - Cons: Some surfaces (audio waveform) need extra work
  - **B. WCAG 2.1 AAA**
    - Pros: Best-in-class
    - Cons: Significant engineering cost; not a closed-beta blocker
  - **Choice:** [ ] A [ ] B

---

## Tier 4 — GA / Phase 3

### Step 17 · Mobile apps

- [ ] **Apple Developer account**
  - How: https://developer.apple.com/programs/enroll/ → Enroll. Requires DUNS number (free at https://www.dnb.com/duns-number/get-a-duns.html, ~5 days).
  - Cost: $99/year
  - **Enrolled on:** ________________

- [ ] **Google Play developer account**
  - How: https://play.google.com/console/signup
  - Cost: $25 one-time
  - **Enrolled on:** ________________

- [ ] **Critical alerts entitlement (Apple)** — for emergency push that bypasses Do Not Disturb
  - How: Apple Developer Portal → Certificates → Identifiers → request the entitlement. Apple reviews; ~2–4 weeks. Include a 1-page justification ("Switchboard is a paid receptionist tool; an emergency push that bypasses DND is the core value proposition").
  - **Submitted on:** ________________
  - **Approved on:** ________________

#### Decisions

- [ ] **Stack**
  - **A. Expo + React Native** (recommended)
    - Pros: Fastest to ship, OTA updates, web parity easier
    - Cons: Some native modules require ejecting
  - **B. Native iOS (Swift) + Native Android (Kotlin)**
    - Pros: Best perf, deepest platform integration
    - Cons: 2× engineering, slower iteration
  - **C. Capacitor wrapping the existing web app**
    - Pros: Reuse the entire web codebase
    - Cons: Push reliability and audio playback are weaker than native
  - **Choice:** [ ] A [ ] B [ ] C

---

### Step 18 · Multi-firma rollup

#### Decisions

- [ ] **Plan tier**
  - **Recommendation:** Premium-only (PRD §10 implies). Avoids cannibalizing Pro.
  - **Choice:** [ ] Premium-only   [ ] Pro and above

---

### Step 19 · White-label theming

#### Decisions

- [ ] **Tier threshold for white-label**
  - **A. Premium-only** (recommended)
    - Pros: Justifies Premium price; prevents brand dilution
    - Cons: Pro firmor may push back
  - **B. Pro and above (with platform watermark)**
    - Pros: Wider adoption; can drop watermark for Premium
    - Cons: More code paths; brand consistency harder
  - **Choice:** [ ] A [ ] B

---

## Cross-cutting — validation research (PRD §16)

These are not engineering tasks — they gate Phase 1 build. Track here so engineering knows when validation is green and to align timing.

### Call-tracking pilot (14 days, 10–15 friendly hantverkare)

- [ ] **Pilot firmor recruited**
  - How: Founders' network + 1 LinkedIn post + cold outreach to 30. Aim for 10–15 yes.
  - Incentive: 500 SEK gift card per firma + free 6-month subscription if Phase 1 launches.
  - Cost: ~5 kSEK + gift cards.
  - **Recruited:**
    - [ ] firma 1: ____________________________
    - [ ] firma 2: ____________________________
    - … through 15

- [ ] **Tracking number setup per firma**
  - How: 46elks number with call-forwarding to firma's existing number; we record metadata (time, duration, call-flow status) but not audio at this stage.

- [ ] **Daily SMS to pilot firmor**
  - "Hur många missade samtal hade ni igår? Hur många bokningar?"
  - Tooling: 46elks SMS; spreadsheet to log replies.

- [ ] **Weekly survey**
  - Google Forms; 5 questions about lead loss, time spent on phone, willingness-to-pay laddering.

### Structured interviews (n≥30)

- [ ] **Interview script** with willingness-to-pay laddering ("would you pay 1 495? at 1 695? at 1 295?")
  - Draft: ___________________________
  - Final: ___________________________

- [ ] **Interview log** (one row per interview, fields: firma, trade, anställda, integrations, lost-leads/month, WTP at each price tier, blocker themes)
  - Tool: Google Sheets or Airtable
  - **Log URL:** ________________________________

### Triangulation — public data

- [ ] **Skatteverket ROT-statistik** for VVS-related work types — aggregate per region for 2023–2025
- [ ] **SCB SNI-kod 43.21 / 43.22 / 43.39** firma counts and revenue distribution
- [ ] **Bolagsverket** active VVS / el / snickeri firma counts
- [ ] **Installatörsföretagen** annual reports for VVS/el state of industry
- All compiled into a one-pager for the validation memo.

### Validation memo

- [ ] **Written memo** answering each demand-hypothesis green/yellow/red
  - Reviewers: Founders + 2–3 advisors
  - Format: 3–5 pages
  - **Draft:** ___________________________________________
  - **Approved on:** ________________

---

## Cross-cutting — legal & compliance

- [ ] **DPA template** finalized
  - **Drafted:** [ ]   **Reviewed by counsel:** [ ]

- [ ] **Sub-processor list** in DPA — Google, 46elks, Twilio (if used), Postmark/email vendor, Vercel, GCP, Sentry
  - **Approved:** [ ]

- [ ] **DPIA (Art. 35)** completed before GA, reviewed by external DPO
  - **External DPO retained:** ____________________________
  - **DPIA draft:** ______________________________________
  - **Approved on:** ________________

- [ ] **Recording consent disclosure** — Swedish wording reviewed
  - PRD §9.2 default: `Detta samtal kan spelas in för kvalitets- och utbildningsändamål. Vänligen säg till om du inte vill att samtalet spelas in.`
  - **Final:** _________________________________________

- [ ] **Recording consent default — opt-in vs opt-out**
  - **B2B:** Swedish law tolerates opt-out. **Recommendation:** opt-out (disclosure-based).
  - **B2C:** **Recommendation:** opt-in via verbal disclosure.
  - **Confirmed with counsel:** ________________

- [ ] **F-skatt + bolagsregistrering**
  - **Status:** ________________

- [ ] **ROT-bedömning legal review** before any AI-spoken statements about ROT
  - **Approved on:** ________________

---

## Cross-cutting — observability & cost

- [ ] **Sentry EU project**
  - How: https://sentry.io → Create org → Region: EU → Create projects `switchboard-backend`, `switchboard-bridge`, `switchboard-web`.
  - **DSN backend (1Password ref):** ___________________
  - **DSN bridge:** _____________________________________
  - **DSN web:** _______________________________________

- [ ] **Cost-alert thresholds**
  - **Recommendation:** GCP budget alerts at 50 %, 80 %, 100 % of monthly target. Initial monthly target 5 000 SEK during pre-pilot, 15 000 SEK during pilot.
  - **Configured:** [ ]

---

## Doc hygiene

- Edit this file inline as items are filled.
- When an item is collected, change `[ ]` to `[x]` and paste the value (or 1Password reference for secrets).
- Never commit a real secret. Use `op://` references.
- When a tier is fully green, ping engineering to kick off the corresponding plan tier.

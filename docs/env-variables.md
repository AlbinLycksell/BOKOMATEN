# Environment variables

Every config knob the Switchboard frontend and backend can read, where to put it locally, and where to put it in production. Treat this as the canonical reference — if a new env var lands in code without a row here, the PR isn't done.

Three things to internalise before reading further:

1. **The Next.js app and the FastAPI backend load env vars independently.** Next.js reads from `web/.env.local` (or `web/.env`); it does **not** walk up to the repo root. The backend reads from `.env` and `.env.local` at the **repo root** (configured in `backend/src/switchboard/core/config.py`). One physical secret often has to be set in both places.
2. **`NEXT_PUBLIC_*` is shipped to the browser.** Anything else in the Next.js process is server-only. Never put a secret behind a `NEXT_PUBLIC_*` name.
3. **Secrecy levels in this doc:**
   - 🌐 **Public** — safe to commit, ship to client, log freely.
   - 🟡 **Internal** — server-only; not a credential but reveals topology. Don't log.
   - 🔒 **Secret** — credential or signing key. Rotate on leak. Use Secret Manager in prod.

For where 🔒 secrets physically live (Secret Manager, Vercel, GitHub), how to create / rotate / audit them, and the full secret inventory by category, see [`secrets-management.md`](./secrets-management.md).

### How to read the Dev / Prod columns

- `—` means leave unset; the default in `core/config.py` (or NextAuth's default) is right.
- `(required)` means there is no safe default; the service won't boot or won't function without it.
- `(generate)` means produce the value on the spot — typically `openssl rand -base64 32`.
- A literal value (e.g. `prod`, `jwks`, `gcs`) means set it to exactly that string.
- A pattern (e.g. `postgresql://…`) means set it to a real value matching that shape.

---

## Quick start (local dev)

```bash
# 1. Frontend
cp web/.env.local.example web/.env.local
# Fill in NEXTAUTH_SECRET (openssl rand -base64 32),
# GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET.

# 2. Backend (repo root)
cat > .env.local <<'EOF'
GEMINI_API_KEY=<your gemini key>
EOF
# Other backend defaults are fine for dev. See "Backend variables" below.

# 3. Boot
(cd backend && uv run uvicorn switchboard.app:app --reload)  # :8000
(cd web && pnpm dev)                                          # :3000
```

---

## Loading order

### Frontend (Next.js)

Next.js loads, in priority order: `web/.env.local` → `web/.env.development` (or `.env.production`) → `web/.env`. Vars set on the shell win over all of these. **Restart `next dev` after editing.**

### Backend (FastAPI / pydantic-settings)

`Settings` in `backend/src/switchboard/core/config.py` reads (in order): `<repo-root>/.env` then `<repo-root>/.env.local`. The `env_prefix` is `SWITCHBOARD_` for every field except `gemini_api_key`, which uses the bare alias `GEMINI_API_KEY`.

Environment shell vars override file values. The Settings instance is `lru_cache`'d — restart the process after edits.

---

## Frontend variables (`web/.env.local`)

| Variable | Secrecy | Dev | Prod | Purpose |
|---|---|---|---|---|
| `NEXTAUTH_URL` | 🟡 Internal | `http://localhost:3000` | `https://app.switchboard.se` (required) | Canonical app URL. Without it, NextAuth guesses from `Host` header — fine in dev, breaks behind a proxy. |
| `NEXTAUTH_SECRET` | 🔒 Secret | `(generate)` per dev | `(generate)` once, store in Secret Manager, **same value across all instances** | Signs JWT session tokens. Rotate by overlapping deploys (set new value, redeploy, drain old sessions). |
| `GOOGLE_CLIENT_ID` | 🟡 Internal | `(required)` — your dev OAuth client | `(required)` — separate prod OAuth client | NextAuth Google login. Identifier, not a credential, but tied to the secret below. |
| `GOOGLE_CLIENT_SECRET` | 🔒 Secret | `(required)` — paired with dev id | `(required)` — paired with prod id, in Secret Manager | Pairs with the client id. Rotate via Google Cloud Console. |
| `SWITCHBOARD_BACKEND_INTERNAL_URL` | 🟡 Internal | `—` (defaults to `http://127.0.0.1:8000`) | internal Cloud Run URL or VPC connector, e.g. `https://switchboard-app-internal-…run.app` | Server-only URL the Next.js auth-bootstrap call uses. The bootstrap call should never traverse the public internet in prod. |
| `SWITCHBOARD_BOOTSTRAP_INTERNAL_TOKEN` | 🔒 Secret | `—` (token check is skipped if both sides empty) | `(required)` — must match backend's same-named var | Locks `/api/auth/bootstrap` to known callers. |
| `SWITCHBOARD_FALLBACK_FIRMA_ID` | 🌐 Public | `—` (defaults to demo firma `01J0000FIRM0ANDERSSONSVVS00`) | **leave unset** so a failed bootstrap surfaces an error instead of silently logging into the demo tenant | Demo firma id used when bootstrap fails. Dev/demo only. |
| `SWITCHBOARD_API_BASE` | 🟡 Internal | `—` (defaults to `http://127.0.0.1:8000`) | same as `SWITCHBOARD_BACKEND_INTERNAL_URL` | Server-side API base for SSR fetches in `/admin`. |
| `NEXT_PUBLIC_BACKEND_URL` | 🌐 Public | `—` (Next dev rewrites `/api/proxy/*` to `127.0.0.1:8000`) | `https://api.switchboard.se` | Backend HTTP base used by the `/api/proxy` rewrite. **Browser-visible.** |
| `NEXT_PUBLIC_BACKEND_WS_BASE` | 🌐 Public | `—` (defaults to `ws://localhost:8000` from same host) | `wss://api.switchboard.se` | WebSocket base for inbox + bridge live audio. Bypasses dev rewrites. **Browser-visible.** |

### Setting up Google OAuth (per environment)

You need **two** OAuth clients — one for dev, one for prod. Mixing them is a common deploy mistake (dev secrets end up in prod and vice versa).

1. Google Cloud Console → **APIs & Services** → **Credentials** → **Create OAuth client ID** → "Web application".
2. Authorized redirect URIs (one client per environment):
   - Dev client: `http://localhost:3000/api/auth/callback/google`
   - Prod client: `https://app.switchboard.se/api/auth/callback/google`
3. Copy each client's id and secret into the matching environment.
4. The Google Calendar integration (backend) uses a **separate** OAuth client per environment — see `SWITCHBOARD_GOOGLE_OAUTH_CLIENT_ID` below. Do not reuse credentials across login + Calendar; their consent scopes differ.

---

## Backend variables (repo-root `.env` / `.env.local`)

All names below get a `SWITCHBOARD_` prefix in the actual env file, except `GEMINI_API_KEY` which uses the bare alias.

### Environment & runtime

| Variable | Secrecy | Dev | Prod | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_ENV` | 🌐 Public | `dev` (default) | `prod` | Toggles `is_dev` / `is_prod` checks. Staging instances should set `staging`. |
| `SWITCHBOARD_VERSION` | 🌐 Public | `—` (defaults to `0.1.0`) | `$(git describe --tags)` injected at build time | Surfaced via `/health`. CI sets this. |
| `SWITCHBOARD_REGION` | 🌐 Public | `—` | `europe-west4` | Used in GCS bucket naming. Match the Cloud Run region. |
| `SWITCHBOARD_API_HOST` | 🌐 Public | `—` (defaults to `127.0.0.1`) | `0.0.0.0` (required inside containers so Cloud Run can route) | uvicorn bind host. |
| `SWITCHBOARD_API_PORT` | 🌐 Public | `—` (defaults to `8000`) | `8080` (Cloud Run convention) — set via Cloud Run `--port` flag, not env | uvicorn port. |
| `SWITCHBOARD_CORS_ORIGINS` | 🌐 Public | `—` (defaults to `localhost:3000` pair) | `https://app.switchboard.se` (required) | Comma-separated allowed origins for the Next.js app. |

### Database

| Variable | Secrecy | Dev | Prod | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_DATABASE_URL` | 🔒 Secret | `—` (SQLite at `backend/switchboard.db`) | `postgresql+psycopg://USER:PASS@/DB?host=/cloudsql/INSTANCE` (required) | Cloud SQL Postgres in prod, via the Cloud SQL Auth Proxy or unix socket. |
| `SWITCHBOARD_SEED_DEV_DATA` | 🌐 Public | `—` (defaults to `true`) | `false` (required — never seed demo data into a real tenant DB) | Insert demo firma on boot. |
| `SWITCHBOARD_DB_POOL_SIZE` | 🌐 Public | `—` (5) | `10`–`20` depending on Cloud Run concurrency | SQLAlchemy pool size. |
| `SWITCHBOARD_DB_POOL_MAX_OVERFLOW` | 🌐 Public | `—` (10) | `20` | SQLAlchemy overflow connections. |

### Logging

| Variable | Secrecy | Dev | Prod | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_LOG_LEVEL` | 🌐 Public | `—` (defaults to `INFO`) — set `DEBUG` while diagnosing | `INFO` | One of `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `SWITCHBOARD_LOG_JSON` | 🌐 Public | `—` (defaults to `false`, human-readable) | `true` (required for Cloud Logging / Datadog ingestion) | JSON structured logs. |

### Realtime bridge ↔ application backend

| Variable | Secrecy | Dev | Prod | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_TOOL_DISPATCH_MODE` | 🟡 Internal | `—` (defaults to `local`, in-process) | `http` once Bridge is split out to its own Cloud Run service; otherwise `local` | `local` runs the dispatch handler in-process. `http` POSTs to the App service over the VPC. |
| `SWITCHBOARD_APPLICATION_BACKEND_URL` | 🟡 Internal | `—` | `https://switchboard-app-internal-…run.app` (required when `dispatch_mode=http`) | Where the Bridge reaches the Application Backend. |
| `SWITCHBOARD_BRIDGE_INTERNAL_TOKEN` | 🔒 Secret | `—` | `(required when dispatch_mode=http)` — Secret Manager | Bearer-style token matched on `/api/tools/dispatch`. Lock down or you've shipped an open RPC. |

### Gemini Live (voice AI)

| Variable | Secrecy | Dev | Prod | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_GEMINI_PROVIDER` | 🌐 Public | `—` (defaults to `api_key`) | `vertex` (required for EU residency, DPA, audit logs) | `api_key` hits `generativelanguage.googleapis.com` (US-hosted, no DPA). `vertex` hits Vertex AI in `europe-west4`. |
| `GEMINI_API_KEY` | 🔒 Secret | `(required if provider=api_key)` | `—` (Vertex uses Workload Identity, no key) | Generative Language API key. Note: bare name, no `SWITCHBOARD_` prefix. |
| `SWITCHBOARD_GEMINI_MODEL` | 🌐 Public | `—` (defaults to `models/gemini-3.1-flash-live-preview`) | same default unless GA model id changes | Vertex strips the `models/` prefix automatically. |
| `SWITCHBOARD_GEMINI_VOICE` | 🌐 Public | `—` (defaults to `Aoede`) | same | Default voice. Per-firma override lives in `FirmaSettings.voice`. |
| `SWITCHBOARD_GEMINI_LANGUAGE` | 🌐 Public | `—` (defaults to `sv-SE`) | same | BCP-47 language. |
| `SWITCHBOARD_VERTEX_PROJECT` | 🟡 Internal | `—` | `(required when provider=vertex)` — your GCP project id | GCP project for Vertex Live API. |
| `SWITCHBOARD_VERTEX_LOCATION` | 🌐 Public | `—` | `europe-west4` | Vertex region. Must match data-residency requirements. |

### Google Cloud / storage

| Variable | Secrecy | Dev | Prod | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_STORAGE_MODE` | 🌐 Public | `—` (defaults to `local` → `backend/recordings/{firma_id}/`) | `gcs` (required) | `local` writes to the filesystem. `gcs` writes to per-tenant buckets. |
| `SWITCHBOARD_GCP_PROJECT` | 🟡 Internal | `—` | `(required when storage_mode=gcs)` — GCP project id | Project for storage / KMS. |
| `SWITCHBOARD_GCS_BUCKET_PREFIX` | 🌐 Public | `—` (defaults to `switchboard-rec`) | same default unless multi-region split | Bucket names become `${prefix}-{firma_id}-{region}`. |
| `SWITCHBOARD_GCS_RECORDING_RETENTION_DAYS` | 🌐 Public | `—` (defaults to 7) | `7` (PRD default) | Object lifecycle policy. |
| `SWITCHBOARD_KMS_KEYRING` | 🟡 Internal | `—` | `switchboard` | KMS keyring id. |
| `SWITCHBOARD_KMS_LOCATION` | 🟡 Internal | `—` | `europe-west4` | KMS location. |

Production GCS auth uses **Workload Identity** on Cloud Run — no static service-account JSON in env. Local dev (when testing `gcs` mode) uses `gcloud auth application-default login`.

### Redis (deferred)

| Variable | Secrecy | Dev | Prod | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_REDIS_URL` | 🔒 Secret | `—` (in-process pub-sub is fine for one process) | `(required once multi-process)` — `redis://default:AUTH@…` to Memorystore | The URL itself is a secret because it contains the AUTH token. |

### 46elks (telephony + SMS)

In dev these can stay unset — SMS is simulated (logged, not sent), and inbound voice calls hit the local bridge directly.

| Variable | Secrecy | Dev | Prod | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_ELKS_API_USERNAME` | 🔒 Secret | `—` (SMS simulated) | `(required)` — Secret Manager | 46elks API username. |
| `SWITCHBOARD_ELKS_API_PASSWORD` | 🔒 Secret | `—` | `(required)` — Secret Manager | 46elks API password. |
| `SWITCHBOARD_ELKS_DEFAULT_SENDER_ID` | 🌐 Public | `—` (defaults to `Switchboard`) | `Switchboard` (or your verified alphanumeric, 3–11 chars) | Platform-wide SMS sender id. |
| `SWITCHBOARD_ELKS_WEBHOOK_SECRET` | 🔒 Secret | `—` | `(required)` — Secret Manager; matches the value configured in 46elks dashboard | HMAC secret for inbound voice webhooks. |

### Fortnox

| Variable | Secrecy | Dev | Prod | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_FORTNOX_CLIENT_ID` | 🟡 Internal | `—` (integration disabled) | `(required when integration enabled)` | OAuth app id. |
| `SWITCHBOARD_FORTNOX_CLIENT_SECRET` | 🔒 Secret | `—` | `(required when integration enabled)` — Secret Manager | OAuth secret. |
| `SWITCHBOARD_FORTNOX_REDIRECT_URI` | 🌐 Public | `http://localhost:8000/api/integrations/fortnox/callback` (if testing locally) | `https://app.switchboard.se/api/integrations/fortnox/callback` | Must match the Fortnox app config exactly. |

### Visma eEkonomi

| Variable | Secrecy | Dev | Prod | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_VISMA_CLIENT_ID` | 🟡 Internal | `—` (integration disabled) | `(required when integration enabled)` | OAuth app id. |
| `SWITCHBOARD_VISMA_CLIENT_SECRET` | 🔒 Secret | `—` | `(required)` — Secret Manager | OAuth secret. |
| `SWITCHBOARD_VISMA_REDIRECT_URI` | 🌐 Public | `http://localhost:8000/api/integrations/visma/callback` (if testing locally) | `https://app.switchboard.se/api/integrations/visma/callback` | Must match Visma app config. |

### Google Calendar (separate from NextAuth login)

| Variable | Secrecy | Dev | Prod | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_GOOGLE_OAUTH_CLIENT_ID` | 🟡 Internal | `—` (integration disabled) | `(required)` — distinct from frontend `GOOGLE_CLIENT_ID` (Calendar scopes ≠ login scopes) | Calendar OAuth client id. |
| `SWITCHBOARD_GOOGLE_OAUTH_CLIENT_SECRET` | 🔒 Secret | `—` | `(required)` — Secret Manager | Calendar OAuth secret. |
| `SWITCHBOARD_GOOGLE_CALENDAR_REDIRECT_URI` | 🌐 Public | `http://localhost:8000/api/integrations/google-calendar/callback` (if testing locally) | `https://app.switchboard.se/api/integrations/google-calendar/callback` | Must match Google Cloud OAuth app. |

### Stripe billing

| Variable | Secrecy | Dev | Prod | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_STRIPE_API_KEY` | 🔒 Secret | `sk_test_…` from Stripe dashboard test mode | `sk_live_…` (required) — Secret Manager | Stripe secret key. |
| `SWITCHBOARD_STRIPE_WEBHOOK_SECRET` | 🔒 Secret | `whsec_…` from `stripe listen --forward-to localhost:8000/api/billing/webhook` | `whsec_…` from the prod webhook endpoint — Secret Manager | Webhook signature verification. |
| `SWITCHBOARD_STRIPE_PRICE_STARTER` | 🌐 Public | `price_…` from test mode | `price_…` from live mode (required) | Starter plan price id. |
| `SWITCHBOARD_STRIPE_PRICE_PROFESSIONAL` | 🌐 Public | test `price_…` | live `price_…` (required) | Professional plan price id. |
| `SWITCHBOARD_STRIPE_PRICE_PREMIUM` | 🌐 Public | test `price_…` | live `price_…` (required) | Premium plan price id. |
| `SWITCHBOARD_STRIPE_PORTAL_RETURN_URL` | 🌐 Public | `http://localhost:3000/settings` | `https://app.switchboard.se/settings` | Where the Stripe customer portal returns to. |

### Auth (NextAuth ↔ FastAPI handshake)

| Variable | Secrecy | Dev | Prod | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_AUTH_MODE` | 🌐 Public | `—` (defaults to `dev_header` — backend trusts `X-Firma-Id`) | `jwks` (required — verifies Bearer JWTs against NextAuth JWKS) | `dev_header` is a development-only shortcut; never run prod with it. |
| `SWITCHBOARD_AUTH_JWKS_URL` | 🌐 Public | `—` (unused in `dev_header` mode) | `https://app.switchboard.se/api/auth/jwks` (required when `auth_mode=jwks`) | Public JWKS endpoint of the Next.js auth handler. |
| `SWITCHBOARD_AUTH_AUDIENCE` | 🌐 Public | `—` (defaults to `switchboard-backend`) | same default | JWT `aud` claim the backend accepts. |
| `SWITCHBOARD_AUTH_ISSUER` | 🌐 Public | `—` | `https://app.switchboard.se` (required) | JWT `iss` claim the backend accepts. |
| `SWITCHBOARD_ALLOWED_SIGNUP_DOMAINS` | 🌐 Public | `—` (open — any domain can bootstrap) | `your-customer-domains.se,…` for closed beta; `—` once self-serve | Comma-separated email-domain allowlist for new firmas. |
| `SWITCHBOARD_BOOTSTRAP_INTERNAL_TOKEN` | 🔒 Secret | `—` (token check skipped if both sides empty) | `(required)` — must match frontend's same-named var, Secret Manager | Locks `/api/auth/bootstrap`. |

### Observability

| Variable | Secrecy | Dev | Prod | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_SENTRY_DSN` | 🔒 Secret | `—` (Sentry off in dev — local logs are enough) | `https://…@sentry.io/…` (required) — Secret Manager | The DSN includes a write-only key but is treated as secret to discourage abuse. |
| `SWITCHBOARD_SENTRY_ENVIRONMENT` | 🌐 Public | `—` (inherits `env`) | `prod` (or `staging` for staging) — explicit override | Sentry environment tag. |

### Cost telemetry (tunable)

These are not secrets — they're rate cards. Update when GA pricing changes. Same in dev and prod unless you're deliberately modelling.

| Variable | Default | Purpose |
|---|---|---|
| `SWITCHBOARD_COST_RATE_PROMPT_TOKEN_SEK` | `0.0000125` | Vertex Live prompt token rate (SEK). |
| `SWITCHBOARD_COST_RATE_RESPONSE_TOKEN_SEK` | `0.000050` | Vertex Live response token rate (SEK). |
| `SWITCHBOARD_COST_RATE_TELEPHONY_MINUTE_SEK` | `0.40` | 46elks inbound voice rate (SEK / min). |
| `SWITCHBOARD_COST_RATE_SMS_SEK` | `0.30` | 46elks SMS rate (SEK / message). |
| `SWITCHBOARD_COST_OVERHEAD_SEK` | `0.30` | Per-call overhead surcharge (SEK). |

### CLI / tooling

| Variable | Secrecy | Dev | Prod | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_EVAL_SLACK_WEBHOOK` | 🔒 Secret | `—` | `https://hooks.slack.com/services/…` — GitHub repo secret on the eval workflow | Optional Slack webhook for `scripts/run_eval.py` failure pings. Set on the **CI** environment, not on Cloud Run. |

---

## Deployment topology

### Cloud Run (production reference)

**Two services**, deployed from `backend/Dockerfile.app` and `backend/Dockerfile.bridge`:

```bash
# App service — full HTTP API + dashboard backend
gcloud run deploy switchboard-app \
  --image=europe-west4-docker.pkg.dev/PROJECT/switchboard/app:$SHA \
  --region=europe-west4 \
  --service-account=switchboard-app@PROJECT.iam.gserviceaccount.com \
  --set-env-vars=SWITCHBOARD_ENV=prod,SWITCHBOARD_AUTH_MODE=jwks,\
SWITCHBOARD_GEMINI_PROVIDER=vertex,SWITCHBOARD_STORAGE_MODE=gcs,\
SWITCHBOARD_TOOL_DISPATCH_MODE=local,SWITCHBOARD_LOG_JSON=true,\
SWITCHBOARD_SEED_DEV_DATA=false \
  --set-secrets=SWITCHBOARD_DATABASE_URL=switchboard-db-url:latest,\
SWITCHBOARD_BOOTSTRAP_INTERNAL_TOKEN=bootstrap-token:latest,\
SWITCHBOARD_BRIDGE_INTERNAL_TOKEN=bridge-token:latest,\
SWITCHBOARD_ELKS_API_USERNAME=elks-user:latest,\
SWITCHBOARD_ELKS_API_PASSWORD=elks-pass:latest,\
SWITCHBOARD_ELKS_WEBHOOK_SECRET=elks-webhook:latest,\
SWITCHBOARD_STRIPE_API_KEY=stripe-api-key:latest,\
SWITCHBOARD_STRIPE_WEBHOOK_SECRET=stripe-webhook:latest,\
SWITCHBOARD_FORTNOX_CLIENT_SECRET=fortnox-secret:latest,\
SWITCHBOARD_VISMA_CLIENT_SECRET=visma-secret:latest,\
SWITCHBOARD_GOOGLE_OAUTH_CLIENT_SECRET=gcal-secret:latest,\
SWITCHBOARD_SENTRY_DSN=sentry-dsn:latest

# Bridge service — same secrets pattern; smaller env subset
gcloud run deploy switchboard-bridge ...
```

**Rules:**

- 🔒 **Secrets** → `--set-secrets`, never `--set-env-vars`. They route through Secret Manager so rotation is a one-line `gcloud secrets versions add` and Cloud Run auto-picks the new value on next request.
- 🟡 **Internal** → `--set-env-vars`. They're not credentials but Cloud Run's audit log treats them as visible config.
- 🌐 **Public** → `--set-env-vars`. Same place; no different trust level.

Setting up secrets:

```bash
echo -n "$VALUE" | gcloud secrets create switchboard-db-url --data-file=- --replication-policy=user-managed --locations=europe-west4
gcloud secrets add-iam-policy-binding switchboard-db-url \
  --member=serviceAccount:switchboard-app@PROJECT.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

### Vercel (frontend)

The Next.js app is deployable to Vercel. Project settings → Environment variables. Set per environment (Production / Preview / Development):

| Class | Variables | Vercel "Sensitive" toggle |
|---|---|---|
| 🔒 Secret | `NEXTAUTH_SECRET`, `GOOGLE_CLIENT_SECRET`, `SWITCHBOARD_BOOTSTRAP_INTERNAL_TOKEN` | **on** |
| 🟡 Internal | `GOOGLE_CLIENT_ID`, `SWITCHBOARD_BACKEND_INTERNAL_URL`, `SWITCHBOARD_API_BASE`, `NEXTAUTH_URL` | optional |
| 🌐 Public | `NEXT_PUBLIC_BACKEND_URL`, `NEXT_PUBLIC_BACKEND_WS_BASE` | off |

`SWITCHBOARD_BACKEND_INTERNAL_URL` should point at the **internal** Cloud Run URL (or VPC connector), not the public one — the bootstrap call should never traverse the public internet.

`SWITCHBOARD_FALLBACK_FIRMA_ID` should be set on **Development / Preview only**, never on Production.

### GitHub Actions (CI / eval)

CI doesn't need most secrets. The eval job needs:

```yaml
env:
  GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  SWITCHBOARD_EVAL_SLACK_WEBHOOK: ${{ secrets.EVAL_SLACK_WEBHOOK }}
```

Repository secrets, not environment variables. Never use `${{ env.* }}` for secrets — it doesn't redact in logs.

### Local dev (single dev machine)

- Frontend → `web/.env.local` (template at `web/.env.local.example`).
- Backend → repo-root `.env` (committable defaults like rate cards) + repo-root `.env.local` (your `GEMINI_API_KEY`).
- `.env.local` is git-ignored at both layers — verified.

---

## Environment cheat-sheets

### Minimum dev set (just enough to boot login + voice test)

```bash
# web/.env.local
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=<openssl rand -base64 32>
GOOGLE_CLIENT_ID=<dev oauth client>
GOOGLE_CLIENT_SECRET=<dev oauth secret>

# .env.local at repo root
GEMINI_API_KEY=<your gemini key>
```

That's it — the rest fall back to sensible dev defaults.

### Minimum prod set (Cloud Run + Vercel)

**Backend (Cloud Run env vars):**
```
SWITCHBOARD_ENV=prod
SWITCHBOARD_AUTH_MODE=jwks
SWITCHBOARD_AUTH_ISSUER=https://app.switchboard.se
SWITCHBOARD_AUTH_JWKS_URL=https://app.switchboard.se/api/auth/jwks
SWITCHBOARD_GEMINI_PROVIDER=vertex
SWITCHBOARD_VERTEX_PROJECT=<gcp project>
SWITCHBOARD_STORAGE_MODE=gcs
SWITCHBOARD_GCP_PROJECT=<gcp project>
SWITCHBOARD_LOG_JSON=true
SWITCHBOARD_SEED_DEV_DATA=false
SWITCHBOARD_API_HOST=0.0.0.0
SWITCHBOARD_CORS_ORIGINS=https://app.switchboard.se
```

**Backend (Cloud Run secrets — Secret Manager):**
```
SWITCHBOARD_DATABASE_URL
SWITCHBOARD_BOOTSTRAP_INTERNAL_TOKEN
SWITCHBOARD_ELKS_API_USERNAME
SWITCHBOARD_ELKS_API_PASSWORD
SWITCHBOARD_ELKS_WEBHOOK_SECRET
SWITCHBOARD_STRIPE_API_KEY
SWITCHBOARD_STRIPE_WEBHOOK_SECRET
SWITCHBOARD_SENTRY_DSN
+ any integration secrets actually enabled (Fortnox, Visma, Google Calendar)
```

**Frontend (Vercel Production env):**
```
NEXTAUTH_URL=https://app.switchboard.se
NEXTAUTH_SECRET=<sensitive>
GOOGLE_CLIENT_ID=<prod oauth client>
GOOGLE_CLIENT_SECRET=<sensitive>
SWITCHBOARD_BACKEND_INTERNAL_URL=<internal cloud run url>
SWITCHBOARD_API_BASE=<internal cloud run url>
SWITCHBOARD_BOOTSTRAP_INTERNAL_TOKEN=<sensitive, matches backend>
NEXT_PUBLIC_BACKEND_URL=https://api.switchboard.se
NEXT_PUBLIC_BACKEND_WS_BASE=wss://api.switchboard.se
```

---

## Secrecy summary

🔒 **Secrets — Secret Manager / Vercel "Sensitive" / GitHub repo secret. Rotate on leak. Never log:**

- `NEXTAUTH_SECRET`
- `GOOGLE_CLIENT_SECRET` (frontend login + backend Calendar are separate clients, separate secrets)
- `SWITCHBOARD_GOOGLE_OAUTH_CLIENT_SECRET`
- `SWITCHBOARD_BOOTSTRAP_INTERNAL_TOKEN`
- `SWITCHBOARD_BRIDGE_INTERNAL_TOKEN`
- `SWITCHBOARD_DATABASE_URL`
- `SWITCHBOARD_REDIS_URL`
- `GEMINI_API_KEY`
- `SWITCHBOARD_ELKS_API_USERNAME`, `SWITCHBOARD_ELKS_API_PASSWORD`, `SWITCHBOARD_ELKS_WEBHOOK_SECRET`
- `SWITCHBOARD_FORTNOX_CLIENT_SECRET`, `SWITCHBOARD_VISMA_CLIENT_SECRET`
- `SWITCHBOARD_STRIPE_API_KEY`, `SWITCHBOARD_STRIPE_WEBHOOK_SECRET`
- `SWITCHBOARD_SENTRY_DSN`
- `SWITCHBOARD_EVAL_SLACK_WEBHOOK`

🟡 **Internal — server-only, but topology not credentials:**

- `NEXTAUTH_URL`
- `GOOGLE_CLIENT_ID`, `SWITCHBOARD_GOOGLE_OAUTH_CLIENT_ID`
- `SWITCHBOARD_BACKEND_INTERNAL_URL`, `SWITCHBOARD_API_BASE`, `SWITCHBOARD_APPLICATION_BACKEND_URL`
- `SWITCHBOARD_FORTNOX_CLIENT_ID`, `SWITCHBOARD_VISMA_CLIENT_ID`
- `SWITCHBOARD_GCP_PROJECT`, `SWITCHBOARD_VERTEX_PROJECT`
- `SWITCHBOARD_KMS_KEYRING`, `SWITCHBOARD_KMS_LOCATION`
- `SWITCHBOARD_TOOL_DISPATCH_MODE`

🌐 **Public — committable, browser-safe, log-safe:** every other variable in this document.

---

## Adding a new variable

1. Add the field to `Settings` in `backend/src/switchboard/core/config.py` (backend) or read it via `process.env.X` (frontend).
2. Add a row to the appropriate table above. Choose the secrecy level deliberately. Fill the **Dev** and **Prod** columns explicitly — `—` is fine for "leave unset" but never blank.
3. If 🔒 — add a `--set-secrets` entry to the Cloud Run deploy reference and a Vercel "Sensitive" entry if it's frontend.
4. If frontend, add it to `web/.env.local.example` so a fresh clone boots cleanly.
5. PR description must call out the new variable explicitly so Ops can pre-create the secret.

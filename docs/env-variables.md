# Environment variables

Every config knob the Switchboard frontend and backend can read, where to put it locally, and where to put it in production. Treat this as the canonical reference — if a new env var lands in code without a row here, the PR isn't done.

Three things to internalise before reading further:

1. **The Next.js app and the FastAPI backend load env vars independently.** Next.js reads from `web/.env.local` (or `web/.env`); it does **not** walk up to the repo root. The backend reads from `.env` and `.env.local` at the **repo root** (configured in `backend/src/switchboard/core/config.py`). One physical secret often has to be set in both places.
2. **`NEXT_PUBLIC_*` is shipped to the browser.** Anything else in the Next.js process is server-only. Never put a secret behind a `NEXT_PUBLIC_*` name.
3. **Secrecy levels in this doc:**
   - 🌐 **Public** — safe to commit, ship to client, log freely.
   - 🟡 **Internal** — server-only; not a credential but reveals topology. Don't log.
   - 🔒 **Secret** — credential or signing key. Rotate on leak. Use Secret Manager in prod.

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

| Variable | Required | Secrecy | Purpose |
|---|---|---|---|
| `NEXTAUTH_URL` | dev: optional · prod: **yes** | 🟡 Internal | Canonical app URL. Without it, NextAuth guesses from `Host` header — fine in dev, breaks behind a proxy. |
| `NEXTAUTH_SECRET` | **yes** | 🔒 Secret | Signs JWT session tokens. Must match across instances. Rotate by overlapping deploys. |
| `GOOGLE_CLIENT_ID` | **yes** | 🟡 Internal | NextAuth Google login. Identifier, not a credential, but tied to the secret below. |
| `GOOGLE_CLIENT_SECRET` | **yes** | 🔒 Secret | Pairs with the client id. Rotate via Google Cloud Console. |
| `SWITCHBOARD_BACKEND_INTERNAL_URL` | dev: optional · prod: **yes** | 🟡 Internal | Server-only URL the Next.js auth-bootstrap call uses. Default `http://127.0.0.1:8000`. |
| `SWITCHBOARD_BOOTSTRAP_INTERNAL_TOKEN` | prod: **yes** | 🔒 Secret | Shared secret matched against the backend's same-named var. Locks `/api/auth/bootstrap` to known callers. |
| `SWITCHBOARD_FALLBACK_FIRMA_ID` | no | 🌐 Public | Demo firma id used when bootstrap fails. Dev/demo only. |
| `SWITCHBOARD_API_BASE` | no | 🟡 Internal | Server-side API base for SSR fetches in `/admin`. Default `http://127.0.0.1:8000`. |
| `NEXT_PUBLIC_BACKEND_URL` | no | 🌐 Public | Backend HTTP base used by the `/api/proxy` rewrite. Default `http://127.0.0.1:8000`. **Browser-visible.** |
| `NEXT_PUBLIC_BACKEND_WS_BASE` | no | 🌐 Public | WebSocket base for inbox + bridge live audio. Bypasses dev rewrites. **Browser-visible.** |

### Setting up Google OAuth (one-off)

1. Google Cloud Console → **APIs & Services** → **Credentials** → **Create OAuth client ID** → "Web application".
2. Authorized redirect URIs:
   - `http://localhost:3000/api/auth/callback/google` (dev)
   - `https://app.switchboard.se/api/auth/callback/google` (prod)
3. Copy the client id and secret into `web/.env.local`.
4. The Google Calendar integration (backend) uses a **separate** OAuth client — see `SWITCHBOARD_GOOGLE_OAUTH_CLIENT_ID` below. Do not reuse credentials across login + Calendar; their consent scopes differ.

---

## Backend variables (repo-root `.env` / `.env.local`)

All names below get a `SWITCHBOARD_` prefix in the actual env file, except `GEMINI_API_KEY` which uses the bare alias.

### Environment & runtime

| Variable | Required | Secrecy | Default | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_ENV` | no | 🌐 Public | `dev` | One of `dev`, `staging`, `prod`. Toggles `is_dev` / `is_prod` checks. |
| `SWITCHBOARD_VERSION` | no | 🌐 Public | `0.1.0` | Surfaced via `/health`. CI sets this from `git describe`. |
| `SWITCHBOARD_REGION` | no | 🌐 Public | `europe-west4` | Used in GCS bucket naming. |
| `SWITCHBOARD_API_HOST` | no | 🌐 Public | `127.0.0.1` | uvicorn bind host. Set to `0.0.0.0` in containers. |
| `SWITCHBOARD_API_PORT` | no | 🌐 Public | `8000` | uvicorn port. |
| `SWITCHBOARD_CORS_ORIGINS` | prod: **yes** | 🌐 Public | `localhost:3000` pair | Comma-separated allowed origins for the Next.js app. |

### Database

| Variable | Required | Secrecy | Default | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_DATABASE_URL` | prod: **yes** | 🔒 Secret | local SQLite | SQLAlchemy URL. Postgres in prod (`postgresql://user:pass@host/db`). The full URL is a secret because it contains the password. |
| `SWITCHBOARD_SEED_DEV_DATA` | no | 🌐 Public | `true` | Insert demo firma on boot. **Set to `false` in prod.** |
| `SWITCHBOARD_DB_POOL_SIZE` | no | 🌐 Public | `5` | SQLAlchemy pool size. |
| `SWITCHBOARD_DB_POOL_MAX_OVERFLOW` | no | 🌐 Public | `10` | SQLAlchemy overflow connections. |

### Logging

| Variable | Required | Secrecy | Default | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_LOG_LEVEL` | no | 🌐 Public | `INFO` | One of `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `SWITCHBOARD_LOG_JSON` | no | 🌐 Public | `false` | JSON structured logs (Cloud Run, Datadog). |

### Realtime bridge ↔ application backend

| Variable | Required | Secrecy | Default | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_TOOL_DISPATCH_MODE` | no | 🟡 Internal | `local` | `local` (in-process, single binary) or `http` (Bridge POSTs to App). |
| `SWITCHBOARD_APPLICATION_BACKEND_URL` | when split: **yes** | 🟡 Internal | `http://127.0.0.1:8000` | Where the Bridge reaches the Application Backend in `http` mode. |
| `SWITCHBOARD_BRIDGE_INTERNAL_TOKEN` | when split: **yes** | 🔒 Secret | empty | Bearer-style token matched on `/api/tools/dispatch`. Lock down or you've shipped an open RPC. |

### Gemini Live (voice AI)

| Variable | Required | Secrecy | Default | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_GEMINI_PROVIDER` | no | 🌐 Public | `api_key` | `api_key` (dev / eval) or `vertex` (prod, EU residency). |
| `GEMINI_API_KEY` | dev: **yes** if `provider=api_key` | 🔒 Secret | empty | Generative Language API key. Note: bare name, no prefix. |
| `SWITCHBOARD_GEMINI_MODEL` | no | 🌐 Public | `models/gemini-3.1-flash-live-preview` | Model id. Vertex strips the `models/` prefix automatically. |
| `SWITCHBOARD_GEMINI_VOICE` | no | 🌐 Public | `Aoede` | Default voice name. Per-firma override lives in `FirmaSettings.voice`. |
| `SWITCHBOARD_GEMINI_LANGUAGE` | no | 🌐 Public | `sv-SE` | BCP-47 language. |
| `SWITCHBOARD_VERTEX_PROJECT` | when `provider=vertex`: **yes** | 🟡 Internal | empty | GCP project for Vertex Live API. |
| `SWITCHBOARD_VERTEX_LOCATION` | no | 🌐 Public | `europe-west4` | Vertex region. |

### Google Cloud / storage

| Variable | Required | Secrecy | Default | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_STORAGE_MODE` | no | 🌐 Public | `local` | `local` (filesystem) or `gcs` (per-tenant buckets). |
| `SWITCHBOARD_GCP_PROJECT` | prod: **yes** | 🟡 Internal | empty | GCP project id for storage / KMS. |
| `SWITCHBOARD_GCS_BUCKET_PREFIX` | no | 🌐 Public | `switchboard-rec` | Prefix for per-firma bucket names. |
| `SWITCHBOARD_GCS_RECORDING_RETENTION_DAYS` | no | 🌐 Public | `7` | Recording lifecycle in days. |
| `SWITCHBOARD_KMS_KEYRING` | no | 🟡 Internal | `switchboard` | KMS keyring id. |
| `SWITCHBOARD_KMS_LOCATION` | no | 🟡 Internal | `europe-west4` | KMS location. |

Production GCS auth uses **Workload Identity** on Cloud Run — no static service-account JSON in env. Local dev uses `gcloud auth application-default login`.

### Redis (deferred)

| Variable | Required | Secrecy | Default | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_REDIS_URL` | when used: **yes** | 🔒 Secret | empty | Memorystore URL for cross-process pub-sub. The URL itself is a secret because it contains the AUTH token. |

### 46elks (telephony + SMS)

| Variable | Required | Secrecy | Default | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_ELKS_API_USERNAME` | live: **yes** | 🔒 Secret | empty | 46elks API username. Empty → SMS is simulated (logged, not sent). |
| `SWITCHBOARD_ELKS_API_PASSWORD` | live: **yes** | 🔒 Secret | empty | 46elks API password. |
| `SWITCHBOARD_ELKS_DEFAULT_SENDER_ID` | no | 🌐 Public | `Switchboard` | Platform-wide SMS sender id (3–11 chars, alpha). |
| `SWITCHBOARD_ELKS_WEBHOOK_SECRET` | live: **yes** | 🔒 Secret | empty | HMAC secret for inbound voice webhooks. |

### Fortnox

| Variable | Required | Secrecy | Default | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_FORTNOX_CLIENT_ID` | live: **yes** | 🟡 Internal | empty | OAuth app id. |
| `SWITCHBOARD_FORTNOX_CLIENT_SECRET` | live: **yes** | 🔒 Secret | empty | OAuth secret. |
| `SWITCHBOARD_FORTNOX_REDIRECT_URI` | live: **yes** | 🌐 Public | prod URL | Must match the Fortnox app config exactly. |

### Visma eEkonomi

| Variable | Required | Secrecy | Default | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_VISMA_CLIENT_ID` | live: **yes** | 🟡 Internal | empty | OAuth app id. |
| `SWITCHBOARD_VISMA_CLIENT_SECRET` | live: **yes** | 🔒 Secret | empty | OAuth secret. |
| `SWITCHBOARD_VISMA_REDIRECT_URI` | live: **yes** | 🌐 Public | prod URL | Must match Visma app config. |

### Google Calendar (separate from NextAuth login)

| Variable | Required | Secrecy | Default | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_GOOGLE_OAUTH_CLIENT_ID` | live: **yes** | 🟡 Internal | empty | Calendar OAuth client. **Distinct from frontend `GOOGLE_CLIENT_ID`** (different scopes). |
| `SWITCHBOARD_GOOGLE_OAUTH_CLIENT_SECRET` | live: **yes** | 🔒 Secret | empty | Calendar OAuth secret. |
| `SWITCHBOARD_GOOGLE_CALENDAR_REDIRECT_URI` | live: **yes** | 🌐 Public | prod URL | Must match Google Cloud OAuth app. |

### Stripe billing

| Variable | Required | Secrecy | Default | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_STRIPE_API_KEY` | billing on: **yes** | 🔒 Secret | empty | Stripe secret key (`sk_live_...` / `sk_test_...`). |
| `SWITCHBOARD_STRIPE_WEBHOOK_SECRET` | billing on: **yes** | 🔒 Secret | empty | `whsec_...` for webhook signature verification. |
| `SWITCHBOARD_STRIPE_PRICE_STARTER` | billing on: **yes** | 🌐 Public | empty | `price_...` id for Starter plan. |
| `SWITCHBOARD_STRIPE_PRICE_PROFESSIONAL` | billing on: **yes** | 🌐 Public | empty | `price_...` id for Professional plan. |
| `SWITCHBOARD_STRIPE_PRICE_PREMIUM` | billing on: **yes** | 🌐 Public | empty | `price_...` id for Premium plan. |
| `SWITCHBOARD_STRIPE_PORTAL_RETURN_URL` | no | 🌐 Public | prod URL | Where the Stripe customer portal returns to. |

### Auth (NextAuth ↔ FastAPI handshake)

| Variable | Required | Secrecy | Default | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_AUTH_MODE` | prod: **yes** | 🌐 Public | `dev_header` | `dev_header` trusts `X-Firma-Id`; `jwks` verifies Bearer JWTs against NextAuth JWKS. **Always `jwks` in prod.** |
| `SWITCHBOARD_AUTH_JWKS_URL` | when `auth_mode=jwks`: **yes** | 🌐 Public | empty | Public JWKS endpoint of the Next.js auth handler. |
| `SWITCHBOARD_AUTH_AUDIENCE` | no | 🌐 Public | `switchboard-backend` | JWT `aud` claim the backend accepts. |
| `SWITCHBOARD_AUTH_ISSUER` | prod: **yes** | 🌐 Public | prod URL | JWT `iss` claim the backend accepts. |
| `SWITCHBOARD_ALLOWED_SIGNUP_DOMAINS` | no | 🌐 Public | empty (open) | Comma-separated email-domain allowlist for new firmas. |
| `SWITCHBOARD_BOOTSTRAP_INTERNAL_TOKEN` | prod: **yes** | 🔒 Secret | empty | Pairs with the same-named frontend var. Required for `/api/auth/bootstrap`. |

### Observability

| Variable | Required | Secrecy | Default | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_SENTRY_DSN` | prod: **yes** | 🔒 Secret | empty | Sentry DSN. The DSN includes a write-only key but is treated as a secret to discourage abuse. |
| `SWITCHBOARD_SENTRY_ENVIRONMENT` | no | 🌐 Public | inherits `env` | Override Sentry environment tag. |

### Cost telemetry (tunable)

These are not secrets — they're rate cards. Update when GA pricing changes.

| Variable | Default | Purpose |
|---|---|---|
| `SWITCHBOARD_COST_RATE_PROMPT_TOKEN_SEK` | `0.0000125` | Vertex Live prompt token rate (SEK). |
| `SWITCHBOARD_COST_RATE_RESPONSE_TOKEN_SEK` | `0.000050` | Vertex Live response token rate (SEK). |
| `SWITCHBOARD_COST_RATE_TELEPHONY_MINUTE_SEK` | `0.40` | 46elks inbound voice rate (SEK / min). |
| `SWITCHBOARD_COST_RATE_SMS_SEK` | `0.30` | 46elks SMS rate (SEK / message). |
| `SWITCHBOARD_COST_OVERHEAD_SEK` | `0.30` | Per-call overhead surcharge (SEK). |

### CLI / tooling

| Variable | Required | Secrecy | Default | Purpose |
|---|---|---|---|---|
| `SWITCHBOARD_EVAL_SLACK_WEBHOOK` | no | 🔒 Secret | empty | Optional Slack webhook for `scripts/run_eval.py` failure pings. |

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
| 🌐 Public | `NEXT_PUBLIC_BACKEND_URL`, `NEXT_PUBLIC_BACKEND_WS_BASE`, `SWITCHBOARD_FALLBACK_FIRMA_ID` | off |

`SWITCHBOARD_BACKEND_INTERNAL_URL` should point at the **internal** Cloud Run URL (or VPC connector), not the public one — the bootstrap call should never traverse the public internet.

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
2. Add a row to the appropriate table above. Choose the secrecy level deliberately.
3. If 🔒 — add a `--set-secrets` entry to the Cloud Run deploy reference and a Vercel "Sensitive" entry if it's frontend.
4. If frontend, add it to `web/.env.local.example` so a fresh clone boots cleanly.
5. PR description must call out the new variable explicitly so Ops can pre-create the secret.

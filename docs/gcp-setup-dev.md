# GCP setup — developer environment

The 15-minute path to a working dev setup. Most of [`gcp-setup.md`](./gcp-setup.md) — Terraform, Cloud SQL, KMS, VPC, Cloud Run — is **prod-only** and intentionally skipped here. Dev runs uvicorn + pnpm on your laptop, talks to a SQLite file, simulates SMS, and uses the Gemini Generative Language API directly (no Vertex). You touch GCP only for the things that genuinely need a Google identity: OAuth login, Calendar integration, optional Vertex testing.

---

## TL;DR — minimum path

If you only want login + voice test working, you need **two things**:

1. A **Gemini API key** from [Google AI Studio](https://aistudio.google.com/apikey) → put in repo-root `.env.local` as `GEMINI_API_KEY`.
2. A **Google OAuth client** (for NextAuth login) → put `client id` and `client secret` in `web/.env.local`.

That's it. Skip the rest of this doc unless you need Calendar integration, Vertex testing, or a clean isolated dev GCP project.

```bash
# repo root
cat > .env.local <<'EOF'
GEMINI_API_KEY=AIza...
EOF

# web/
cp web/.env.local.example web/.env.local
# edit and fill GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, NEXTAUTH_SECRET
```

---

## What dev needs vs doesn't

| Capability | Needed in dev? | How |
|---|---|---|
| Gemini Live | ✅ yes | API key from AI Studio. Or Vertex if testing prod path. |
| Google OAuth (NextAuth login) | ✅ yes | Personal OAuth client in any GCP project. |
| Backend Postgres | ❌ no | SQLite at `backend/switchboard.db` is the dev default. |
| KMS | ❌ no | Recordings go to filesystem (`SWITCHBOARD_STORAGE_MODE=local`). |
| VPC / Workload Identity | ❌ no | Single-process local dev, no service-to-service hops. |
| Cloud Run | ❌ no | uvicorn + pnpm dev. |
| Cloud SQL Auth Proxy | ❌ no | See above — no SQL. |
| 46elks live API | ❌ no | Empty creds → SMS is simulated (logged, not sent). |
| Stripe live | ❌ no | Use `sk_test_…` keys in dev only when actually testing billing. |
| Sentry | ❌ no | Local logs are enough. |
| Calendar integration | optional | Needs separate OAuth client + APIs enabled (see §6). |
| Vertex Gemini path | optional | Needs project + ADC + API enabled (see §5). |
| GCS recording storage | optional | Needs ADC + a personal bucket if testing the `gcs` path. |

---

## 0. Prerequisites

- A Google account (personal or work — doesn't matter for dev).
- `gcloud` CLI installed: `brew install --cask google-cloud-sdk`.
- Authenticated: `gcloud auth login`.

You **don't** need a GCP organization for dev. A standalone project under your personal account is fine — orgs are a prod concern (billing aggregation, IAM scoping across multiple projects).

---

## 1. (Recommended) Create a dev project

You can skip this if you're happy putting OAuth clients into the GCP "default" project Google auto-creates. The downside is mixing dev creds with anything else you have in that project. Cleaner: dedicated `switchboard-dev`.

```bash
DEV_PROJECT="switchboard-dev"          # globally unique — pick something else if taken
gcloud projects create "$DEV_PROJECT" --name "Switchboard dev"
gcloud config set project "$DEV_PROJECT"
```

If your account is part of an org with billing, link a billing account so you can enable APIs that require it (Vertex, Calendar do; basic OAuth does not):

```bash
BILLING="0X0X0X-XXXXXX-XXXXXX"   # gcloud beta billing accounts list
gcloud beta billing projects link "$DEV_PROJECT" --billing-account "$BILLING"
```

If you don't have a billing account, the project still works — you'll just be limited to free-tier APIs.

---

## 2. Get a Gemini API key (no project plumbing required)

Fastest path. Skips the whole Vertex / IAM / ADC setup.

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
2. Click **Create API key** → choose your dev project (or "Create API key in new project").
3. Copy the `AIza…` value into repo-root `.env.local`:

```bash
echo 'GEMINI_API_KEY=AIza...' > .env.local
```

This routes through `generativelanguage.googleapis.com` (US-hosted, no DPA) — fine for dev, never for prod. Free tier is generous enough for repeated voice tests during local development.

The backend defaults to `SWITCHBOARD_GEMINI_PROVIDER=api_key`, so no other env var is needed.

---

## 3. Create the OAuth client for NextAuth login

This is the one piece of GCP plumbing you can't skip — login won't work without it.

1. **Enable the API:**
   ```bash
   gcloud services enable iamcredentials.googleapis.com
   ```
   (OAuth client creation itself doesn't need an API enabled, but the consent screen does.)

2. **Configure the OAuth consent screen:**

   Go to [Console → APIs & Services → OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent).

   - User type: **External**
   - App name: `Switchboard (dev)` so it's obvious in the consent prompt.
   - User support email: your email.
   - Developer contact: your email.
   - Scopes: leave default for now (you can add Calendar scopes later if needed).
   - Test users: add your own Google account email — required while the app is in "Testing" mode.

3. **Create the OAuth client:**

   [Console → APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials) → **Create Credentials** → **OAuth client ID**.

   - Application type: **Web application**
   - Name: `switchboard-dev-login`
   - Authorized redirect URIs:
     - `http://localhost:3000/api/auth/callback/google`

4. **Copy the client id and secret into `web/.env.local`:**

   ```bash
   GOOGLE_CLIENT_ID=<your-client-id>.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=GOCSPX-...
   NEXTAUTH_URL=http://localhost:3000
   NEXTAUTH_SECRET=$(openssl rand -base64 32)
   ```

5. **Restart `next dev`** — env vars only load at boot.

---

## 4. (Optional) Set up Application Default Credentials

Only needed if you'll touch Vertex (§5), Calendar (§6), or GCS (§7) from the local backend. Not needed for the minimum path.

```bash
gcloud auth application-default login
```

This drops a JSON credential at `~/.config/gcloud/application_default_credentials.json` that GCP client libraries pick up automatically. Set the quota project so usage is billed correctly:

```bash
gcloud auth application-default set-quota-project "$DEV_PROJECT"
```

---

## 5. (Optional) Enable Vertex AI to test the prod Gemini path

The prod build uses `SWITCHBOARD_GEMINI_PROVIDER=vertex` for EU residency + DPA + audit logs. To exercise the same code path locally:

```bash
gcloud services enable aiplatform.googleapis.com --project "$DEV_PROJECT"

# Grant your user the right to call Vertex (only needed once)
USER=$(gcloud config get-value account)
gcloud projects add-iam-policy-binding "$DEV_PROJECT" \
  --member="user:$USER" \
  --role="roles/aiplatform.user"
```

Then in repo-root `.env.local`:

```bash
SWITCHBOARD_GEMINI_PROVIDER=vertex
SWITCHBOARD_VERTEX_PROJECT=switchboard-dev
SWITCHBOARD_VERTEX_LOCATION=europe-west4
# unset GEMINI_API_KEY — Vertex uses ADC, not a key
```

Vertex Live preview models may require allowlist access; if you get a `404` or `permission denied` on the model name, file an internal request via the GCP console and use `api_key` provider until it lands.

---

## 6. (Optional) Calendar integration OAuth client

**Distinct from the login OAuth client.** The Calendar integration uses different consent scopes, so it needs a separate client to avoid scope creep on the login flow.

1. **Enable the API:**
   ```bash
   gcloud services enable calendar-json.googleapis.com --project "$DEV_PROJECT"
   ```

2. **Create the client** (same Console UI as §3):
   - Name: `switchboard-dev-calendar`
   - Authorized redirect URIs:
     - `http://localhost:8000/api/integrations/google-calendar/callback`

3. **Add the scope** to the OAuth consent screen:
   - `https://www.googleapis.com/auth/calendar` (full access — required to create / move bookings)

4. **Put the credentials in repo-root `.env.local`:**

   ```bash
   SWITCHBOARD_GOOGLE_OAUTH_CLIENT_ID=<calendar-client-id>.apps.googleusercontent.com
   SWITCHBOARD_GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-...
   SWITCHBOARD_GOOGLE_CALENDAR_REDIRECT_URI=http://localhost:8000/api/integrations/google-calendar/callback
   ```

---

## 7. (Optional) GCS for recording storage

Only do this if you specifically want to exercise the `gcs` storage path. The default `local` mode writes to `backend/recordings/` and is fine for everything else.

```bash
gcloud services enable storage.googleapis.com --project "$DEV_PROJECT"
gcloud storage buckets create gs://switchboard-dev-rec-$USER \
  --location=europe-west4 \
  --uniform-bucket-level-access
```

```bash
# repo-root .env.local
SWITCHBOARD_STORAGE_MODE=gcs
SWITCHBOARD_GCP_PROJECT=switchboard-dev
SWITCHBOARD_GCS_BUCKET_PREFIX=switchboard-dev-rec-$USER
```

ADC (§4) handles auth; no service-account JSON keys.

---

## 8. (Optional) Wire up the secret-management story locally

If you want to test the prod-shape "secrets come from Secret Manager" loading without provisioning prod, you can use Secret Manager in the dev project:

```bash
gcloud services enable secretmanager.googleapis.com --project "$DEV_PROJECT"
echo -n "$NEXTAUTH_SECRET" | gcloud secrets create nextauth-secret --data-file=- --replication-policy=automatic
gcloud secrets versions list nextauth-secret
```

Locally you'd still load from `.env.local` — Secret Manager mounting only happens in the Cloud Run runtime. If you want to mirror Cloud Run behaviour on your laptop, use [`berglas`](https://github.com/GoogleCloudPlatform/berglas) or `gcloud secrets versions access latest --secret=NAME` in a shell wrapper before launching uvicorn.

For 99% of dev work, this is unnecessary. The full inventory + creation procedure lives in [`secrets-management.md`](./secrets-management.md).

---

## 9. Verify the setup

```bash
# Backend boots
make backend
# → http://127.0.0.1:8000/health should return {"status":"ok"}

# Web boots
make web
# → http://localhost:3000 redirects to /marketing

# Login works (after step 3)
open http://localhost:3000/login
# → "Logga in med Google" → consent screen → /inbox

# Voice test works (after step 2)
open http://localhost:3000/admin
# → scroll to "Röstprov" → "Starta test-samtal"
# → see the bridge open and Gemini Live respond
```

If any step fails, the troubleshooting tree:

- **Login error `client_id is required`:** §3 not done, or `web/.env.local` missing / not picked up. Restart `next dev`.
- **Voice test pre-flight fails:** `GEMINI_API_KEY` missing in repo-root `.env.local` (§2), or you set `SWITCHBOARD_GEMINI_PROVIDER=vertex` without doing §5.
- **Vertex returns 404 / permission denied:** model not allowlisted yet — fall back to `api_key` and continue dev work.
- **Calendar OAuth fails with `redirect_uri_mismatch`:** the URI in your client config (§6) must exactly match `SWITCHBOARD_GOOGLE_CALENDAR_REDIRECT_URI` in `.env.local` — `localhost` ≠ `127.0.0.1` to OAuth.

---

## 10. Cleaning up

If you're done with the dev project:

```bash
gcloud projects delete switchboard-dev
```

OAuth clients are deleted with the project. Secret Manager secrets, GCS buckets, billing exports — all gone. (You have 30 days to undo the deletion if you regret it.)

---

## Differences from prod (`gcp-setup.md`)

| Aspect | Dev | Prod |
|---|---|---|
| Provisioning | Manual `gcloud` commands, ~15 min | Terraform, ~2 hours pair work |
| Database | SQLite (`backend/switchboard.db`) | Cloud SQL Postgres in private VPC |
| Storage | Local filesystem | Per-tenant GCS buckets, KMS-encrypted |
| Gemini | API key (US-hosted) | Vertex AI in `europe-west4` |
| Auth handshake | `dev_header` (X-Firma-Id trusted) | `jwks` (Bearer JWT verified against NextAuth JWKS) |
| Deploys | `make dev` | Cloud Run via GitHub Actions |
| Secrets | `.env.local` files | Secret Manager + Vercel Sensitive |
| Domains | `localhost` | `app.switchboard.se`, `bridge.switchboard.se` |
| Bridge ↔ App | In-process (`tool_dispatch_mode=local`) | HTTP over VPC (`tool_dispatch_mode=http`) |
| Min instances | 0 | Bridge ≥ 2 (PRD §8.10) |
| Cost | Free tier | ~500–1500 SEK/mo target |

When in doubt: dev never needs prod's complexity. If you're tempted to set up Cloud SQL or KMS in dev, you almost certainly don't need to.

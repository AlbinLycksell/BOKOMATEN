# GCP setup — developer environment

A single shared `switchboard-dev` project owns all dev-time GCP resources. New developers don't bootstrap a project — they're added as members and create their own OAuth client + API key inside it. This means: one Vertex allowlist request, one OAuth consent screen, one Cloud Logging dashboard, one billing line. Less per-dev friction, faster onboarding.

Most of [`gcp-setup.md`](./gcp-setup.md) — Terraform, Cloud SQL, KMS, VPC, Cloud Run — is **prod-only** and intentionally skipped here. Dev runs uvicorn + pnpm on your laptop, talks to a SQLite file, simulates SMS, and uses Gemini via either an API key or Vertex AI in the shared dev project.

### Two paths through this doc

- **You're the project bootstrapper** (lead engineer / founder, doing this first time): start at §0 and run the whole thing. You'll set up the project, consent screen, optional Vertex allowlist, and IAM. About 20 minutes.
- **You're a developer joining an existing team**: ask the project owner to add you as a test user on the consent screen and grant `roles/aiplatform.user` (only if you'll use Vertex). Then **skip to §3** — create your personal OAuth client + Gemini key. About 5 minutes.

Per-developer resources you'll create inside the shared project:

- One OAuth client for NextAuth login: `switchboard-dev-login-<your-handle>` (required).
- One Gemini API key: also tied to your handle (required).
- Optional: a second OAuth client `switchboard-dev-calendar-<your-handle>` for Calendar integration testing; a personal GCS bucket if testing the `gcs` storage path.

---

## What dev needs vs doesn't

| Capability | Needed in dev? | How |
|---|---|---|
| Shared GCP project (`switchboard-dev`) | ✅ yes | Bootstrapped once in §1; new devs added via IAM in §2. |
| Google OAuth (NextAuth login) | ✅ yes | Per-dev OAuth client created in §3. |
| Gemini Live | ✅ yes | Per-dev API key (§4). Vertex is optional and covered in §6. |
| Backend Postgres | ❌ no | SQLite at `backend/switchboard.db` is the dev default. |
| KMS | ❌ no | Recordings go to filesystem (`SWITCHBOARD_STORAGE_MODE=local`). |
| VPC / Workload Identity | ❌ no | Single-process local dev, no service-to-service hops. |
| Cloud Run | ❌ no | uvicorn + pnpm dev. |
| Cloud SQL Auth Proxy | ❌ no | See above — no SQL. |
| 46elks live API | ❌ no | Empty creds → SMS is simulated (logged, not sent). |
| Stripe live | ❌ no | Use `sk_test_…` keys in dev only when actually testing billing. |
| Sentry | ❌ no | Local logs are enough. |
| Calendar integration | optional | Separate OAuth client + API enabled (§7). |
| Vertex Gemini path | optional | Vertex AI API + ADC quota project (§6). |
| GCS recording storage | optional | Personal bucket + ADC (§8). |

---

## 0. Prerequisites

- A Google account (personal or work — doesn't matter for dev).
- `gcloud` CLI installed: `brew install --cask google-cloud-sdk`.
- Authenticated: `gcloud auth login`.

You **don't** need a GCP organization for dev. A standalone project under your personal account is fine — orgs are a prod concern (billing aggregation, IAM scoping across multiple projects).

---

## 1. Bootstrap the shared `switchboard-dev` project (once, by the project owner)

> Already exists? **Skip this section** — go to §2 to be added as a member, then §3 to create your own OAuth client.

The project id needs to be globally unique. The team standard is `switchboard-dev`; if that's taken on your org, fall back to `switchboard-dev-<orgslug>` (e.g. `switchboard-dev-siftlab`).

```bash
DEV_PROJECT="switchboard-dev"
gcloud projects create "$DEV_PROJECT" --name "Switchboard dev"
gcloud config set project "$DEV_PROJECT"
```

Link a billing account so Vertex / Calendar APIs can be enabled (they require billing even on free tier):

```bash
BILLING="0X0X0X-XXXXXX-XXXXXX"           # gcloud beta billing accounts list
gcloud beta billing projects link "$DEV_PROJECT" --billing-account "$BILLING"
```

If your org has a tag policy you'll see a warning right after `projects create`:

> *Project '…' lacks an 'environment' tag. Please create or add a tag with key 'environment' and a value like 'Production', 'Development', …*

That's a warning, not a block — but bind the tag now (some orgs harden it to a hard block later, and billing rollups by environment depend on it):

```bash
ORG_ID=$(gcloud organizations list --format='value(ID)' | head -1)
TAG_KEY_ID=$(gcloud resource-manager tags keys list \
  --parent="organizations/$ORG_ID" \
  --filter='shortName=environment' --format='value(name)' | sed 's|tagKeys/||')
TAG_VALUE_ID=$(gcloud resource-manager tags values list \
  --parent="tagKeys/$TAG_KEY_ID" \
  --filter='shortName=Development' --format='value(name)' | sed 's|tagValues/||')
PROJECT_NUMBER=$(gcloud projects describe "$DEV_PROJECT" --format='value(projectNumber)')

gcloud resource-manager tags bindings create \
  --location=global \
  --tag-value="tagValues/$TAG_VALUE_ID" \
  --parent="//cloudresourcemanager.googleapis.com/projects/$PROJECT_NUMBER"
```

If `gcloud organizations list` returns nothing, your account isn't in a GCP org → no tag policy applies → skip this step.

Enable the always-needed APIs in one shot:

```bash
gcloud services enable \
  iamcredentials.googleapis.com \
  generativelanguage.googleapis.com \
  --project "$DEV_PROJECT"
# Add aiplatform / calendar-json / storage at §6 / §7 / §8 only if needed.
```

**Configure the OAuth consent screen** (one-off; new devs are added as test users in §2 instead of reconfiguring this):

[Console → APIs & Services → OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent).

- User type: **External**
- App name: `Switchboard (dev)`
- User support email + developer contact: a shared dev alias (e.g. `dev@switchboard.se`) so it doesn't churn when individual devs leave.
- Scopes: leave default. (§7 adds the Calendar scope when needed.)
- Test users: the bootstrapper's email — more added in §2.

**Set the cost guardrail** so a runaway Vertex test can't burn through a credit card:

```bash
gcloud billing budgets create \
  --billing-account "$BILLING" \
  --display-name "switchboard-dev guardrail" \
  --budget-amount=100 \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=0.9 \
  --threshold-rule=percent=1.0
```

100 SEK/mo is a generous dev budget; alerts fire at 50 / 90 / 100 %.

---

## 2. Add a developer to the shared project (once per new hire)

Run by the project owner whenever a new developer joins.

```bash
DEV_EMAIL="alice@switchboard.se"
DEV_PROJECT="switchboard-dev"

# Minimum: lets them use Gemini, create OAuth clients, see logs.
gcloud projects add-iam-policy-binding "$DEV_PROJECT" \
  --member="user:$DEV_EMAIL" --role="roles/serviceusage.serviceUsageConsumer"
gcloud projects add-iam-policy-binding "$DEV_PROJECT" \
  --member="user:$DEV_EMAIL" --role="roles/iam.serviceAccountUser"
gcloud projects add-iam-policy-binding "$DEV_PROJECT" \
  --member="user:$DEV_EMAIL" --role="roles/oauthconfig.editor"
gcloud projects add-iam-policy-binding "$DEV_PROJECT" \
  --member="user:$DEV_EMAIL" --role="roles/logging.viewer"

# If they'll use Vertex (§6):
gcloud projects add-iam-policy-binding "$DEV_PROJECT" \
  --member="user:$DEV_EMAIL" --role="roles/aiplatform.user"
```

Add them as a **test user** on the OAuth consent screen so the login flow accepts their Google account: [Console → OAuth consent screen → Test users → Add users](https://console.cloud.google.com/apis/credentials/consent).

Once that's done, the new dev runs `gcloud config set project switchboard-dev` and continues at §3.

---

## 3. Create your personal OAuth client for NextAuth login

Each developer creates their own OAuth client inside the shared project. Different `client_secret` per developer scopes blast radius — one leaked dev secret doesn't compromise everyone.

[Console → APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials) → **Create Credentials** → **OAuth client ID**.

- Application type: **Web application**
- Name: `switchboard-dev-login-<your-handle>` (e.g. `switchboard-dev-login-tj`)
- Authorized redirect URIs:
  - `http://localhost:3000/api/auth/callback/google`

Copy the credentials into `web/.env.local`:

```bash
GOOGLE_CLIENT_ID=<your-client-id>.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-...
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=$(openssl rand -base64 32)
```

Restart `next dev` — env vars only load at boot.

---

## 4. Get your personal Gemini API key

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
2. Click **Create API key** → select the **`switchboard-dev`** project.
3. Name it `switchboard-dev-<your-handle>` so it's obvious whose key it is.
4. Copy the `AIza…` value into repo-root `.env.local`:

```bash
echo 'GEMINI_API_KEY=AIza...' > .env.local
```

Per-dev keys (rather than a shared key) make rotation safer — a leaked key only blocks one dev when revoked.

This routes through `generativelanguage.googleapis.com` (US-hosted, no DPA) — fine for dev, never for prod. Free tier is generous enough for repeated voice tests during local development.

The backend defaults to `SWITCHBOARD_GEMINI_PROVIDER=api_key`, so no other env var is needed unless you opt into Vertex in §6.

---

## 5. (Optional) Set up Application Default Credentials

Only needed if you'll touch Vertex (§6), Calendar (§7), or GCS (§8) from the local backend.

```bash
gcloud auth application-default login
```

This drops a JSON credential at `~/.config/gcloud/application_default_credentials.json` that GCP client libraries pick up automatically. Set the quota project so usage is billed correctly:

```bash
gcloud auth application-default set-quota-project "$DEV_PROJECT"
```

---

## 6. (Optional) Enable Vertex AI to test the prod Gemini path

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

## 7. (Optional) Calendar integration OAuth client

**Distinct from the login OAuth client.** Calendar uses different consent scopes, so it needs a separate client per developer to avoid scope creep on the login flow.

1. **Enable the API** (project owner; one-off):
   ```bash
   gcloud services enable calendar-json.googleapis.com --project "$DEV_PROJECT"
   ```

2. **Create your personal client** (same Console UI as §3):
   - Name: `switchboard-dev-calendar-<your-handle>`
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

## 8. (Optional) GCS for recording storage

Only do this if you specifically want to exercise the `gcs` storage path. The default `local` mode writes to `backend/recordings/` and is fine for everything else.

Per-dev buckets — keep one dev's recordings out of another's namespace:

```bash
HANDLE="$(whoami)"
gcloud services enable storage.googleapis.com --project switchboard-dev
gcloud storage buckets create "gs://switchboard-dev-rec-$HANDLE" \
  --location=europe-west4 \
  --uniform-bucket-level-access
```

```bash
# repo-root .env.local
SWITCHBOARD_STORAGE_MODE=gcs
SWITCHBOARD_GCP_PROJECT=switchboard-dev
SWITCHBOARD_GCS_BUCKET_PREFIX=switchboard-dev-rec-<your-handle>
```

ADC (§5) handles auth; no service-account JSON keys.

---

## 9. (Optional) Wire up the secret-management story locally

If you want to test the prod-shape "secrets come from Secret Manager" loading without provisioning prod, you can use Secret Manager in the dev project:

```bash
gcloud services enable secretmanager.googleapis.com --project "$DEV_PROJECT"
echo -n "$NEXTAUTH_SECRET" | gcloud secrets create nextauth-secret --data-file=- --replication-policy=automatic
gcloud secrets versions list nextauth-secret
```

Locally you'd still load from `.env.local` — Secret Manager mounting only happens in the Cloud Run runtime. If you want to mirror Cloud Run behaviour on your laptop, use [`berglas`](https://github.com/GoogleCloudPlatform/berglas) or `gcloud secrets versions access latest --secret=NAME` in a shell wrapper before launching uvicorn.

For 99% of dev work, this is unnecessary. The full inventory + creation procedure lives in [`secrets-management.md`](./secrets-management.md).

---

## 10. Verify the setup

```bash
# Backend boots
make backend
# → http://127.0.0.1:8000/health should return {"status":"ok"}

# Web boots
make web
# → http://localhost:3000 redirects to /marketing

# Login works (after §3)
open http://localhost:3000/login
# → "Logga in med Google" → consent screen → /inbox

# Voice test works (after §4)
open http://localhost:3000/admin
# → scroll to "Röstprov" → "Starta test-samtal"
# → see the bridge open and Gemini Live respond
```

If any step fails, the troubleshooting tree:

- **Login error `client_id is required`:** §3 not done, or `web/.env.local` missing / not picked up. Restart `next dev`.
- **Login error `Access blocked: This app's request is invalid`:** you weren't added as a test user on the OAuth consent screen — ask the project owner to run §2.
- **Voice test pre-flight fails:** `GEMINI_API_KEY` missing in repo-root `.env.local` (§4), or you set `SWITCHBOARD_GEMINI_PROVIDER=vertex` without doing §6.
- **Vertex returns 404 / permission denied:** model not allowlisted yet — fall back to `api_key` and continue dev work; the project owner can request allowlist access once for the whole team.
- **Calendar OAuth fails with `redirect_uri_mismatch`:** the URI in your client config (§7) must exactly match `SWITCHBOARD_GOOGLE_CALENDAR_REDIRECT_URI` in `.env.local` — `localhost` ≠ `127.0.0.1` to OAuth.

---

## 11. Cleaning up

The shared project stays — what gets cleaned up depends on whether you're a leaving developer or the project bootstrapper.

**Leaving developer:** delete only your own per-dev resources, not the project itself.

```bash
# Delete your personal OAuth clients (Console → APIs & Services → Credentials)
# - switchboard-dev-login-<your-handle>
# - switchboard-dev-calendar-<your-handle>  (if you created one)

# Revoke your personal Gemini API key (https://aistudio.google.com/apikey)
# - switchboard-dev-<your-handle>

# Delete your personal GCS bucket (if you created one in §8)
gcloud storage rm -r "gs://switchboard-dev-rec-$HANDLE"
```

The project owner then removes you from IAM:

```bash
gcloud projects remove-iam-policy-binding switchboard-dev \
  --member="user:$DEV_EMAIL" --role="roles/aiplatform.user"
# repeat for every role granted in §2
```

Also remove them from the OAuth consent screen test-user list.

**Project owner sunsetting the whole dev environment:** rare, but the command is:

```bash
gcloud projects delete switchboard-dev
```

(30-day undo window.)

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

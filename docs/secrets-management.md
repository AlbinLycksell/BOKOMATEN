# Secrets management

How Switchboard stores, mounts, rotates, and audits secrets across dev, staging, prod, and CI. The list of which env vars are secrets lives in [`env-variables.md`](./env-variables.md); this doc is about the **storage layer** underneath them.

The reading order, if you're new:

1. [`env-variables.md`](./env-variables.md) — what each variable does and what to set it to per environment.
2. **This doc** — where the actual secret values physically live and who has access.
3. [`gcp-setup.md`](./gcp-setup.md) — one-time bootstrap of the GCP project, Secret Manager bucket, IAM bindings.

---

## The four storage tiers

Switchboard has exactly four places a secret value can legitimately exist. Anything outside these is a leak.

### 1. Google Secret Manager (production backend)

**Use for:** every 🔒 secret consumed by the FastAPI backend on Cloud Run.

**Why:** Secret Manager versions every value, integrates with Cloud Run `--set-secrets` for zero-downtime rotation, and writes every access to Cloud Audit Logs. Cloud Run resolves `:latest` on each cold-start, so rotation is `gcloud secrets versions add` + nothing else.

**Region:** all secrets are pinned to `europe-west4` to match data-residency. The Terraform config in `gcp-setup.md` already enforces this with a user-managed replication policy.

**Naming:** lowercase kebab-case, no `switchboard-` prefix (the project name implies it). `db-url`, `bootstrap-token`, `stripe-api-key`, `elks-pass`, etc. The mapping from Cloud Run env var → secret name is explicit in the deploy command (see `env-variables.md` Cloud Run reference).

### 2. Vercel Environment Variables (production frontend)

**Use for:** every 🔒 secret consumed by the Next.js app at build or runtime.

**Why:** Vercel injects env vars per environment (Production / Preview / Development), encrypts them at rest, and the **Sensitive** toggle prevents the value from ever being read back through the dashboard or API once set. The Vercel runtime is the only place that can decrypt them.

**Setup:** Project → Settings → Environment Variables → "Add". Always tick **Sensitive** for 🔒 secrets, and pick the environment(s) the secret applies to.

### 3. GitHub Actions Repository Secrets (CI)

**Use for:** secrets only used by CI workflows (`SWITCHBOARD_EVAL_SLACK_WEBHOOK`, `GEMINI_API_KEY` for the eval job, deployment service-account keys).

**Why:** GitHub redacts the value automatically in workflow logs, scopes access to the repo, and exposes them only via `${{ secrets.NAME }}`.

**Setup:** Repo → Settings → Secrets and variables → Actions → "New repository secret".

**Don't:** put CI secrets in `vars` (they're not redacted) or `env` blocks at the workflow level (same — only `secrets` is redacted).

### 4. Local `.env.local` files (developer machines)

**Use for:** every secret a developer needs to run the app locally.

**Locations:** `web/.env.local` (frontend) and repo-root `.env.local` (backend). Both git-ignored. Verified — see `web/.gitignore` line 4 (`.env*.local`).

**Each developer manages their own values:**
- Personal Google OAuth client (don't share dev OAuth credentials between devs — when one dev's app gets locked or leaked, you don't want everyone else affected).
- Personal `GEMINI_API_KEY` (unless a shared "switchboard-dev" key exists in the org's password manager).
- Stripe **test mode** keys are shared across devs and can live in a team password manager (1Password / Bitwarden), since they only access test mode.

**Onboarding:** the `web/.env.local.example` template documents required keys. New devs copy → fill in. We do not commit a "default dev secret" anywhere; that's how shared dev secrets become prod secrets by accident.

---

## What is and isn't a secret

A variable is 🔒 **Secret** if **any** of these are true:

- Possessing the value lets an attacker impersonate the app to a third party (`STRIPE_API_KEY`, `ELKS_API_PASSWORD`, OAuth client secrets).
- Possessing the value lets an attacker forge a session or bypass auth (`NEXTAUTH_SECRET`, `BOOTSTRAP_INTERNAL_TOKEN`, `BRIDGE_INTERNAL_TOKEN`).
- Possessing the value gives direct access to a data store (`DATABASE_URL`, `REDIS_URL` — both contain credentials in the URL).
- Possessing the value lets an attacker write to your error/observability sink at scale (`SENTRY_DSN` — write-only key, but still rate-limit-abusable).

A variable is **not** secret just because:

- It's only on the server (that's "Internal", not "Secret"). Topology — backend URLs, project ids, JWKS endpoints — leaks topology, not credentials.
- It's a config the user can see anyway (CORS origins, plan price ids).
- It looks technical (`KMS_KEYRING`, `STORAGE_MODE`).

When in doubt, classify as Internal first; promote to Secret only when the threat model demands it. Over-classifying everything as Secret means real rotation discipline gets ignored.

---

## The secret inventory

This is the canonical list. Every entry has a single source of truth (one of the four tiers above), and the env-var name on each consumer side.

### Auth & sessions

| Secret value | Where the truth lives | Backend env var | Frontend env var | Notes |
|---|---|---|---|---|
| NextAuth JWT signing key | Vercel Sensitive (prod), `web/.env.local` (dev) | — | `NEXTAUTH_SECRET` | Generate per environment with `openssl rand -base64 32`. Same value across all Next.js instances or sessions invalidate. |
| Frontend Google OAuth client secret (login) | Vercel Sensitive (prod), `web/.env.local` (dev) | — | `GOOGLE_CLIENT_SECRET` | Distinct dev / prod OAuth clients. |
| Backend Google OAuth client secret (Calendar) | Secret Manager (prod), repo `.env.local` (dev) | `SWITCHBOARD_GOOGLE_OAUTH_CLIENT_SECRET` | — | **Different** OAuth client than the login one — different scopes. |
| Bootstrap shared secret (Next.js → FastAPI) | Secret Manager + Vercel Sensitive (must match) | `SWITCHBOARD_BOOTSTRAP_INTERNAL_TOKEN` | `SWITCHBOARD_BOOTSTRAP_INTERNAL_TOKEN` | Pair must agree byte-for-byte. Locks `/api/auth/bootstrap` to known callers. |

### Service-to-service

| Secret value | Where the truth lives | Backend env var | Notes |
|---|---|---|---|
| Bridge → App dispatch token | Secret Manager | `SWITCHBOARD_BRIDGE_INTERNAL_TOKEN` | Required only when `SWITCHBOARD_TOOL_DISPATCH_MODE=http` (Bridge split out). Both services need it. |

### External provider credentials

| Secret value | Where the truth lives | Backend env var | Notes |
|---|---|---|---|
| Gemini API key | Repo `.env.local` (dev only); not used in prod | `GEMINI_API_KEY` | Prod uses Vertex with Workload Identity — no static key. Bare name, no `SWITCHBOARD_` prefix. |
| 46elks API username | Secret Manager | `SWITCHBOARD_ELKS_API_USERNAME` | Empty in dev → SMS is simulated (logged, not sent). |
| 46elks API password | Secret Manager | `SWITCHBOARD_ELKS_API_PASSWORD` | Pair with username. |
| 46elks webhook HMAC secret | Secret Manager + 46elks dashboard | `SWITCHBOARD_ELKS_WEBHOOK_SECRET` | Must match the value configured on the 46elks side. |
| Stripe secret key | Secret Manager (prod, `sk_live_…`); `.env.local` (dev, `sk_test_…`) | `SWITCHBOARD_STRIPE_API_KEY` | Test mode keys are shareable across devs; live keys never leave Secret Manager. |
| Stripe webhook signing secret | Secret Manager (prod); `.env.local` (dev, from `stripe listen`) | `SWITCHBOARD_STRIPE_WEBHOOK_SECRET` | Per-endpoint — prod webhook endpoint and dev `stripe listen` produce different `whsec_…` values. |
| Fortnox OAuth client secret | Secret Manager | `SWITCHBOARD_FORTNOX_CLIENT_SECRET` | Disable integration in dev rather than committing test creds. |
| Visma OAuth client secret | Secret Manager | `SWITCHBOARD_VISMA_CLIENT_SECRET` | Same. |

### Infrastructure (URLs that contain credentials)

| Secret value | Where the truth lives | Backend env var | Notes |
|---|---|---|---|
| Postgres URL | Secret Manager | `SWITCHBOARD_DATABASE_URL` | Cloud SQL connection via unix socket / Cloud SQL Auth Proxy. The full URL (`postgresql+psycopg://USER:PASS@/DB?host=/cloudsql/INSTANCE`) is treated as secret because of the embedded password. |
| Redis URL | Secret Manager | `SWITCHBOARD_REDIS_URL` | Memorystore URL. The AUTH token is part of the URL (`redis://default:AUTH@host:port`). |

### Observability

| Secret value | Where the truth lives | Backend env var | Notes |
|---|---|---|---|
| Sentry DSN | Secret Manager | `SWITCHBOARD_SENTRY_DSN` | Write-only, but still rate-limit-abusable. Per environment (separate dev / staging / prod projects in Sentry). |

### CI / tooling

| Secret value | Where the truth lives | Used by | Notes |
|---|---|---|---|
| Slack webhook for eval failures | GitHub repo secret `EVAL_SLACK_WEBHOOK` | `scripts/run_eval.py` workflow | Read into `SWITCHBOARD_EVAL_SLACK_WEBHOOK` env var inside the workflow. Not used by Cloud Run. |
| GCP deploy service-account key | GitHub repo secret `GCP_SA_KEY` *(if not using Workload Identity Federation)* | Deploy workflows | **Prefer Workload Identity Federation** over a static JSON key. The Cloud Run + GitHub Actions OIDC integration is documented in `gcp-setup.md`. |

---

## Per-environment expectations

### Local dev — minimum

The smallest set that boots login + voice test:

```
# web/.env.local
NEXTAUTH_SECRET=<openssl rand -base64 32>
GOOGLE_CLIENT_ID=<dev oauth client>
GOOGLE_CLIENT_SECRET=<dev oauth secret>

# .env.local (repo root)
GEMINI_API_KEY=<your gemini key>
```

Stripe / 46elks / Fortnox / Visma stay empty in dev unless you're explicitly testing them. The app falls back to simulated SMS, no live calls, no live billing.

### Staging — full prod-shape, isolated

Staging has its own copy of every prod secret, in its own GCP project (or, at minimum, its own set of Secret Manager secrets). **Never share secrets between staging and prod.** A staging leak should have zero blast radius on prod.

### Production — Secret Manager owns the truth

Every 🔒 secret in the inventory above must exist as a Secret Manager secret in the prod project, and be referenced by the Cloud Run deploy with `--set-secrets`. The deploy command in `env-variables.md` is the source of truth for which secret name maps to which env var.

For the Vercel side, the production environment's "Sensitive" entries must match.

---

## Creating a new secret

```bash
# 1. Create the secret in Secret Manager (no value yet)
gcloud secrets create stripe-api-key \
  --replication-policy=user-managed \
  --locations=europe-west4

# 2. Add the value as version 1
echo -n "$VALUE" | gcloud secrets versions add stripe-api-key --data-file=-

# 3. Grant the Cloud Run service account access
gcloud secrets add-iam-policy-binding stripe-api-key \
  --member=serviceAccount:switchboard-app@PROJECT.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# 4. Wire it into the Cloud Run deploy
gcloud run services update switchboard-app \
  --update-secrets=SWITCHBOARD_STRIPE_API_KEY=stripe-api-key:latest \
  --region=europe-west4
```

The `:latest` reference means Cloud Run picks up the newest version on every cold start — no redeploy needed for rotation.

---

## Rotating a secret

```bash
# 1. Add a new version
echo -n "$NEW_VALUE" | gcloud secrets versions add stripe-api-key --data-file=-

# 2. Force Cloud Run to pick it up (new revision = new cold start)
gcloud run services update switchboard-app \
  --region=europe-west4 \
  --update-labels=rotated-at=$(date +%s)

# 3. Disable the previous version once the new one is confirmed working
gcloud secrets versions disable 1 --secret=stripe-api-key
```

For 🔒 secrets that must agree across two systems (`BOOTSTRAP_INTERNAL_TOKEN`, `BRIDGE_INTERNAL_TOKEN`), rotation is a two-step:

1. Add the new value to **both** sides as a fallback (code accepts old OR new).
2. Once the new value is propagated everywhere, remove the old.

Without this, you'll lock the bootstrap or bridge calls during the propagation window.

### When to rotate

- **Always:** on departure of someone who had access.
- **Always:** on suspected leak — committed accidentally, leaked in a screenshot, surfaced in a log.
- **Periodic:** at least annually for long-lived secrets (database URL, integration secrets). Stripe and Sentry expose this in their dashboards; do it when they remind you.
- **Per environment:** never propagate a rotated prod secret to dev or vice versa. Distinct values, distinct rotation cadence.

---

## Access control

Three principal types matter:

| Principal | What it can read | How |
|---|---|---|
| Cloud Run runtime service account (`switchboard-app@…`) | Secrets in its own `--set-secrets` mount | `roles/secretmanager.secretAccessor` per secret, **never** at project level. |
| Engineers (humans) | Whatever they were granted via IAM Conditions | `roles/secretmanager.secretAccessor` on a per-secret basis. Audit who has it quarterly. |
| GitHub Actions deploys | Whatever the Workload Identity binding allows | OIDC short-lived tokens, no static JSON. Configured in `gcp-setup.md`. |

**Prohibited:** granting `roles/secretmanager.admin` at project level to engineers. That role can read the value of every secret. Reserve it for the lead engineer + one backup, both with 2FA.

---

## Pre-commit hygiene

`gitleaks` is wired in three places — pick whichever matches your workflow:

1. **Pre-commit hook** (per-developer) — runs on every `git commit`, blocks the commit if a secret-shaped value is staged.

   ```bash
   # one-time, per clone
   make hooks
   # or directly:
   pre-commit install
   ```

   Config lives in `.pre-commit-config.yaml` at the repo root.

2. **Makefile target** (manual scan, ad-hoc) — scan the entire history when investigating a leak.

   ```bash
   make secrets-scan
   ```

3. **GitHub Actions** (`.github/workflows/gitleaks.yml`) — runs on every push and pull request. Defense-in-depth: catches anything that bypassed the pre-commit hook (`--no-verify`, fresh clone without `pre-commit install`).

The shared allowlist for known-benign patterns (the demo firma id, env example placeholders, lockfiles, doc files, CI workflow files) lives in `.gitleaks.toml` at the repo root. Update it when you intentionally introduce a new secret-shaped placeholder; never to silence a real finding.

If a secret does land in a commit:

1. **Don't `git rm` and commit again** — the secret is still in history.
2. Rotate the value immediately (see "Rotating a secret").
3. Then rewrite history (`git filter-repo`) and force-push **only if the leaked secret was never accessed** — once it's been read, the rotation is what matters; history rewrites are theatre.

---

## What never to do

- ❌ Put a secret behind a `NEXT_PUBLIC_*` name. It ships to the browser.
- ❌ `console.log` or `print` a secret, even temporarily. The log line will end up in Cloud Logging / Datadog with weeks of retention.
- ❌ Paste a secret in Slack / Notion / Linear / Jira. Use a 1Password share link with expiry.
- ❌ Reuse a secret across environments. Dev leak ≠ prod leak only when they're distinct values.
- ❌ Commit a `.env` file with real values. `.env*.local` is git-ignored; `.env` is not (it holds committable defaults like rate cards).
- ❌ Share dev OAuth client credentials between developers. Each dev has their own.
- ❌ Use `--set-env-vars` for a 🔒 value on Cloud Run. Always `--set-secrets`.
- ❌ Grant `roles/secretmanager.admin` at the project level.

---

## Auditing access

```bash
# Who has access to a specific secret?
gcloud secrets get-iam-policy stripe-api-key

# Who accessed it, and when?
gcloud logging read \
  'resource.type="secretmanager.googleapis.com/Secret" AND
   resource.labels.secret_id="stripe-api-key" AND
   protoPayload.methodName="google.cloud.secretmanager.v1.SecretManagerService.AccessSecretVersion"' \
  --limit=50 --format=json
```

Cloud Audit Logs retain access events for 400 days by default. Set up an alert if you want to be notified on unusual access patterns (a service account reading a secret it doesn't normally use, etc.).

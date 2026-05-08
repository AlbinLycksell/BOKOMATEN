# GCP setup — first-time bootstrap

One-time steps to bring up the production environment in `europe-west4`. Run by Founders + the lead engineer together; takes ~2 hours of pair work.

## 0. Prerequisites

- A GCP organization with billing attached.
- `gcloud` CLI signed in as a user with `Project Creator` and `Billing Account User` on the org.
- `terraform` ≥ 1.9.
- A registered domain you'll point at the Cloud Run services (default: `svarsa.se`, with `app.svarsa.se` + `bridge.svarsa.se` subdomains).

## 1. Create the project

```bash
ORG_ID=...
BILLING=...
gcloud projects create svarsa-prod \
  --organization "$ORG_ID" \
  --name "Svarsa AI Production"
gcloud beta billing projects link svarsa-prod --billing-account "$BILLING"
gcloud config set project svarsa-prod
```

## 2. Bootstrap Terraform state bucket (one-off)

The Terraform backend lives in GCS. Create the bucket before the first `terraform init`:

```bash
gcloud storage buckets create gs://svarsa-tfstate \
  --location=europe-west4 \
  --uniform-bucket-level-access \
  --enable-autoclass
```

Copy `terraform/backend.tfvars.example` → `terraform/backend.tfvars`:

```
bucket = "svarsa-tfstate"
prefix = "envs/prod"
```

## 3. Provision base infrastructure

```bash
cd terraform/envs/prod
cp prod.tfvars.example prod.tfvars   # set project_id, github_repo, domains
terraform init -backend-config=../../backend.tfvars
terraform plan -var-file=prod.tfvars \
  -var="postgres_app_password=$(openssl rand -base64 32)"
# Review carefully — this enables APIs, creates network, SQL, KMS keyring,
# Workload Identity pool, two Cloud Run services (no images yet).
terraform apply -var-file=prod.tfvars \
  -var="postgres_app_password=$(openssl rand -base64 32)"
```

Save the password to 1Password as `Svarsa / Postgres app role` and put a copy into Secret Manager via:

```bash
echo -n "$PASSWORD" | gcloud secrets versions add postgres-app-password --data-file=-
```

## 4. Set the platform secrets

Secret Manager entries created empty by Terraform — populate them:

| Secret | Source |
|---|---|
| `database-url` | `postgresql+psycopg://svarsa_app:<password>@<private-ip>:5432/svarsa?sslmode=require` |
| `bridge-internal-token` | `openssl rand -hex 32` |
| `elks-api-username` | 46elks dashboard → Account → API |
| `elks-api-password` | 46elks dashboard → Account → API |
| `sentry-dsn` | `https://...@o<id>.ingest.de.sentry.io/<project>` |
| `nextauth-secret` | `openssl rand -base64 32` |
| `google-client-id` | GCP console → Credentials → OAuth client |
| `google-client-secret` | same |
| `gemini-api-key` | only for non-prod fallback path |

```bash
echo -n "<value>" | gcloud secrets versions add <secret-name> --data-file=-
```

## 5. Run database migrations

The Application Backend container runs `alembic upgrade head` on boot, so the first deploy migrates automatically. You can run it manually first to verify:

```bash
gcloud sql connect svarsa-pg --user=svarsa_app --database=svarsa
# password from Secret Manager
\q

cd backend
SVARSA_DATABASE_URL=postgresql+psycopg://svarsa_app:<pw>@127.0.0.1:5432/svarsa \
  uv run alembic upgrade head
```

(Use Cloud SQL Auth Proxy locally during this manual step.)

## 6. Build and push the first images

```bash
gcloud auth configure-docker europe-west4-docker.pkg.dev

cd backend
SHA=$(git rev-parse --short=12 HEAD)
docker build -f Dockerfile.app    -t europe-west4-docker.pkg.dev/svarsa-prod/svarsa/app:$SHA .
docker build -f Dockerfile.bridge -t europe-west4-docker.pkg.dev/svarsa-prod/svarsa/bridge:$SHA .
docker push europe-west4-docker.pkg.dev/svarsa-prod/svarsa/app:$SHA
docker push europe-west4-docker.pkg.dev/svarsa-prod/svarsa/bridge:$SHA

cd ../web
docker build -t europe-west4-docker.pkg.dev/svarsa-prod/svarsa/web:$SHA .
docker push europe-west4-docker.pkg.dev/svarsa-prod/svarsa/web:$SHA
```

## 7. Deploy the images

```bash
gcloud run deploy svarsa-app    --image europe-west4-docker.pkg.dev/svarsa-prod/svarsa/app:$SHA    --region europe-west4
gcloud run deploy svarsa-bridge --image europe-west4-docker.pkg.dev/svarsa-prod/svarsa/bridge:$SHA --region europe-west4
gcloud run deploy svarsa-web    --image europe-west4-docker.pkg.dev/svarsa-prod/svarsa/web:$SHA    --region europe-west4
```

## 8. DNS

Point your registrar at Cloud Run's domain mapping:

```bash
gcloud run domain-mappings list --region europe-west4
```

Cloud Run will provide CNAME / A records — paste them into your DNS.

## 9. GitHub Actions

Add the following repo secrets (Settings → Secrets and variables → Actions):

| Name | Value |
|---|---|
| `GCP_PROJECT` | `svarsa-prod` |
| `GCP_WIF_PROVIDER` | `projects/<num>/locations/global/workloadIdentityPools/github/providers/github-provider` |
| `GCP_DEPLOY_SA` | `svarsa-app@svarsa-prod.iam.gserviceaccount.com` |
| `NEXTAUTH_SECRET`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | for `deploy-web.yml` if not using Secret Manager mounts |

Push to `main` → `deploy-app` and `deploy-web` run automatically. `deploy-bridge` is workflow-dispatch-only (canary).

## 10. Verify

```bash
curl -i https://app.svarsa.se/health
curl -i https://bridge.svarsa.se/health
open https://app.svarsa.se/login   # web
```

Logs:

```bash
gcloud logging read 'resource.type="cloud_run_revision"' --limit 50 --project svarsa-prod
```

## 11. Cost monitoring

Set up budget alerts:

```bash
gcloud billing budgets create \
  --billing-account "$BILLING" \
  --display-name "Svarsa pre-pilot" \
  --budget-amount=500 \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=0.8 \
  --threshold-rule=percent=1.0
```

Pre-pilot target: 500 SEK/mo. Pilot: 1500 SEK/mo. Review monthly.

## Troubleshooting

- **Cloud SQL connection refused from Cloud Run:** verify the VPC connector is in the same network as the SQL instance, and that the service account has `roles/cloudsql.client`.
- **GCS bucket creation fails with "kms key not found":** the per-tenant key is created lazily by the application during firma onboarding. Run a smoke onboarding to materialize it before testing recordings.
- **Bridge cold-start dropping calls:** verify `min_instances ≥ 2` on the Cloud Run service; min instances are non-negotiable for the bridge per PRD §8.10.

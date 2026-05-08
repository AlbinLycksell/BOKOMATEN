# Terraform — Svarsa GCP infrastructure

Cost-efficient single-region (`europe-west4`) deploy. Two Cloud Run services
(Application Backend + Realtime Bridge), one Cloud SQL Postgres, GCS for
recordings, KMS for per-tenant CMEK, Secret Manager, Cloud Tasks, Workload
Identity Federation for GitHub Actions, optional Memorystore Redis.

## Layout

```
terraform/
├── envs/
│   ├── prod/        production env (europe-west4)
│   └── staging/     identical shape, smaller tier (mirror to verify changes)
├── modules/
│   ├── project/             enable APIs, create artifact registry
│   ├── network/             VPC, connector, firewall rules
│   ├── postgres/            Cloud SQL + databases + roles
│   ├── storage/              KMS keyring + base GCS settings
│   ├── secrets/             Secret Manager entries
│   ├── cloud_run/           one module instance per service
│   ├── workload_identity/   federation pool + provider for GitHub
│   └── observability/       Sentry mirror to error reporting (optional)
└── README.md
```

## First-time bootstrap

```bash
cd terraform/envs/prod
terraform init -backend-config=../../backend.tfvars   # GCS-backed remote state
terraform plan -var-file=prod.tfvars
terraform apply -var-file=prod.tfvars
```

Plan-then-apply discipline. Never run `apply` without a peer review of the
plan. `prod.tfvars` lives in 1Password (it contains the org id, billing
account id, and domain names — no secrets).

## Cost estimate (pre-pilot)

| Item | Tier | Monthly |
|---|---|---|
| Cloud Run — Application Backend | min=0, autoscale | ~$10 |
| Cloud Run — Realtime Bridge | min=2, autoscale | ~$30 |
| Cloud SQL Postgres | `db-custom-1-3840` | ~$30 |
| Cloud Storage (recordings) | Standard | ~$1/firma/mo (typical) |
| Cloud KMS | per-tenant key | ~$0.06/firma/mo |
| Secret Manager | platform secrets | <$1 |
| Memorystore Redis | skip until needed | $0 |
| **Total** | (5 firmor pilot) | ~$80–100/mo |

Once we cross 50 firmor or 50k calls/mo we re-tune (Postgres up to
`db-custom-2-8`, optional Redis, dedicated CDN domain).

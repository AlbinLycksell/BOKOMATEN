# Deployment runbook

## Steady state

| Service | Cadence | Trigger | Strategy | Rollback |
|---|---|---|---|---|
| `switchboard-app` (Application Backend) | hourly during business hours | merge to `main`, paths `backend/**` | rolling, immediate 100% | `gcloud run services update-traffic --to-revisions <prev>=100` |
| `switchboard-bridge` (Realtime Bridge) | weekly Sunday 04:00 CET | `gh workflow run deploy-bridge.yml` | canary 5% → 25% → 100% over 30 min | revert traffic split |
| `switchboard-web` (Next.js dashboard) | hourly with backend | merge to `main`, paths `web/**` | rolling, 100% | redeploy previous image |

Rationale per PRD §8.10. Active calls are 1–10 minutes long; the Bridge is the only service that can drop them, so its deploys are isolated.

## Hot rollback

Cloud Run keeps revisions for 30 days. Revert traffic to the last known-good in <30 s:

```bash
gcloud run revisions list --service switchboard-bridge --region europe-west4
gcloud run services update-traffic switchboard-bridge \
  --to-revisions "switchboard-bridge-<revision-id>=100" \
  --region europe-west4
```

## Database migrations

Forward-only, two-phase per PRD §8.10:

1. Code that tolerates BOTH the old and new schema lands on `main`. Backend deploy picks it up.
2. Migration runs (`alembic upgrade head`) — usually as part of the next backend deploy's container start. For breaking changes, run manually first via Cloud SQL Auth Proxy.
3. Code that uses ONLY the new schema lands on `main`. Backend deploy picks it up.

Never combine the two phases. Never write down-migrations beyond MVP — fix forward.

## Secrets rotation

| Secret | Rotation cadence | How |
|---|---|---|
| `bridge-internal-token` | quarterly | `openssl rand -hex 32` → new Secret Manager version → redeploy both services |
| `nextauth-secret` | quarterly | rotate, signs out all users (acceptable) |
| `database-url` (password) | annually | rotate switchboard_app password, update Secret Manager, redeploy |
| `elks-api-password` | only on staff change | 46elks dashboard → regenerate |
| `google-client-secret` | only on compromise | GCP Credentials → rotate |

## Per-call observability

Every call binds these contextvars at bridge entry: `firma_id`, `call_id`, `gemini_session_id`. Cloud Logging filter `jsonPayload.call_id="..."` returns the full per-call trace.

Aggregated dashboards (Cloud Monitoring custom metrics, populated by structlog → Cloud Logging metric extractors):

- `bridge.audio.latency_ms.p50/p95/p99`
- `tools.<name>.latency_ms.p50/p95`
- `bridge.calls_active`
- `gemini.session.disconnects_per_min`

SLO targets:

- Audio latency p50 < 1 200 ms (PRD §15)
- Audio latency p95 < 2 000 ms
- Tool dispatch p95 < 200 ms (PRD §8.4)
- Per-call cost median < 2.50 SEK (PRD §3.1)

## Cost guardrails

- GCP budget alert at 50%/80%/100% of monthly target.
- Cloud Run scale-to-zero on Application Backend (min=0); Bridge fixed min=2.
- GCS lifecycle rule: delete recordings after 7 days (per-firma configurable up to 365).
- Cloud SQL `db-custom-1-3840` for pre-pilot (~$30/mo); upgrade to `db-custom-2-8` at >50 firmor.

## Failure isolation

A Bridge pod crash kills its 10–50 in-flight calls — caller hears busy tone, expected to redial. We do not migrate active call state (PRD §8.10). Application Backend pod crashes are invisible: Bridge transparently retries the failing tool call.

## Tenant erasure (GDPR Art. 17)

Single transactional operation triggered from the admin tooling:

```sql
DELETE FROM <child tables in topo order> WHERE firma_id = :id;
DELETE FROM firma WHERE id = :id;
```

Then per-tenant GCS bucket and KMS key:

```bash
gsutil rm -r gs://switchboard-rec-<firma-lower>-europe-west4
gcloud kms keys versions destroy --location europe-west4 --keyring switchboard --key firma-<id> --version <v>
```

Audit log row written. 30-day SLA.

## Useful commands

```bash
# tail bridge logs
gcloud beta logging tail 'resource.type="cloud_run_revision" AND resource.labels.service_name="switchboard-bridge"' --project switchboard-prod

# call replay (per-call trace, last 1h)
gcloud logging read 'jsonPayload.call_id="01J..." AND timestamp>="2026-05-09T08:00:00Z"' --order=asc --project switchboard-prod

# database shell via auth proxy
gcloud sql connect switchboard-pg --user=switchboard_app --database=switchboard --quiet

# gcs object listing for a firma (signed URLs preferred — see Recording.signed_url)
gsutil ls gs://switchboard-rec-<firma-lower>-europe-west4/calls/
```

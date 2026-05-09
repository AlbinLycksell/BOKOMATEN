# Multi-tenancy

PRD §8.9. Shared platform, logical isolation, defence in depth across five layers.

## Tenant context — bound at request entry

Every authenticated request resolves to one `firma_id`. We bind it as a `contextvars.ContextVar` in `core/tenant.py`. The FastAPI middleware in `core/middleware.py` runs before every route and calls `firma_context(firma_id)` for the duration of the request. Two consequences:

1. **structlog auto-merges** the firma id into every log line via `merge_contextvars`.
2. **Background tasks inherit** the scope across `asyncio.create_task` boundaries — the tenant follows the work.

Code that needs the current scope:

```python
from switchboard.core.tenant import get_firma_id, require_firma_id

# Optional read
fid = get_firma_id()

# Refuses to run unscoped — raises RuntimeError
fid = require_firma_id()
```

Use `require_firma_id()` in services that handle tenant data. It's a runtime tripwire: any background path that forgets to bind the scope crashes loudly instead of silently leaking.

## Postgres row-level security (planned, deploys with Postgres)

When the dev SQLite is swapped for Cloud SQL Postgres:

```sql
-- Per tenant-scoped table
ALTER TABLE call ENABLE ROW LEVEL SECURITY;
CREATE POLICY firma_isolation ON call
  USING (firma_id = current_setting('app.firma_id')::text);
```

The application connects with a low-privilege role that **cannot** bypass RLS. A FastAPI `lifespan` hook will issue `SET app.firma_id = '<id>'` per connection checkout — driver hook lives in `db/session.py` (skeleton present; populates when Postgres lands).

## Repository discipline

We use SQLModel directly rather than a separate repository abstraction. The discipline:

- Every query that touches a tenant-scoped table includes `.where(<table>.firma_id == ...)`.
- Foreign-key cascades from `Firma` make tenant erasure a single transactional `DELETE WHERE firma_id = ?`.
- `tools/handlers.py` builds `ToolContext(firma_id=...)` once per call and passes it down — services accept `firma_id` explicitly rather than reading it from elsewhere.

A future linting rule (planned, not yet wired) will reject any SQL that hits a tenant-scoped table without a `firma_id` predicate.

## Cache keys (when Redis lands)

Convention: `firma:{firma_id}:<purpose>:<key>`. Anything tenant-agnostic goes under `platform:` and is reviewed in code review. There is no Redis dependency in the foundation commit.

## Per-tenant GCS buckets for recordings

The one shared-everything exception. Recordings carry the most sensitive data (caller voices, addresses, occasional accidental personnummer). Production layout:

- One GCS bucket per firma: `gs://switchboard-recordings-{firma_id}-{region}`
- Per-tenant CMEK key in Cloud KMS
- 7-day default TTL via Lifecycle rule, configurable per firma

The Recording Service (deferred) writes via the firma's bucket only. A leak in the recording path therefore exposes one firma, not all.

## External API credentials

Every Fortnox / Hantverksdata / Visma / Google integration uses the firma's own OAuth tokens, encrypted with a per-tenant DEK in Postgres (Secret Manager wraps the KEK). No platform-level credentials masquerading as tenants.

## Audit log

Every action that affects tenant data writes a row to `audit_log` (`models/audit.py`). Required fields: `firma_id`, `actor`, `action`, `target_type`, `target_id`, `created_at`. Use `services.audit_service.record(...)` — it refuses to write without a tenant context.

The dashboard exposes a per-firma audit trail (Phase 1 follow-up).

## Tenant erasure (GDPR Art. 17, 30 days)

Single transactional operation:

1. `DELETE FROM <table> WHERE firma_id = :id` in topological order (children first).
2. Per-tenant GCS bucket delete (recordings).
3. Per-tenant Cloud KMS key destroy (so backups are provably unreadable).
4. Audit log row marking the erasure.

Foreign-key cascades from `Firma` mean step 1 is one statement once we put `ON DELETE CASCADE` on the FKs. Currently the foundation uses non-cascading FKs to avoid accidental deletion in dev — switch to cascade in the migration that lands the erasure tooling.

## Where this is enforced in the foundation today

| Layer | Today | Production gap |
|---|---|---|
| Tenant context bound on every request | ✅ middleware + contextvar | OAuth replaces `X-Firma-Id` header |
| structlog auto-tags `firma_id` | ✅ via `merge_contextvars` | — |
| Every model carries `firma_id` | ✅ (incl. `tool_invocation` redundantly + `audit_log`) | — |
| Tenant-scoped queries | ✅ (manual discipline) | Lint rule + repository enforcement |
| Postgres RLS | Deploy-time (skeleton in `db/session.py`) | Wire on Postgres switch |
| Per-tenant GCS buckets | — (no recording pipeline) | Lands with recording service |
| Audit log writes | ✅ table + service | Wire from every mutation site |
| External API tokens per-tenant | ✅ `Integration.sync_state` placeholder | Real OAuth + DEK encrypt |

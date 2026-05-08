# Data model

Mirror of PRD §8.6, materialized in SQLModel under `backend/src/svarsa/models/`.

## ER overview

```
Firma ─┬─ PhoneNumber
       ├─ User
       ├─ EscalationChain
       ├─ Integration
       ├─ Customer ─┬─ Note
       │            ├─ Photo
       │            └─ Job ──── Call (1:N reverse)
       └─ Call ─┬─ TranscriptSegment
                ├─ ToolInvocation
                └─ Escalation
```

All foreign keys are `firma_id`-scoped at minimum so a multi-tenant query can never cross firmas without an explicit join through Firma.

## Tables

### `firma`

| Column | Type | Notes |
|---|---|---|
| `id` | `str` (ULID, pk) | Lexicographically sortable. |
| `name` | `str` | Indexed. |
| `org_number` | `str?` | Indexed. Format `XXXXXX-XXXX`. |
| `trade` | `Trade` enum | `vvs` default. |
| `plan` | `Plan` enum | `starter` default. |
| `locality` | `str?` | E.g. "Bromma". |
| `settings` | `JSON` | Serialized `FirmaSettings` Pydantic model. |
| `created_at`, `updated_at` | `datetime` | UTC. |

### `phone_number`

E.164 numbers owned by a firma. `provider` is the telephony partner (default `46elks`). One number per row; firma can own multiple.

### `user`

A person tied to a firma. `role` is one of `owner | back_office | technician`. `on_call` flips during jourrullning.

### `escalation_chain`

JSON `steps` array of `{target_user_id?, target_external_phone?, wait_minutes, method}`. `intent` scopes the chain (`akut`, `bokning`, …). `schedule_cron` lets the chain swap by time-of-day.

### `customer`

| Column | Type | Notes |
|---|---|---|
| `id` | ULID pk |
| `firma_id` | fk |
| `type` | `private | company` |
| `name` | `str` indexed |
| `phone` | `str` indexed (E.164) |
| `email` | `str?` |
| `org_number` | `str?` indexed (companies) |
| `address` | `JSON?` (`Address`) |
| `source` | `str` — `ai_call`, `import`, `manual` |
| `notes_summary` | `str?` |

### `call`

The hot table.

| Column | Type | Notes |
|---|---|---|
| `id` | ULID pk |
| `firma_id` | fk |
| `customer_id` | fk nullable (filled when CLI matches) |
| `caller_phone` | `str?` indexed |
| `started_at`, `ended_at` | `datetime` indexed |
| `intent` | `Intent?` indexed |
| `severity` | `Severity?` indexed |
| `status` | `CallStatus` indexed |
| `summary` | `JSON?` (`CallSummary`) |
| `recording_url`, `transcript_url` | `str?` |
| `gemini_session_id` | `str?` |
| `billing_seconds` | `int` |

### `transcript_segment`

Per-utterance row. `role` is `caller | ai | system`. `ts_ms_offset` is milliseconds from `Call.started_at`, used by the dashboard to scrub audio. Indexed by `call_id`.

### `tool_invocation`

Every function call the AI made during a session, in invocation order. Persisted via `ToolContext.session.add(...)` inside `tools.handlers.dispatch()`. Includes `latency_ms` for SLO monitoring.

`firma_id` is carried **redundantly** alongside `call_id → firma_id` (PRD §4 update). The redundancy is intentional: it makes per-tenant leak-detection queries trivial and tenant erasure a single statement on each table.

### `audit_log`

Append-only audit trail for all actions that affect tenant data (PRD §8.9).

| Column | Type | Notes |
|---|---|---|
| `id` | ULID pk |
| `firma_id` | fk indexed |
| `actor` | `str` indexed | User id, `"ai"`, `"system"`, or external service name. |
| `action` | `str` indexed | Verb-noun pair: `tool.invoked`, `call.created`, `settings.updated`. |
| `target_type` | `str?` | Optional referenced entity type. |
| `target_id` | `str?` indexed | Optional id. |
| `payload` | `JSON` | Action-specific context. |
| `created_at` | `datetime` indexed |

Written via `services.audit_service.record(...)` which refuses to write without a tenant context bound (`require_firma_id()`). Logically partitioned by `firma_id` so per-firma exports are a single index seek.

### `job`

A scheduled or completed unit of work tied to a customer (and usually a call). `intent` is preserved so reporting can split `akut` actuals from `bokning` actuals.

### `escalation`

Created by `escalation_service.escalate()`. `contacted_user_ids` is the list of users whose phones the system tried to reach. `next_in_chain_minutes` is the wait before the chain advances.

## JSON-blob fields

Used deliberately for nested settings that don't need indexing or relational joins:

- `Firma.settings` — `FirmaSettings` (greeting, voice, hours, retention).
- `EscalationChain.steps` — list of `EscalationStep`.
- `Customer.address` — `Address`.
- `Call.summary` — `CallSummary`.
- `Integration.sync_state` — opaque to the schema; per-integration shape.

These are validated into Pydantic models at the read boundary, so callers never see raw dict access in business code.

## Indexing strategy

- `Call(firma_id, started_at desc)` for the inbox query.
- `Call(intent)`, `Call(severity)`, `Call(status)` for filter pivots.
- `Customer(firma_id, phone)` for CLI-based lookup (the most-called code path).
- `Customer(firma_id, org_number)` for B2B match.
- `TranscriptSegment(call_id, ts_ms_offset)` for ordered fetch.
- `ToolInvocation(call_id, invoked_at)` likewise.

## Multi-tenancy

Every tenant-scoped table carries a non-nullable `firma_id` foreign key to `firma`. See [`multi-tenancy.md`](./multi-tenancy.md) for the layered isolation policy (request context, structlog binding, Postgres RLS, repository discipline, cache prefixes, per-tenant GCS, audit log, tenant erasure).

## Migrations

MVP uses `SQLModel.metadata.create_all()` against SQLite for fast iteration. Production switch to Alembic happens before the first prod write — model changes today are not migration-tracked.

Migration discipline is forward-only and two-phase (PRD §8.10): deploy code tolerating both schemas → migrate → deploy code using new schema only. Backfills run as Cloud Run Jobs in a separate window from regular deploys.

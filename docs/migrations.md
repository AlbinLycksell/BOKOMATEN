# Migrations

We use Alembic. SQLite drives local dev; Postgres drives prod. Both run the same revisions.

## Layout

```
backend/
├── alembic.ini
└── alembic/
    ├── env.py
    ├── script.py.mako
    └── versions/
        ├── 0001_initial_schema.py
        └── 0002_postgres_rls.py
```

## Daily commands

```bash
cd backend

# apply all pending
uv run alembic upgrade head

# autogenerate a revision against the live model state
uv run alembic revision --autogenerate -m "add foo"

# show current revision
uv run alembic current

# show history
uv run alembic history --verbose

# downgrade by one (dev only — do not in prod)
uv run alembic downgrade -1
```

## Production discipline

Forward-only, two-phase (PRD §8.10):

1. Land code that **tolerates both** old and new schema → deploy.
2. Run the migration.
3. Land code that **requires** new schema → deploy.

The Application Backend container runs `alembic upgrade head` on boot, so step 2 happens automatically as long as a migration is in `alembic/versions/`. For destructive changes, run the migration manually via Cloud SQL Auth Proxy first.

## Postgres-only DDL

Some migrations (RLS in `0002`) only make sense on Postgres. Guard with:

```python
if op.get_bind().dialect.name != "postgresql":
    return
```

so SQLite dev still moves forward.

## Test discipline

The `ci.yml` workflow runs `alembic upgrade head` against an ephemeral Postgres service container after every push, ensuring migrations stay clean before they ever touch Cloud SQL.

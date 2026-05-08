"""postgres row-level security on tenant-scoped tables (PRD §8.9)

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-09

Postgres-only. On SQLite this is a no-op so dev tests still pass.
The application connects with role `svarsa_app` which has no BYPASSRLS.
Every connection is opened with `SET app.firma_id = '<id>'` by the
SQLAlchemy `checkout` listener in `db/session.py`.
"""

from __future__ import annotations

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

TENANT_TABLES = (
    "phone_number",
    "user",
    "escalation_chain",
    "integration",
    "customer",
    "call",
    "tool_invocation",
    "job",
    "escalation",
    "audit_log",
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'svarsa_app') THEN
            CREATE ROLE svarsa_app NOLOGIN;
          END IF;
        END$$;
        """
    )

    for tbl in TENANT_TABLES:
        op.execute(f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {tbl} FORCE ROW LEVEL SECURITY")
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {tbl} TO svarsa_app")
        op.execute(
            f"""
            CREATE POLICY firma_isolation ON {tbl}
              USING (firma_id = current_setting('app.firma_id', true))
              WITH CHECK (firma_id = current_setting('app.firma_id', true))
            """
        )

    # firma is referenced by every other table; readable by app role for joins
    # but writable only via explicit superuser tooling (onboarding flow).
    op.execute("GRANT SELECT ON firma TO svarsa_app")
    op.execute("GRANT USAGE ON SCHEMA public TO svarsa_app")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for tbl in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS firma_isolation ON {tbl}")
        op.execute(f"ALTER TABLE {tbl} DISABLE ROW LEVEL SECURITY")
        op.execute(f"REVOKE ALL ON {tbl} FROM svarsa_app")
    op.execute("REVOKE ALL ON firma FROM svarsa_app")

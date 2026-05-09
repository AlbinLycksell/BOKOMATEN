"""user.google_sub + last_login_at + email index

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-09
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user", sa.Column("google_sub", sa.String(), nullable=True))
    op.add_column("user", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_user_google_sub", "user", ["google_sub"], unique=True)
    op.create_index("ix_user_email", "user", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_user_email", table_name="user")
    op.drop_index("ix_user_google_sub", table_name="user")
    op.drop_column("user", "last_login_at")
    op.drop_column("user", "google_sub")

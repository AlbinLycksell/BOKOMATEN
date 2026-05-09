"""multi-firma membership + white-label columns

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-09
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_firma_membership",
        sa.Column("user_id", sa.String(), sa.ForeignKey("user.id"), primary_key=True),
        sa.Column(
            "firma_id",
            sa.String(),
            sa.ForeignKey("firma.id"),
            primary_key=True,
            index=True,
        ),
        sa.Column("role", sa.String(), nullable=False, server_default="owner"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_firma_membership")

"""call cost columns

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-09
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("call", sa.Column("cost_breakdown", sa.JSON, nullable=True))
    op.add_column(
        "call",
        sa.Column(
            "cost_total_sek",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    op.drop_column("call", "cost_total_sek")
    op.drop_column("call", "cost_breakdown")

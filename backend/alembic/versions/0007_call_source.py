"""call source column

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "call",
        sa.Column(
            "source",
            sa.String(),
            nullable=False,
            server_default="telephony",
        ),
    )
    op.create_index("ix_call_source", "call", ["source"])


def downgrade() -> None:
    op.drop_index("ix_call_source", table_name="call")
    op.drop_column("call", "source")

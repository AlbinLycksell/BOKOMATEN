"""firma stripe + plan enforcement columns

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-09
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("firma", sa.Column("stripe_customer_id", sa.String(), nullable=True))
    op.add_column("firma", sa.Column("stripe_subscription_id", sa.String(), nullable=True))
    op.add_column(
        "firma",
        sa.Column(
            "subscription_status",
            sa.String(),
            nullable=False,
            server_default="trialing",
        ),
    )
    op.add_column(
        "firma",
        sa.Column(
            "plan_calls_used_period",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "firma",
        sa.Column("plan_period_end", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_firma_stripe_customer", "firma", ["stripe_customer_id"])
    op.create_index("ix_firma_stripe_subscription", "firma", ["stripe_subscription_id"])


def downgrade() -> None:
    op.drop_index("ix_firma_stripe_subscription", table_name="firma")
    op.drop_index("ix_firma_stripe_customer", table_name="firma")
    op.drop_column("firma", "plan_period_end")
    op.drop_column("firma", "plan_calls_used_period")
    op.drop_column("firma", "subscription_status")
    op.drop_column("firma", "stripe_subscription_id")
    op.drop_column("firma", "stripe_customer_id")

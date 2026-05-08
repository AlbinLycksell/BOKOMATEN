"""initial schema (foundation tables)

Revision ID: 0001
Revises:
Create Date: 2026-05-09

Captures every table defined under `svarsa.models.*` as of the foundation
commit. Forward-only per PRD §8.10 — downgrade drops everything (only
useful in dev).
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
import sqlmodel  # noqa: F401  used in autogen output

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def _json_col(name: str, *, nullable: bool = True, default=None) -> sa.Column:
    kwargs = {"nullable": nullable}
    if default is not None:
        kwargs["server_default"] = sa.text(default)
    return sa.Column(name, sa.JSON, **kwargs)


def upgrade() -> None:
    op.create_table(
        "firma",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, index=True),
        sa.Column("org_number", sa.String(), nullable=True, index=True),
        sa.Column("trade", sa.String(), nullable=False),
        sa.Column("plan", sa.String(), nullable=False),
        sa.Column("locality", sa.String(), nullable=True),
        _json_col("settings", nullable=False, default="'{}'"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "phone_number",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("firma_id", sa.String(), sa.ForeignKey("firma.id"), nullable=False, index=True),
        sa.Column("e164", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "user",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("firma_id", sa.String(), sa.ForeignKey("firma.id"), nullable=False, index=True),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("on_call", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "escalation_chain",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("firma_id", sa.String(), sa.ForeignKey("firma.id"), nullable=False, index=True),
        sa.Column("intent", sa.String(), nullable=False),
        sa.Column("schedule_cron", sa.String(), nullable=True),
        _json_col("steps", nullable=False, default="'[]'"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "integration",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("firma_id", sa.String(), sa.ForeignKey("firma.id"), nullable=False, index=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("connected", sa.Boolean(), nullable=False),
        _json_col("sync_state", nullable=False, default="'{}'"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "customer",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("firma_id", sa.String(), sa.ForeignKey("firma.id"), nullable=False, index=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False, index=True),
        sa.Column("phone", sa.String(), nullable=False, index=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("org_number", sa.String(), nullable=True, index=True),
        _json_col("address"),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("notes_summary", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "customer_note",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("customer_id", sa.String(), sa.ForeignKey("customer.id"), nullable=False, index=True),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "customer_photo",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("customer_id", sa.String(), sa.ForeignKey("customer.id"), nullable=False, index=True),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "call",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("firma_id", sa.String(), sa.ForeignKey("firma.id"), nullable=False, index=True),
        sa.Column("customer_id", sa.String(), sa.ForeignKey("customer.id"), nullable=True, index=True),
        sa.Column("caller_phone", sa.String(), nullable=True, index=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("intent", sa.String(), nullable=True, index=True),
        sa.Column("severity", sa.String(), nullable=True, index=True),
        sa.Column("status", sa.String(), nullable=False, index=True),
        sa.Column("recording_url", sa.String(), nullable=True),
        sa.Column("transcript_url", sa.String(), nullable=True),
        _json_col("summary"),
        sa.Column("gemini_session_id", sa.String(), nullable=True),
        sa.Column("billing_seconds", sa.Integer(), nullable=False),
    )

    op.create_table(
        "transcript_segment",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("call_id", sa.String(), sa.ForeignKey("call.id"), nullable=False, index=True),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("ts_ms_offset", sa.Integer(), nullable=False),
    )

    op.create_table(
        "tool_invocation",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("firma_id", sa.String(), sa.ForeignKey("firma.id"), nullable=False, index=True),
        sa.Column("call_id", sa.String(), sa.ForeignKey("call.id"), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False, index=True),
        _json_col("args", nullable=False, default="'{}'"),
        _json_col("result"),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("invoked_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "job",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("firma_id", sa.String(), sa.ForeignKey("firma.id"), nullable=False, index=True),
        sa.Column("customer_id", sa.String(), sa.ForeignKey("customer.id"), nullable=False, index=True),
        sa.Column("call_id", sa.String(), sa.ForeignKey("call.id"), nullable=True, index=True),
        sa.Column("intent", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("summary_sv", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("technician_id", sa.String(), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("estimated_value_sek", sa.Integer(), nullable=True),
        sa.Column("rot_eligible", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "escalation",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("firma_id", sa.String(), sa.ForeignKey("firma.id"), nullable=False, index=True),
        sa.Column("call_id", sa.String(), sa.ForeignKey("call.id"), nullable=False, index=True),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("reason_sv", sa.String(), nullable=False),
        _json_col("contacted_user_ids", nullable=False, default="'[]'"),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("next_in_chain_minutes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acked_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("firma_id", sa.String(), sa.ForeignKey("firma.id"), nullable=False, index=True),
        sa.Column("actor", sa.String(), nullable=False, index=True),
        sa.Column("action", sa.String(), nullable=False, index=True),
        sa.Column("target_type", sa.String(), nullable=True),
        sa.Column("target_id", sa.String(), nullable=True, index=True),
        _json_col("payload", nullable=False, default="'{}'"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, index=True),
    )


def downgrade() -> None:
    for tbl in (
        "audit_log",
        "escalation",
        "job",
        "tool_invocation",
        "transcript_segment",
        "call",
        "customer_photo",
        "customer_note",
        "customer",
        "integration",
        "escalation_chain",
        "user",
        "phone_number",
        "firma",
    ):
        op.drop_table(tbl)

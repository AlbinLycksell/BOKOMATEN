from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import JSON, Column
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel

from switchboard.core.ids import new_id
from switchboard.core.time import utcnow
from switchboard.models.enums import CallStatus, Intent, Severity, TranscriptRole


class CallSummary(BaseModel):
    short_sv: str
    long_sv: str
    next_action_sv: str
    owner_action_required: bool
    structured_fields: dict[str, Any] = {}


class Call(SQLModel, table=True):
    __tablename__ = "call"

    id: str = SQLField(default_factory=new_id, primary_key=True)
    firma_id: str = SQLField(foreign_key="firma.id", index=True)
    customer_id: str | None = SQLField(default=None, foreign_key="customer.id", index=True)
    caller_phone: str | None = SQLField(default=None, index=True)
    started_at: datetime = SQLField(default_factory=utcnow, index=True)
    ended_at: datetime | None = None
    intent: Intent | None = SQLField(default=None, index=True)
    severity: Severity | None = SQLField(default=None, index=True)
    status: CallStatus = SQLField(default=CallStatus.IN_PROGRESS, index=True)
    recording_url: str | None = None
    transcript_url: str | None = None
    summary: dict[str, Any] | None = SQLField(default=None, sa_column=Column(JSON))
    gemini_session_id: str | None = None
    billing_seconds: int = 0
    cost_breakdown: dict[str, Any] | None = SQLField(
        default=None, sa_column=Column(JSON)
    )
    cost_total_sek: float = 0.0


class TranscriptSegment(SQLModel, table=True):
    __tablename__ = "transcript_segment"

    id: str = SQLField(default_factory=new_id, primary_key=True)
    call_id: str = SQLField(foreign_key="call.id", index=True)
    role: TranscriptRole
    text: str
    ts_ms_offset: int = 0


class ToolInvocation(SQLModel, table=True):
    __tablename__ = "tool_invocation"

    id: str = SQLField(default_factory=new_id, primary_key=True)
    firma_id: str = SQLField(foreign_key="firma.id", index=True)
    call_id: str = SQLField(foreign_key="call.id", index=True)
    name: str = SQLField(index=True)
    args: dict[str, Any] = SQLField(default_factory=dict, sa_column=Column(JSON))
    result: dict[str, Any] | None = SQLField(default=None, sa_column=Column(JSON))
    latency_ms: int = 0
    error: str | None = None
    invoked_at: datetime = SQLField(default_factory=utcnow)


class CallRead(BaseModel):
    id: str
    customer_id: str | None
    customer_name: str | None
    caller_phone: str | None
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int
    intent: Intent | None
    severity: Severity | None
    status: CallStatus
    summary_short: str | None
    cost_total_sek: float = 0.0


class TranscriptSegmentRead(BaseModel):
    role: TranscriptRole
    text: str
    ts_ms_offset: int


class ToolInvocationRead(BaseModel):
    name: str
    args: dict[str, Any]
    result: dict[str, Any] | None
    latency_ms: int
    error: str | None
    invoked_at: datetime


class CallDetailRead(CallRead):
    summary: CallSummary | None
    transcript: list[TranscriptSegmentRead]
    tool_invocations: list[ToolInvocationRead]
    recording_url: str | None

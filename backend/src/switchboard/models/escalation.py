from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import JSON, Column
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel

from switchboard.core.ids import new_id
from switchboard.core.time import utcnow
from switchboard.models.enums import EscalationStatus, Severity


class Escalation(SQLModel, table=True):
    __tablename__ = "escalation"

    id: str = SQLField(default_factory=new_id, primary_key=True)
    firma_id: str = SQLField(foreign_key="firma.id", index=True)
    call_id: str = SQLField(foreign_key="call.id", index=True)
    severity: Severity
    reason_sv: str
    contacted_user_ids: list[str] = SQLField(default_factory=list, sa_column=Column(JSON))
    status: EscalationStatus = EscalationStatus.PENDING
    next_in_chain_minutes: int = 0
    created_at: datetime = SQLField(default_factory=utcnow)
    acked_at: datetime | None = None


class EscalationRead(BaseModel):
    id: str
    severity: Severity
    reason_sv: str
    contacted_user_ids: list[str]
    status: EscalationStatus
    created_at: datetime
    acked_at: datetime | None

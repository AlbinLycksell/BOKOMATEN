from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel

from switchboard.core.ids import new_id
from switchboard.core.time import utcnow
from switchboard.models.enums import Intent, JobStatus


class Job(SQLModel, table=True):
    __tablename__ = "job"

    id: str = SQLField(default_factory=new_id, primary_key=True)
    firma_id: str = SQLField(foreign_key="firma.id", index=True)
    customer_id: str = SQLField(foreign_key="customer.id", index=True)
    call_id: str | None = SQLField(default=None, foreign_key="call.id", index=True)
    intent: Intent = Intent.BOKNING
    status: JobStatus = JobStatus.PROPOSED
    summary_sv: str
    address: str
    technician_id: str | None = SQLField(default=None, foreign_key="user.id")
    scheduled_for: datetime | None = SQLField(default=None, index=True)
    duration_minutes: int = 60
    estimated_value_sek: int | None = None
    rot_eligible: bool = False
    created_at: datetime = SQLField(default_factory=utcnow)
    updated_at: datetime = SQLField(default_factory=utcnow)


class JobRead(BaseModel):
    id: str
    customer_id: str
    intent: Intent
    status: JobStatus
    summary_sv: str
    address: str
    scheduled_for: datetime | None
    duration_minutes: int
    estimated_value_sek: int | None
    rot_eligible: bool

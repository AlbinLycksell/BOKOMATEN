from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import JSON, Column
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel

from svarsa.core.ids import new_id
from svarsa.core.time import utcnow


class AuditLog(SQLModel, table=True):
    """Append-only audit trail for tenant-scoped actions (PRD §8.9).

    One row per action that affects tenant data. Partitioned (logically) by
    `firma_id` so per-firma exports are a single index seek.
    """

    __tablename__ = "audit_log"

    id: str = SQLField(default_factory=new_id, primary_key=True)
    firma_id: str = SQLField(foreign_key="firma.id", index=True)
    actor: str = SQLField(index=True)
    """Who acted: user id, "ai", "system", or external service name."""
    action: str = SQLField(index=True)
    """Verb-noun pair: tool.invoked, call.created, settings.updated, …"""
    target_type: str | None = None
    target_id: str | None = SQLField(default=None, index=True)
    payload: dict[str, Any] = SQLField(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = SQLField(default_factory=utcnow, index=True)


class AuditLogRead(BaseModel):
    id: str
    actor: str
    action: str
    target_type: str | None
    target_id: str | None
    payload: dict[str, Any]
    created_at: datetime

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Column
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel

from svarsa.core.ids import new_id
from svarsa.core.time import utcnow
from svarsa.models.enums import IntegrationType, Plan, Trade


class FirmaSettings(BaseModel):
    greeting_text: str = "Hej, du har kommit till {firma_namn}, jag är deras digitala assistent. Hur kan jag hjälpa dig?"
    voice: str = "Aoede"
    open_hours_weekday: tuple[str, str] = ("07:00", "17:00")
    open_hours_saturday: tuple[str, str] | None = None
    open_hours_sunday: tuple[str, str] | None = None
    answer_outside_hours: bool = True
    record_calls: bool = True
    recording_retention_days: int = 7
    transcript_retention_days: int = 90
    persona_overrides: str = ""


class Firma(SQLModel, table=True):
    __tablename__ = "firma"

    id: str = SQLField(default_factory=new_id, primary_key=True)
    name: str = SQLField(index=True)
    org_number: str | None = SQLField(default=None, index=True)
    trade: Trade = SQLField(default=Trade.VVS)
    plan: Plan = SQLField(default=Plan.STARTER)
    locality: str | None = None
    settings: dict[str, Any] = SQLField(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = SQLField(default_factory=utcnow)
    updated_at: datetime = SQLField(default_factory=utcnow)


class PhoneNumber(SQLModel, table=True):
    __tablename__ = "phone_number"

    id: str = SQLField(default_factory=new_id, primary_key=True)
    firma_id: str = SQLField(foreign_key="firma.id", index=True)
    e164: str = SQLField(index=True, unique=True)
    provider: str = "46elks"
    status: str = "active"
    created_at: datetime = SQLField(default_factory=utcnow)


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: str = SQLField(default_factory=new_id, primary_key=True)
    firma_id: str = SQLField(foreign_key="firma.id", index=True)
    role: str
    name: str
    phone: str | None = None
    email: str | None = None
    on_call: bool = False
    created_at: datetime = SQLField(default_factory=utcnow)


class EscalationStep(BaseModel):
    target_user_id: str | None = None
    target_external_phone: str | None = None
    wait_minutes: int = 5
    method: str = "sms+call"


class EscalationChain(SQLModel, table=True):
    __tablename__ = "escalation_chain"

    id: str = SQLField(default_factory=new_id, primary_key=True)
    firma_id: str = SQLField(foreign_key="firma.id", index=True)
    intent: str = SQLField(default="akut")
    schedule_cron: str | None = None
    steps: list[dict[str, Any]] = SQLField(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = SQLField(default_factory=utcnow)


class Integration(SQLModel, table=True):
    __tablename__ = "integration"

    id: str = SQLField(default_factory=new_id, primary_key=True)
    firma_id: str = SQLField(foreign_key="firma.id", index=True)
    type: IntegrationType
    connected: bool = False
    sync_state: dict[str, Any] = SQLField(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = SQLField(default_factory=utcnow)


class FirmaRead(BaseModel):
    id: str
    name: str
    org_number: str | None
    trade: Trade
    plan: Plan
    locality: str | None
    settings: FirmaSettings
    created_at: datetime


class FirmaSettingsUpdate(BaseModel):
    greeting_text: str | None = None
    voice: str | None = None
    open_hours_weekday: tuple[str, str] | None = None
    answer_outside_hours: bool | None = None
    record_calls: bool | None = None
    recording_retention_days: int | None = Field(default=None, ge=0, le=365)
    persona_overrides: str | None = None

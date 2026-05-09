from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

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

    # GDPR §9.2 — consent disclosure read at the start of every call.
    consent_disclosure_sv: str = (
        "Detta samtal kan spelas in för kvalitets- och utbildningsändamål. "
        "Vänligen säg till om du inte vill att samtalet spelas in."
    )
    consent_mode: Literal["disclosure_optout", "explicit_optin"] = "disclosure_optout"

    # SMS sender id management (per-firma alias falls back to platform `Svarsa`)
    sms_sender_id: str | None = None
    sms_sender_id_verified: bool = False

    # White-label (Premium tier — PRD §13).
    brand_color_accent: str | None = None
    brand_logo_url: str | None = None

    # Träna AI feedback loop — appended to system prompt per firma.
    persona_corrections: list[str] = Field(default_factory=list)


class Firma(SQLModel, table=True):
    __tablename__ = "firma"

    id: str = SQLField(default_factory=new_id, primary_key=True)
    name: str = SQLField(index=True)
    org_number: str | None = SQLField(default=None, index=True)
    trade: Trade = SQLField(default=Trade.VVS)
    plan: Plan = SQLField(default=Plan.STARTER)
    locality: str | None = None
    settings: dict[str, Any] = SQLField(default_factory=dict, sa_column=Column(JSON))
    stripe_customer_id: str | None = SQLField(default=None, index=True)
    stripe_subscription_id: str | None = SQLField(default=None, index=True)
    subscription_status: str = SQLField(default="trialing")
    plan_calls_used_period: int = 0
    plan_period_end: datetime | None = None
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
    email: str | None = SQLField(default=None, index=True, unique=True)
    on_call: bool = False
    google_sub: str | None = SQLField(default=None, index=True, unique=True)
    last_login_at: datetime | None = None
    created_at: datetime = SQLField(default_factory=utcnow)


class UserFirmaMembership(SQLModel, table=True):
    """Multi-firma support (PRD §13, Premium-tier feature).

    A User has one canonical `firma_id` (their default), but Premium owners
    can be members of additional firmor and switch via the topbar.
    """

    __tablename__ = "user_firma_membership"

    user_id: str = SQLField(foreign_key="user.id", primary_key=True)
    firma_id: str = SQLField(foreign_key="firma.id", primary_key=True, index=True)
    role: str = "owner"
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
    consent_disclosure_sv: str | None = None
    sms_sender_id: str | None = None
    brand_color_accent: str | None = None
    brand_logo_url: str | None = None

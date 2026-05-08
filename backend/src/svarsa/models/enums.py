from __future__ import annotations

from enum import StrEnum


class Intent(StrEnum):
    AKUT = "akut"
    OFFERT = "offertforfragan"
    BOKNING = "bokning"
    BEFINTLIG_KUND = "befintlig_kund_fraga"
    OVRIGT = "ovrigt"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Trade(StrEnum):
    VVS = "vvs"
    EL = "el"
    SNICKERI = "snickeri"
    TAK = "tak"
    KAKEL = "kakel"
    OVRIGT = "ovrigt"


class Plan(StrEnum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    PREMIUM = "premium"


class CustomerType(StrEnum):
    PRIVATE = "private"
    COMPANY = "company"


class CallStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    HANDLED = "handled"
    NEEDS_FOLLOWUP = "needs_followup"


class JobStatus(StrEnum):
    PROPOSED = "proposed"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class IntegrationType(StrEnum):
    FORTNOX = "fortnox"
    HANTVERKSDATA = "hantverksdata"
    VISMA = "visma"
    GOOGLE_CALENDAR = "google_calendar"
    OUTLOOK = "outlook"


class EscalationStatus(StrEnum):
    PENDING = "pending"
    CONTACTED = "contacted"
    ACKED = "acked"
    EXPIRED = "expired"


class TranscriptRole(StrEnum):
    CALLER = "caller"
    AI = "ai"
    SYSTEM = "system"


class EmergencyIndicator(StrEnum):
    LACKA = "lacka"
    RINNER = "rinner"
    STROMLOST = "stromlost"
    INGEN_VARME = "ingen_varme"
    GAS_LUKT = "gas_lukt"
    BRAND = "brand"
    AVLOPP_STOPP = "avlopp_stopp"
    ISOLERAD_ALDRE = "isolerad_aldre"

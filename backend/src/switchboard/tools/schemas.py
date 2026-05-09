"""Typed argument and result schemas for the 12 tools the AI calls.

Each tool has a `<Name>Args` and `<Name>Result` Pydantic model. These
double as: (a) Gemini Live tool declarations (via `to_gemini_tool()` in
`declarations.py`), and (b) the source of truth for handler dispatch.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from switchboard.models.enums import (
    CustomerType,
    EmergencyIndicator,
    Severity,
    SmsTemplate,
    ToolName,
    Trade,
    TransferTarget,
    TriageAction,
    Urgency,
)

_ESCALATION_SEVERITIES: frozenset[Severity] = frozenset(
    {Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM}
)


SwedishE164 = Annotated[str, Field(pattern=r"^\+46\d{6,10}$", description="E.164 svenska +46…")]
OrgNumber = Annotated[str, Field(pattern=r"^\d{6}-\d{4}$", description="Svenskt org-nummer")]


class LookupCustomerArgs(BaseModel):
    phone_number: SwedishE164 | None = None
    org_number: OrgNumber | None = None
    name_query: str | None = None


class LookupCustomerResult(BaseModel):
    found: bool
    customer_id: str | None = None
    name: str | None = None
    type: CustomerType | None = None
    last_job_summary: str | None = None
    open_jobs: list[str] = []
    notes: str | None = None


class TriageEmergencyArgs(BaseModel):
    problem_description: str
    trade: Trade
    indicators_present: list[EmergencyIndicator] = []


class TriageEmergencyResult(BaseModel):
    is_emergency: bool
    severity: Severity
    recommended_action: TriageAction
    reasoning_sv: str


class CheckAvailabilityArgs(BaseModel):
    duration_minutes: int = Field(ge=15, le=480)
    earliest_date: str = Field(description="ISO date YYYY-MM-DD")
    latest_date: str = Field(description="ISO date YYYY-MM-DD")
    required_skills: list[str] = []
    address: str | None = None


class AvailabilitySlot(BaseModel):
    start_iso: datetime
    end_iso: datetime
    technician_id: str
    technician_name: str
    travel_buffer_min: int


class CheckAvailabilityResult(BaseModel):
    slots: list[AvailabilitySlot]


class BookAppointmentArgs(BaseModel):
    customer_id: str
    start_iso: datetime
    duration_minutes: int = Field(ge=15, le=480)
    technician_id: str | None = None
    address: str
    problem_summary_sv: str
    rot_eligible: bool = False


class BookAppointmentResult(BaseModel):
    booking_id: str
    calendar_event_url: str | None = None
    confirmation_sms_sent: bool = False
    confirmation_email_sent: bool = False


class CreateLeadArgs(BaseModel):
    name: str
    phone: SwedishE164
    type: CustomerType = CustomerType.PRIVATE
    email: str | None = None
    address: str | None = None
    org_number: OrgNumber | None = None
    problem_summary_sv: str
    estimated_value_sek: int | None = None


class CreateLeadResult(BaseModel):
    customer_id: str
    created: bool


class EscalateToOwnerArgs(BaseModel):
    severity: Severity
    reason_sv: str
    customer_id: str | None = None
    customer_phone: SwedishE164
    address: str | None = None
    callback_window_sv: str = "15 min"

    @field_validator("severity")
    @classmethod
    def _disallow_low(cls, v: Severity) -> Severity:
        if v not in _ESCALATION_SEVERITIES:
            msg = f"escalation_severity_must_be:{[s.value for s in _ESCALATION_SEVERITIES]}"
            raise ValueError(msg)
        return v


class EscalateToOwnerResult(BaseModel):
    escalation_id: str
    contacted: list[str]
    next_in_chain_minutes: int


class SendSmsFollowupArgs(BaseModel):
    to_phone: SwedishE164
    template: SmsTemplate
    context_data: dict[str, str | int | bool] = {}


class SendSmsFollowupResult(BaseModel):
    sent: bool
    sms_id: str


class RequestPhotoUploadArgs(BaseModel):
    to_phone: SwedishE164
    lead_or_customer_id: str
    expires_hours: int = Field(default=168, ge=1, le=720)


class RequestPhotoUploadResult(BaseModel):
    upload_url: str
    sms_sent: bool


class LookupJobStatusArgs(BaseModel):
    customer_id: str
    job_query_sv: str | None = None


class LookupJobStatusResult(BaseModel):
    found: bool
    job_id: str | None = None
    status_sv: str | None = None
    summary_sv: str | None = None


class CheckRotEligibilityArgs(BaseModel):
    is_private_person: bool
    owns_property: bool
    property_age_years: int = Field(ge=0)
    work_type: str


class CheckRotEligibilityResult(BaseModel):
    eligible: bool
    max_deduction_sek_estimate: int
    caveats_sv: str


class TransferToHumanArgs(BaseModel):
    target: TransferTarget
    context_summary_sv: str


class TransferToHumanResult(BaseModel):
    transferred: bool
    target_phone: str | None = None


class TakeMessageArgs(BaseModel):
    caller_phone: SwedishE164
    topic_sv: str
    urgency: Urgency
    caller_name: str | None = None
    callback_preference_sv: str | None = None


class TakeMessageResult(BaseModel):
    message_id: str
    forwarded_to_user_id: str | None = None


class DisableRecordingArgs(BaseModel):
    reason_sv: str = "Kunden invände mot inspelning."


class DisableRecordingResult(BaseModel):
    disabled: bool


TOOL_NAMES: tuple[ToolName, ...] = tuple(ToolName)

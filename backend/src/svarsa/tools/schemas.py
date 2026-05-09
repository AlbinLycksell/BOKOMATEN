"""Typed argument and result schemas for the 12 tools the AI calls.

Each tool has a `<Name>Args` and `<Name>Result` Pydantic model. These
double as: (a) Gemini Live tool declarations (via `to_gemini_tool()` in
`declarations.py`), and (b) the source of truth for handler dispatch.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from svarsa.models.enums import EmergencyIndicator, Severity, Trade


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
    type: Literal["private", "company"] | None = None
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
    recommended_action: Literal["escalate_now", "book_today", "book_normal", "informational"]
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
    type: Literal["private", "company"] = "private"
    email: str | None = None
    address: str | None = None
    org_number: OrgNumber | None = None
    problem_summary_sv: str
    estimated_value_sek: int | None = None


class CreateLeadResult(BaseModel):
    customer_id: str
    created: bool


class EscalateToOwnerArgs(BaseModel):
    severity: Literal["critical", "high", "medium"]
    reason_sv: str
    customer_id: str | None = None
    customer_phone: SwedishE164
    address: str | None = None
    callback_window_sv: str = "15 min"


class EscalateToOwnerResult(BaseModel):
    escalation_id: str
    contacted: list[str]
    next_in_chain_minutes: int


SmsTemplate = Literal[
    "booking_confirmation",
    "emergency_ack",
    "photo_upload_link",
    "callback_promise",
    "secure_form_link",
]


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
    target: Literal["owner_mobile", "office", "on_call_technician", "external_answering_service"]
    context_summary_sv: str


class TransferToHumanResult(BaseModel):
    transferred: bool
    target_phone: str | None = None


class TakeMessageArgs(BaseModel):
    caller_phone: SwedishE164
    topic_sv: str
    urgency: Literal["low", "medium", "high"]
    caller_name: str | None = None
    callback_preference_sv: str | None = None


class TakeMessageResult(BaseModel):
    message_id: str
    forwarded_to_user_id: str | None = None


class DisableRecordingArgs(BaseModel):
    reason_sv: str = "Kunden invände mot inspelning."


class DisableRecordingResult(BaseModel):
    disabled: bool


TOOL_NAMES: tuple[str, ...] = (
    "lookup_customer",
    "triage_emergency",
    "check_availability",
    "book_appointment",
    "create_lead",
    "escalate_to_owner",
    "send_sms_followup",
    "request_photo_upload",
    "lookup_job_status",
    "check_rot_eligibility",
    "transfer_to_human",
    "take_message",
    "disable_recording_for_call",
)

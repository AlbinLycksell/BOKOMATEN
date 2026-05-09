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


class CallSource(StrEnum):
    TELEPHONY = "telephony"
    VOICE_TEST = "voice_test"
    SCENARIO = "scenario"


class EmergencyIndicator(StrEnum):
    LACKA = "lacka"
    RINNER = "rinner"
    STROMLOST = "stromlost"
    INGEN_VARME = "ingen_varme"
    GAS_LUKT = "gas_lukt"
    BRAND = "brand"
    AVLOPP_STOPP = "avlopp_stopp"
    ISOLERAD_ALDRE = "isolerad_aldre"


class UserRole(StrEnum):
    OWNER = "owner"
    BACK_OFFICE = "back_office"
    TECHNICIAN = "technician"


class PhoneNumberProvider(StrEnum):
    ELKS = "46elks"


class PhoneNumberStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class StripeSubscriptionStatus(StrEnum):
    ACTIVE = "active"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    UNPAID = "unpaid"


class StripeEventType(StrEnum):
    INVOICE_PAID = "invoice.paid"
    INVOICE_PAYMENT_FAILED = "invoice.payment_failed"
    CHECKOUT_COMPLETED = "checkout.session.completed"
    SUBSCRIPTION_PREFIX = "customer.subscription"


class ToolName(StrEnum):
    LOOKUP_CUSTOMER = "lookup_customer"
    TRIAGE_EMERGENCY = "triage_emergency"
    CHECK_AVAILABILITY = "check_availability"
    BOOK_APPOINTMENT = "book_appointment"
    CREATE_LEAD = "create_lead"
    ESCALATE_TO_OWNER = "escalate_to_owner"
    SEND_SMS_FOLLOWUP = "send_sms_followup"
    REQUEST_PHOTO_UPLOAD = "request_photo_upload"
    LOOKUP_JOB_STATUS = "lookup_job_status"
    CHECK_ROT_ELIGIBILITY = "check_rot_eligibility"
    TRANSFER_TO_HUMAN = "transfer_to_human"
    TAKE_MESSAGE = "take_message"
    DISABLE_RECORDING_FOR_CALL = "disable_recording_for_call"


class SmsTemplate(StrEnum):
    BOOKING_CONFIRMATION = "booking_confirmation"
    EMERGENCY_ACK = "emergency_ack"
    PHOTO_UPLOAD_LINK = "photo_upload_link"
    CALLBACK_PROMISE = "callback_promise"
    SECURE_FORM_LINK = "secure_form_link"


class AuditActor(StrEnum):
    SYSTEM = "system"
    AI = "ai"
    ADMIN = "admin"
    OWNER = "owner"


class AuditAction(StrEnum):
    TRANSCRIPT_REDACTED = "transcript.redacted"
    RECORDING_DISABLED = "recording.disabled"
    SCENARIO_RUN = "scenario.run"
    ADMIN_TOOL_TESTED = "admin.tool.tested"
    ADMIN_SMS_TESTED = "admin.sms.tested"
    ADMIN_ESCALATION_TESTED = "admin.escalation.tested"
    TRAINING_CORRECTION = "training.correction"


class AuditTargetType(StrEnum):
    CALL = "call"
    TOOL = "tool"
    PHONE = "phone"
    CUSTOMER = "customer"
    FIRMA = "firma"


class BridgeWSEvent(StrEnum):
    HELLO = "hello"
    AUDIO = "audio"
    SYNC = "sync"
    BYE = "bye"
    STOP = "stop"
    SENDING = "sending"
    LISTENING = "listening"
    INTERRUPT = "interrupt"
    TRANSCRIPT = "transcript"


class InboxEvent(StrEnum):
    CALL_CREATED = "inbox.call.created"
    CALL_UPDATED = "inbox.call.updated"


class BridgeBye(StrEnum):
    UNKNOWN_FIRMA = "unknown_firma"
    GEMINI_AUTH_FAILED = "gemini_auth_failed"
    GEMINI_MODEL_UNAVAILABLE = "gemini_model_unavailable"
    GEMINI_QUOTA_EXHAUSTED = "gemini_quota_exhausted"
    GEMINI_CONNECT_FAILED = "gemini_connect_failed"


class AudioFormat(StrEnum):
    PCM_16K = "pcm_16000"
    PCM_24K = "pcm_24000"


class AudioMimeType(StrEnum):
    PCM_16K = "audio/pcm;rate=16000"
    PCM_24K = "audio/pcm;rate=24000"


class ToolDispatchMode(StrEnum):
    LOCAL = "local"
    HTTP = "http"


class GeminiProvider(StrEnum):
    API_KEY = "api_key"
    VERTEX = "vertex"


class StorageMode(StrEnum):
    LOCAL = "local"
    GCS = "gcs"


class Environment(StrEnum):
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class AuthMode(StrEnum):
    DEV_HEADER = "dev_header"
    JWKS = "jwks"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ConsentMode(StrEnum):
    DISCLOSURE_OPTOUT = "disclosure_optout"
    EXPLICIT_OPTIN = "explicit_optin"


class TriageAction(StrEnum):
    ESCALATE_NOW = "escalate_now"
    BOOK_TODAY = "book_today"
    BOOK_NORMAL = "book_normal"
    INFORMATIONAL = "informational"


class TransferTarget(StrEnum):
    OWNER_MOBILE = "owner_mobile"
    OFFICE = "office"
    ON_CALL_TECHNICIAN = "on_call_technician"
    EXTERNAL_ANSWERING_SERVICE = "external_answering_service"


class Urgency(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TestSmsVia(StrEnum):
    LIVE = "live"
    SIMULATED = "simulated"

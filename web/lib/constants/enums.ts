import type {
  CallStatus as CallStatusType,
  CustomerType as CustomerTypeType,
  Intent as IntentType,
  Plan as PlanType,
  Severity as SeverityType,
  Trade as TradeType,
  TranscriptRole as TranscriptRoleType,
} from "../api-models";

export const CallStatus = {
  IN_PROGRESS: "in_progress",
  COMPLETED: "completed",
  HANDLED: "handled",
  NEEDS_FOLLOWUP: "needs_followup",
} as const satisfies Record<string, CallStatusType>;

export const Intent = {
  AKUT: "akut",
  OFFERT: "offertforfragan",
  BOKNING: "bokning",
  BEFINTLIG_KUND: "befintlig_kund_fraga",
  OVRIGT: "ovrigt",
} as const satisfies Record<string, IntentType>;

export const Severity = {
  CRITICAL: "critical",
  HIGH: "high",
  MEDIUM: "medium",
  LOW: "low",
} as const satisfies Record<string, SeverityType>;

export const Plan = {
  STARTER: "starter",
  PROFESSIONAL: "professional",
  PREMIUM: "premium",
} as const satisfies Record<string, PlanType>;

export const Trade = {
  VVS: "vvs",
  EL: "el",
  SNICKERI: "snickeri",
  TAK: "tak",
  KAKEL: "kakel",
  OVRIGT: "ovrigt",
} as const satisfies Record<string, TradeType>;

export const CustomerType = {
  PRIVATE: "private",
  COMPANY: "company",
} as const satisfies Record<string, CustomerTypeType>;

export const TranscriptRole = {
  CALLER: "caller",
  AI: "ai",
  SYSTEM: "system",
} as const satisfies Record<string, TranscriptRoleType>;

export const CallSource = {
  TELEPHONY: "telephony",
  VOICE_TEST: "voice_test",
  SCENARIO: "scenario",
} as const;
export type CallSource = (typeof CallSource)[keyof typeof CallSource];

export const IntegrationType = {
  FORTNOX: "fortnox",
  HANTVERKSDATA: "hantverksdata",
  VISMA: "visma",
  GOOGLE_CALENDAR: "google_calendar",
  OUTLOOK: "outlook",
} as const;
export type IntegrationType = (typeof IntegrationType)[keyof typeof IntegrationType];

export const SmsTemplate = {
  BOOKING_CONFIRMATION: "booking_confirmation",
  EMERGENCY_ACK: "emergency_ack",
  PHOTO_UPLOAD_LINK: "photo_upload_link",
  CALLBACK_PROMISE: "callback_promise",
  SECURE_FORM_LINK: "secure_form_link",
} as const;
export type SmsTemplate = (typeof SmsTemplate)[keyof typeof SmsTemplate];

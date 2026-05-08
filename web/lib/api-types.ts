/**
 * Hand-authored mirror of the backend's Pydantic schemas.
 * Phase 9 swaps this with `openapi-typescript` generated output.
 */

export type Intent =
  | "akut"
  | "offertforfragan"
  | "bokning"
  | "befintlig_kund_fraga"
  | "ovrigt";

export type Severity = "critical" | "high" | "medium" | "low";

export type CallStatus =
  | "in_progress"
  | "completed"
  | "handled"
  | "needs_followup";

export type TranscriptRole = "caller" | "ai" | "system";

export type Trade = "vvs" | "el" | "snickeri" | "tak" | "kakel" | "ovrigt";
export type Plan = "starter" | "professional" | "premium";
export type CustomerType = "private" | "company";

export interface CallRead {
  id: string;
  customer_id: string | null;
  customer_name: string | null;
  caller_phone: string | null;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number;
  intent: Intent | null;
  severity: Severity | null;
  status: CallStatus;
  summary_short: string | null;
}

export interface CallSummary {
  short_sv: string;
  long_sv: string;
  next_action_sv: string;
  owner_action_required: boolean;
  structured_fields?: Record<string, unknown>;
}

export interface TranscriptSegmentRead {
  role: TranscriptRole;
  text: string;
  ts_ms_offset: number;
}

export interface ToolInvocationRead {
  name: string;
  args: Record<string, unknown>;
  result: Record<string, unknown> | null;
  latency_ms: number;
  error: string | null;
  invoked_at: string;
}

export interface CallDetailRead extends CallRead {
  summary: CallSummary | null;
  transcript: TranscriptSegmentRead[];
  tool_invocations: ToolInvocationRead[];
  recording_url: string | null;
}

export interface Address {
  street: string;
  apartment?: string | null;
  postal_code?: string | null;
  city?: string | null;
  country?: string;
}

export interface CustomerRead {
  id: string;
  type: CustomerType;
  name: string;
  phone: string;
  email: string | null;
  org_number: string | null;
  address: Address | null;
  notes_summary: string | null;
  created_at: string;
}

export interface FirmaSettings {
  greeting_text: string;
  voice: string;
  open_hours_weekday: [string, string];
  open_hours_saturday: [string, string] | null;
  open_hours_sunday: [string, string] | null;
  answer_outside_hours: boolean;
  record_calls: boolean;
  recording_retention_days: number;
  transcript_retention_days: number;
  persona_overrides: string;
}

export interface FirmaRead {
  id: string;
  name: string;
  org_number: string | null;
  trade: Trade;
  plan: Plan;
  locality: string | null;
  settings: FirmaSettings;
  created_at: string;
}

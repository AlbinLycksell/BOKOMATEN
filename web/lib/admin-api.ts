"use client";

const FIRMA_ID = "01J0000FIRM0ANDERSSONSVVS00";

const headers = (): HeadersInit => ({
  "Content-Type": "application/json",
  "X-Firma-Id": FIRMA_ID,
});

export interface ScenarioPreset {
  id: string;
  name_sv: string;
  description_sv: string;
  trade: string;
  expected_intent: string;
  expected_severity: string | null;
  caller_phone: string;
  turn_count: number;
}

export interface ScenarioRunResult {
  call_id: string;
  intent: string | null;
  severity: string | null;
  tool_invocations: string[];
  summary_short: string | null;
}

export interface ToolListEntry {
  name: string;
  args_schema: { properties?: Record<string, unknown>; required?: string[] };
}

export interface AuditEntry {
  id: string;
  actor: string;
  action: string;
  target_type: string | null;
  target_id: string | null;
  payload: Record<string, unknown>;
  created_at: string;
}

async function jget<T>(path: string): Promise<T> {
  const r = await fetch(path, { headers: headers(), cache: "no-store" });
  if (!r.ok) throw new Error(`${r.status}: ${await r.text()}`);
  return (await r.json()) as T;
}

async function jpost<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(path, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${r.status}: ${await r.text()}`);
  return (await r.json()) as T;
}

export const adminApi = {
  systemPrompt: () =>
    jget<{ text: string; length_chars: number; estimated_tokens: number }>(
      "/api/proxy/admin/system-prompt",
    ),
  listScenarios: () => jget<ScenarioPreset[]>("/api/proxy/admin/scenarios"),
  runScenario: (id: string) =>
    jpost<ScenarioRunResult>(`/api/proxy/admin/scenarios/${id}/run`, {}),
  listTools: () => jget<ToolListEntry[]>("/api/proxy/admin/tools"),
  runTool: (name: string, args: Record<string, unknown>) =>
    jpost<{ name: string; result: Record<string, unknown> }>(
      "/api/proxy/admin/tools/run",
      { name, args },
    ),
  testSms: (
    to_phone: string,
    template: string,
    context_data: Record<string, unknown>,
  ) =>
    jpost<{ sent: boolean; sms_id: string; via: string }>(
      "/api/proxy/admin/test/sms",
      { to_phone, template, context_data },
    ),
  testEscalation: (severity: string, reason_sv: string) =>
    jpost<{ escalation_id: string; contacted: string[]; next_in_chain_minutes: number }>(
      "/api/proxy/admin/test/escalation",
      { severity, reason_sv },
    ),
  auditLog: (params: { actionPrefix?: string; hours?: number; limit?: number } = {}) => {
    const qs = new URLSearchParams();
    if (params.actionPrefix) qs.set("action_prefix", params.actionPrefix);
    if (params.hours) qs.set("hours", String(params.hours));
    if (params.limit) qs.set("limit", String(params.limit));
    const tail = qs.toString() ? `?${qs.toString()}` : "";
    return jget<AuditEntry[]>(`/api/proxy/admin/audit-log${tail}`);
  },
  runEval: () =>
    jpost<{
      total: number;
      intent_accuracy: number;
      severity_accuracy: number;
      emergency_false_negatives: number;
      by_intent: Record<string, number>;
      failures: Array<{ call_id: string; actual_intent: string | null; actual_severity: string | null }>;
    }>("/api/proxy/admin/eval/run", {}),
  toolsLatency: () =>
    jget<
      Array<{
        name: string;
        n: number;
        p50_ms: number;
        p95_ms: number;
        p99_ms: number;
        error_rate: number;
        breaches_p95: boolean;
      }>
    >("/api/proxy/admin/metrics/tools/latency"),
};

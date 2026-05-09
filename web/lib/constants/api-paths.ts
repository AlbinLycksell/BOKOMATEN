export const ApiPath = {
  CALLS: "/api/calls",
  CALL: (id: string) => `/api/calls/${encodeURIComponent(id)}`,
  CALL_MARK_HANDLED: (id: string) => `/api/calls/${encodeURIComponent(id)}/mark-handled`,
  CALL_TRAIN: (id: string) => `/api/calls/${encodeURIComponent(id)}/train`,
  CUSTOMERS: "/api/customers",
  CUSTOMER: (id: string) => `/api/customers/${encodeURIComponent(id)}`,
  FIRMA_ME: "/api/firma/me",
  FIRMA_ME_SETTINGS: "/api/firma/me/settings",
  HEALTH: "/health",
} as const;

export const AdminApiPath = {
  VOICE_TEST_READY: "/api/proxy/admin/voice-test/ready",
  SYSTEM_PROMPT: "/api/proxy/admin/system-prompt",
  SCENARIOS: "/api/proxy/admin/scenarios",
  SCENARIO_RUN: (id: string) => `/api/proxy/admin/scenarios/${encodeURIComponent(id)}/run`,
  TOOLS: "/api/proxy/admin/tools",
  TOOLS_RUN: "/api/proxy/admin/tools/run",
  TEST_SMS: "/api/proxy/admin/test/sms",
  TEST_ESCALATION: "/api/proxy/admin/test/escalation",
  AUDIT_LOG: "/api/proxy/admin/audit-log",
  EVAL_RUN: "/api/proxy/admin/eval/run",
  TOOLS_LATENCY: "/api/proxy/admin/metrics/tools/latency",
} as const;

export const ProxyApiPath = {
  INTEGRATIONS_STATUS: "/api/proxy/integrations/status",
  FIRMA_ME_SETTINGS: "/api/proxy/firma/me/settings",
  INTEGRATION_CONNECT: (slug: string) =>
    `/api/proxy/integrations/${encodeURIComponent(slug)}/connect`,
} as const;

export const ServerApiPath = {
  ADMIN_SCENARIOS: "/api/admin/scenarios",
  ADMIN_TOOLS: "/api/admin/tools",
  CALLS_BY_SOURCE: (source: string, limit: number) =>
    `/api/calls?source=${encodeURIComponent(source)}&limit=${limit}`,
} as const;

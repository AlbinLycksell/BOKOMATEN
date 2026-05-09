export const QueryKey = {
  calls: (intent: string | null = null, status: string | null = null, source: string | null = null) =>
    ["calls", intent, status, source] as const,
  callsAll: () => ["calls"] as const,
  call: (id: string) => ["call", id] as const,
  customers: (q: string | null = null) => ["customers", q] as const,
  firma: () => ["firma"] as const,
  integrationsStatus: () => ["integrations-status"] as const,
} as const;

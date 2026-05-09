import type {
  CallDetailRead,
  CallRead,
  CustomerRead,
  FirmaRead,
  Intent,
} from "./api-models";

const API_BASE =
  typeof window === "undefined"
    ? process.env.SWITCHBOARD_API_BASE ?? "http://127.0.0.1:8000"
    : "/api/proxy" in window
      ? "/api/proxy"
      : "";

const FIRMA_HEADER: Record<string, string> = {
  "X-Firma-Id": "01J0000FIRM0ANDERSSONSVVS00",
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...FIRMA_HEADER,
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}: ${await res.text()}`);
  }
  return (await res.json()) as T;
}

export async function listCalls(filters?: {
  intent?: Intent;
  status?: string;
  limit?: number;
}): Promise<CallRead[]> {
  const qs = new URLSearchParams();
  if (filters?.intent) qs.set("intent", filters.intent);
  if (filters?.status) qs.set("status", filters.status);
  if (filters?.limit) qs.set("limit", String(filters.limit));
  const query = qs.toString() ? `?${qs.toString()}` : "";
  return request<CallRead[]>(`/api/calls${query}`);
}

export async function getCall(id: string): Promise<CallDetailRead> {
  return request<CallDetailRead>(`/api/calls/${encodeURIComponent(id)}`);
}

export async function listCustomers(q?: string): Promise<CustomerRead[]> {
  const query = q ? `?q=${encodeURIComponent(q)}` : "";
  return request<CustomerRead[]>(`/api/customers${query}`);
}

export async function getFirma(): Promise<FirmaRead> {
  return request<FirmaRead>(`/api/firma/me`);
}

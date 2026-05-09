import type {
  CallDetailRead,
  CallRead,
  CustomerRead,
  FirmaRead,
  Intent,
} from "./api-models";
import { ApiPath } from "./constants/api-paths";
import { DEMO_FIRMA_ID } from "./constants/firma";
import { ContentType, FetchCache, HttpHeader } from "./constants/headers";

const API_BASE =
  typeof window === "undefined"
    ? process.env.SWITCHBOARD_API_BASE ?? "http://127.0.0.1:8000"
    : "/api/proxy" in window
      ? "/api/proxy"
      : "";

const FIRMA_HEADER: Record<string, string> = {
  [HttpHeader.FIRMA_ID]: DEMO_FIRMA_ID,
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      [HttpHeader.CONTENT_TYPE]: ContentType.JSON,
      ...FIRMA_HEADER,
      ...init?.headers,
    },
    cache: FetchCache.NO_STORE,
  });
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}: ${await res.text()}`);
  }
  return (await res.json()) as T;
}

export async function listCalls(filters?: {
  intent?: Intent;
  status?: string;
  source?: string;
  limit?: number;
}): Promise<CallRead[]> {
  const qs = new URLSearchParams();
  if (filters?.intent) qs.set("intent", filters.intent);
  if (filters?.status) qs.set("status", filters.status);
  if (filters?.source) qs.set("source", filters.source);
  if (filters?.limit) qs.set("limit", String(filters.limit));
  const query = qs.toString() ? `?${qs.toString()}` : "";
  return request<CallRead[]>(`${ApiPath.CALLS}${query}`);
}

export async function getCall(id: string): Promise<CallDetailRead> {
  return request<CallDetailRead>(ApiPath.CALL(id));
}

export async function listCustomers(q?: string): Promise<CustomerRead[]> {
  const query = q ? `?q=${encodeURIComponent(q)}` : "";
  return request<CustomerRead[]>(`${ApiPath.CUSTOMERS}${query}`);
}

export async function getFirma(): Promise<FirmaRead> {
  return request<FirmaRead>(ApiPath.FIRMA_ME);
}

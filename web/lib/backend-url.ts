/**
 * Where the backend lives — for WebSockets that have to bypass Next.js
 * dev-server rewrites (which only proxy HTTP, not WS).
 *
 * Resolution order:
 * 1. `NEXT_PUBLIC_BACKEND_WS_BASE` env var (e.g. "ws://127.0.0.1:8000",
 *    "wss://api.switchboard.se"). Set in `web/.env.local` for dev or in
 *    Cloud Run env in prod.
 * 2. Dev convenience: if served from port 3000 (Next dev) on localhost,
 *    reroute to port 8000 (FastAPI default).
 * 3. Same origin — works when web and backend are reverse-proxied together
 *    behind one ingress.
 */

const EXPLICIT = process.env.NEXT_PUBLIC_BACKEND_WS_BASE;

export function backendWsBase(): string {
  if (EXPLICIT) return EXPLICIT.replace(/\/$/, "");
  if (typeof window === "undefined") return "";
  const { protocol, hostname, port, host } = window.location;
  // Dev: Next dev server on :3000 → assume FastAPI on :8000 of the same host.
  if (port === "3000" && (hostname === "localhost" || hostname === "127.0.0.1")) {
    return `ws://${hostname}:8000`;
  }
  const wsProto = protocol === "https:" ? "wss:" : "ws:";
  return `${wsProto}//${host}`;
}

export function bridgeWsUrl(firmaId: string, callId: string): string {
  return `${backendWsBase()}/ws/bridge/${encodeURIComponent(firmaId)}/${encodeURIComponent(callId)}`;
}

export function inboxWsUrl(firmaId: string): string {
  return `${backendWsBase()}/ws/inbox/${encodeURIComponent(firmaId)}`;
}

"use client";

import { useEffect, useRef } from "react";

import type { CallRead } from "./api-models";

type InboxEvent =
  | { event: "inbox.call.created"; payload: { id: string; started_at: string } }
  | { event: "inbox.call.updated"; payload: Partial<CallRead> & { id: string } };

interface UseInboxWebSocketOpts {
  firmaId: string;
  onEvent: (msg: InboxEvent) => void;
}

const WS_URL = (firmaId: string) => {
  if (typeof window === "undefined") return null;
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = process.env.NEXT_PUBLIC_BACKEND_WS ?? window.location.host;
  return `${proto}//${host.replace(/^https?:\/\//, "")}/ws/inbox/${encodeURIComponent(firmaId)}`;
};

export function useInboxWebSocket({ firmaId, onEvent }: UseInboxWebSocketOpts) {
  const onEventRef = useRef(onEvent);
  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    const url = WS_URL(firmaId);
    if (!url) return;
    let closed = false;
    let backoffMs = 1_000;
    let ws: WebSocket | null = null;
    const open = () => {
      if (closed) return;
      ws = new WebSocket(url);
      ws.onopen = () => {
        backoffMs = 1_000;
      };
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data) as InboxEvent;
          onEventRef.current(msg);
        } catch {
          /* ignore malformed */
        }
      };
      ws.onclose = () => {
        if (closed) return;
        backoffMs = Math.min(backoffMs * 2, 30_000);
        setTimeout(open, backoffMs);
      };
      ws.onerror = () => ws?.close();
    };
    open();
    return () => {
      closed = true;
      ws?.close();
    };
  }, [firmaId]);
}

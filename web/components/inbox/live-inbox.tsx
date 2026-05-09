"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";

import { CallRow } from "@/components/inbox/call-row";
import { useInboxWebSocket } from "@/lib/inbox-ws";
import { useCallsQuery } from "@/lib/queries";
import type { CallRead, Intent } from "@/lib/api-models";

const FIRMA_ID = "01J0000FIRM0ANDERSSONSVVS00";

interface LiveInboxProps {
  initialData: CallRead[];
  intent?: Intent;
}

export function LiveInbox({ initialData, intent }: LiveInboxProps) {
  const qc = useQueryClient();
  const { data, isFetching } = useCallsQuery({ intent });
  const calls = data ?? initialData;
  const [pulse, setPulse] = useState<string | null>(null);
  const lastCreatedRef = useRef<string | null>(null);

  useInboxWebSocket({
    firmaId: FIRMA_ID,
    onEvent: (msg) => {
      qc.invalidateQueries({ queryKey: ["calls"] });
      if (msg.event === "inbox.call.created") {
        lastCreatedRef.current = msg.payload.id;
        setPulse(msg.payload.id);
        setTimeout(() => setPulse(null), 2_000);
      }
    },
  });

  useEffect(() => {
    if (!pulse) return;
    qc.invalidateQueries({ queryKey: ["call", pulse] });
  }, [pulse, qc]);

  return (
    <div className="flex-1 overflow-y-auto bg-bg" aria-busy={isFetching}>
      <div className="mx-auto max-w-4xl border-x border-border bg-surface">
        {calls.length === 0 ? (
          <EmptyState />
        ) : (
          calls.map((c: CallRead) => (
            <div
              key={c.id}
              className={
                c.id === pulse
                  ? "transition-colors bg-accent-soft"
                  : "transition-colors"
              }
            >
              <CallRow call={c} />
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
      <div className="text-4xl">📭</div>
      <h2 className="mt-4 text-base font-medium text-text-strong">
        Inga samtal ännu
      </h2>
      <p className="mt-1 max-w-sm text-sm text-text-muted">
        När det första samtalet kommer in dyker det upp här direkt — ingen sida att uppdatera.
      </p>
    </div>
  );
}

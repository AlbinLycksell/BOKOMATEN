"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";

import { CallRow } from "@/components/inbox/call-row";
import { useInboxWebSocket } from "@/lib/inbox-ws";
import { useCallsQuery } from "@/lib/queries";
import type { CallRead, Intent } from "@/lib/api-models";
import { CallSource } from "@/lib/constants/enums";
import { DEMO_FIRMA_ID } from "@/lib/constants/firma";
import { QueryKey } from "@/lib/constants/query-keys";
import { InboxEvent } from "@/lib/constants/ws";

const PULSE_DURATION_MS = 2_000;

interface LiveInboxProps {
  initialData: CallRead[];
  intent?: Intent;
}

export function LiveInbox({ initialData, intent }: LiveInboxProps) {
  const qc = useQueryClient();
  const { data, isFetching } = useCallsQuery({ intent, source: CallSource.TELEPHONY });
  const calls = data ?? initialData;
  const [pulse, setPulse] = useState<string | null>(null);
  const lastCreatedRef = useRef<string | null>(null);

  useInboxWebSocket({
    firmaId: DEMO_FIRMA_ID,
    onEvent: (msg) => {
      qc.invalidateQueries({ queryKey: QueryKey.callsAll() });
      if (msg.event === InboxEvent.CALL_CREATED) {
        lastCreatedRef.current = msg.payload.id;
        setPulse(msg.payload.id);
        setTimeout(() => setPulse(null), PULSE_DURATION_MS);
      }
    },
  });

  useEffect(() => {
    if (!pulse) return;
    qc.invalidateQueries({ queryKey: QueryKey.call(pulse) });
  }, [pulse, qc]);

  return (
    <div className="flex-1 overflow-y-auto bg-linne" aria-busy={isFetching}>
      <div className="mx-auto max-w-5xl px-8 lg:px-12 py-10">
        <div className="flex items-baseline justify-between mb-5">
          <h2 className="font-display text-[28px] leading-[1.1] tracking-[-0.015em] font-semibold text-text-strong">
            I natt
          </h2>
          <span className="text-sm text-text-muted">
            {calls.length} samtal
          </span>
        </div>
        {calls.length === 0 ? (
          <EmptyState />
        ) : (
          <ul className="list-none m-0 p-0">
            {calls.map((c: CallRead) => (
              <li
                key={c.id}
                className={
                  c.id === pulse
                    ? "transition-colors bg-signaloranje-soft/40"
                    : "transition-colors"
                }
              >
                <CallRow call={c} />
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="border-t border-border py-16 text-center">
      <p className="font-display text-[20px] font-medium text-text-strong">
        Det är tyst i kväll.
      </p>
      <p className="mt-2 text-[15px] text-text-muted max-w-md mx-auto">
        När det första samtalet kommer in dyker det upp här direkt — ingen sida att uppdatera.
      </p>
    </div>
  );
}

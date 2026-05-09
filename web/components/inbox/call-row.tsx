import Link from "next/link";

import { ChevronRightIcon } from "@/components/icons";
import { IntentBadge } from "./intent-badge";
import { formatTimeSv } from "@/lib/format";
import type { CallRead } from "@/lib/api-models";
import { CallSource } from "@/lib/constants/enums";

const SOURCE_LABELS: Record<CallSource, string | undefined> = {
  [CallSource.TELEPHONY]: undefined,
  [CallSource.VOICE_TEST]: "Röstprov",
  [CallSource.SCENARIO]: "Scenario",
};

export function CallRow({ call }: { call: CallRead }) {
  const source = call.source as CallSource;
  const sourceLabel = SOURCE_LABELS[source];
  const customer = call.customer_name ?? call.caller_phone ?? "Okänd ringare";

  return (
    <Link
      href={`/calls/${encodeURIComponent(call.id)}`}
      className="group grid grid-cols-[60px_1fr_18px] items-start gap-5 py-5 border-t border-border first:border-t-0 hover:bg-linne-deep/40 transition-colors"
    >
      <span className="font-mono text-[13px] tracking-[0.02em] text-text-muted v-tnum pt-0.5">
        {formatTimeSv(call.started_at)}
      </span>

      <div className="min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <IntentBadge intent={call.intent} />
          <span className="font-display text-[17px] font-medium tracking-[-0.005em] text-text-strong">
            {customer}
          </span>
          {sourceLabel ? (
            <>
              <span className="text-border-strong">·</span>
              <span className="text-sm text-text-muted">{sourceLabel}</span>
            </>
          ) : null}
        </div>
        <div className="mt-1 text-[15px] text-text">
          {call.summary_short ?? "Ingen sammanfattning ännu"}
        </div>
        {call.caller_phone && call.customer_name ? (
          <div className="mt-1 text-[13px] text-text-muted v-tnum">
            {call.caller_phone}
          </div>
        ) : null}
      </div>

      <ChevronRightIcon
        className="h-[18px] w-[18px] text-grey-300 self-center justify-self-end transition-colors group-hover:text-text-muted"
        strokeWidth={1.75}
      />
    </Link>
  );
}

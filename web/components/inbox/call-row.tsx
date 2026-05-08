import Link from "next/link";

import { ChevronRightIcon, ClockIcon } from "@/components/icons";
import { IntentBadge } from "./intent-badge";
import { SeverityDot } from "./severity-dot";
import { formatDurationSv, formatTimeAgoSv } from "@/lib/format";
import type { CallRead } from "@/lib/api-models";

export function CallRow({ call }: { call: CallRead }) {
  return (
    <Link
      href={`/calls/${encodeURIComponent(call.id)}`}
      className="group flex items-center gap-4 px-5 py-4 border-b border-border last:border-b-0 hover:bg-surface-2 transition-colors"
    >
      <SeverityDot severity={call.severity} />

      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-2">
          <span className="text-sm font-medium text-text-strong truncate">
            {call.customer_name ?? call.caller_phone ?? "Okänd nummer"}
          </span>
          <IntentBadge intent={call.intent} />
        </div>
        <p className="mt-0.5 text-sm text-text-muted truncate">
          {call.summary_short ?? "Ingen sammanfattning ännu"}
        </p>
      </div>

      <div className="hidden md:flex flex-col items-end gap-1 text-xs text-text-muted">
        <span className="flex items-center gap-1">
          <ClockIcon className="h-3.5 w-3.5" />
          {formatTimeAgoSv(call.started_at)}
        </span>
        <span>{formatDurationSv(call.duration_seconds)}</span>
      </div>

      <ChevronRightIcon className="h-4 w-4 text-text-faint group-hover:text-text-muted transition-colors" />
    </Link>
  );
}

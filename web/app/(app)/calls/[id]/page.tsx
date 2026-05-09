import { notFound } from "next/navigation";

import { Topbar } from "@/components/shell/topbar";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Eyebrow } from "@/components/ui/eyebrow";
import { ActionsBar } from "@/components/call/actions-bar";
import { CustomerCard } from "@/components/call/customer-card";
import { SummaryCard } from "@/components/call/summary-card";
import { Transcript } from "@/components/call/transcript";
import { AudioPlayer } from "@/components/ui/audio-player";
import { IntentBadge } from "@/components/inbox/intent-badge";
import { SeverityDot } from "@/components/inbox/severity-dot";
import { getCall } from "@/lib/api";
import { formatDateSv, formatTimeSv, formatDurationSv } from "@/lib/format";
import type { ToolInvocationRead } from "@/lib/api-models";
import { CallSource } from "@/lib/constants/enums";

const SOURCE_LABELS: Record<CallSource, string | undefined> = {
  [CallSource.TELEPHONY]: undefined,
  [CallSource.VOICE_TEST]: "Röstprov",
  [CallSource.SCENARIO]: "Scenario",
};

export const dynamic = "force-dynamic";

export default async function CallPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let call;
  try {
    call = await getCall(id);
  } catch {
    notFound();
  }

  return (
    <>
      <Topbar
        title={call.customer_name ?? call.caller_phone ?? "Okänd ringare"}
        description={`${formatDateSv(call.started_at)} · ${formatTimeSv(call.started_at)} · ${formatDurationSv(call.duration_seconds)}`}
        actions={
          <div className="flex items-center gap-3">
            <SeverityDot severity={call.severity} />
            <IntentBadge intent={call.intent} />
            {SOURCE_LABELS[call.source as CallSource] ? (
              <Badge variant="neutral">
                {SOURCE_LABELS[call.source as CallSource]}
              </Badge>
            ) : null}
          </div>
        }
      />

      <div className="flex-1 overflow-y-auto bg-linne">
        <div className="mx-auto max-w-6xl px-8 lg:px-12 py-10 grid gap-8 lg:grid-cols-[1fr_320px]">
          <div className="flex flex-col gap-6 min-w-0">
            <SummaryCard summary={call.summary} />

            <Card>
              <CardContent className="px-6 py-6 flex flex-col gap-4">
                <Eyebrow>Inspelning</Eyebrow>
                <AudioPlayer
                  src={call.recording_url}
                  duration={call.duration_seconds}
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="px-6 py-6 flex flex-col gap-4">
                <Eyebrow>Utskrift</Eyebrow>
                <Transcript segments={call.transcript} />
              </CardContent>
            </Card>

            {call.tool_invocations.length > 0 ? (
              <Card>
                <CardContent className="px-6 py-6 flex flex-col gap-4">
                  <Eyebrow>Verktygsanrop</Eyebrow>
                  <ul className="grid gap-2">
                    {call.tool_invocations.map(
                      (t: ToolInvocationRead, i: number) => (
                        <li
                          key={i}
                          className="flex items-center justify-between text-sm border-b border-border pb-2 last:border-b-0 last:pb-0"
                        >
                          <span className="font-mono text-[13px] text-text-strong">
                            {t.name}
                          </span>
                          <span className="font-mono text-xs text-text-muted v-tnum">
                            {t.latency_ms} ms
                          </span>
                        </li>
                      ),
                    )}
                  </ul>
                </CardContent>
              </Card>
            ) : null}
          </div>

          <aside className="flex flex-col gap-6">
            <CustomerCard
              name={call.customer_name}
              phone={call.caller_phone}
              email={null}
              notesSummary={null}
            />
            <Card>
              <CardContent className="px-6 py-6 flex flex-col gap-4">
                <Eyebrow>Åtgärder</Eyebrow>
                <ActionsBar />
              </CardContent>
            </Card>
          </aside>
        </div>
      </div>
    </>
  );
}

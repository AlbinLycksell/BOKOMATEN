import { notFound } from "next/navigation";

import { Topbar } from "@/components/shell/topbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ActionsBar } from "@/components/call/actions-bar";
import { CustomerCard } from "@/components/call/customer-card";
import { SummaryCard } from "@/components/call/summary-card";
import { Transcript } from "@/components/call/transcript";
import { AudioPlayer } from "@/components/ui/audio-player";
import { IntentBadge } from "@/components/inbox/intent-badge";
import { SeverityDot } from "@/components/inbox/severity-dot";
import { getCall } from "@/lib/api";
import { formatDateSv, formatTimeSv, formatDurationSv } from "@/lib/format";

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
          <div className="flex items-center gap-2">
            <SeverityDot severity={call.severity} />
            <IntentBadge intent={call.intent} />
          </div>
        }
      />

      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-6 py-6 grid gap-6 lg:grid-cols-[1fr_320px]">
          <div className="flex flex-col gap-6 min-w-0">
            <SummaryCard summary={call.summary} />

            <Card>
              <CardHeader>
                <CardTitle>Inspelning</CardTitle>
              </CardHeader>
              <CardContent>
                <AudioPlayer
                  src={call.recording_url}
                  duration={call.duration_seconds}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Transkription</CardTitle>
              </CardHeader>
              <CardContent>
                <Transcript segments={call.transcript} />
              </CardContent>
            </Card>

            {call.tool_invocations.length > 0 ? (
              <Card>
                <CardHeader>
                  <CardTitle>Verktygsanrop</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="flex flex-col gap-2">
                    {call.tool_invocations.map((t, i) => (
                      <li
                        key={i}
                        className="flex items-center justify-between text-sm border-b border-border pb-2 last:border-b-0 last:pb-0"
                      >
                        <span className="font-mono text-xs text-text-strong">{t.name}</span>
                        <span className="text-xs text-text-muted">{t.latency_ms} ms</span>
                      </li>
                    ))}
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
              <CardHeader>
                <CardTitle>Åtgärder</CardTitle>
              </CardHeader>
              <CardContent>
                <ActionsBar />
              </CardContent>
            </Card>
          </aside>
        </div>
      </div>
    </>
  );
}

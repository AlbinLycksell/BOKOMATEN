import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Eyebrow } from "@/components/ui/eyebrow";
import type { CallSummary } from "@/lib/api-models";

export function SummaryCard({ summary }: { summary: CallSummary | null }) {
  if (!summary) {
    return (
      <Card>
        <CardContent className="px-6 py-6">
          <Eyebrow className="mb-3">Sammanfattning</Eyebrow>
          <p className="text-[15px] text-text-muted">
            AI-sammanfattningen genereras strax efter att samtalet avslutats.
          </p>
        </CardContent>
      </Card>
    );
  }
  return (
    <Card>
      <CardContent className="px-6 py-6 flex flex-col gap-5">
        <div className="flex items-center justify-between gap-3">
          <Eyebrow>Sammanfattning</Eyebrow>
          {summary.owner_action_required ? (
            <Badge variant="warning">Åtgärd krävs</Badge>
          ) : (
            <Badge variant="bokad">Hanterad</Badge>
          )}
        </div>
        <p className="font-display text-[20px] leading-[1.35] tracking-[-0.005em] font-medium text-text-strong">
          {summary.short_sv}
        </p>
        <p className="text-[15px] leading-[1.6] text-text">{summary.long_sv}</p>
        <div className="rounded-[10px] bg-linne-deep px-4 py-3">
          <Eyebrow className="mb-1">Nästa åtgärd</Eyebrow>
          <p className="text-[15px] text-text-strong font-medium">
            {summary.next_action_sv}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

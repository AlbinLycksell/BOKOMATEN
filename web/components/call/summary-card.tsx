import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { CallSummary } from "@/lib/api-models";

export function SummaryCard({ summary }: { summary: CallSummary | null }) {
  if (!summary) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Sammanfattning</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-text-muted">
            AI-sammanfattningen genereras strax efter att samtalet avslutats.
          </p>
        </CardContent>
      </Card>
    );
  }
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Sammanfattning</CardTitle>
          {summary.owner_action_required ? (
            <Badge variant="warning">Åtgärd krävs</Badge>
          ) : (
            <Badge variant="success">Hanterad</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <p className="text-base font-medium text-text-strong leading-relaxed">
          {summary.short_sv}
        </p>
        <p className="text-sm text-text leading-relaxed">{summary.long_sv}</p>
        <div className="rounded-md border border-border bg-surface-2 px-4 py-3">
          <p className="text-xs uppercase tracking-wide text-text-muted">Nästa åtgärd</p>
          <p className="mt-1 text-sm text-text-strong">{summary.next_action_sv}</p>
        </div>
      </CardContent>
    </Card>
  );
}

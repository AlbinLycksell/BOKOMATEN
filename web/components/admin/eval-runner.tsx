"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { adminApi } from "@/lib/admin-api";

export function EvalRunner() {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<{
    total: number;
    intent_accuracy: number;
    severity_accuracy: number;
    emergency_false_negatives: number;
    by_intent: Record<string, number>;
    failures: Array<{ call_id: string; actual_intent: string | null; actual_severity: string | null }>;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setRunning(true);
    setError(null);
    setResult(null);
    try {
      setResult(await adminApi.runEval());
    } catch (e) {
      setError(String(e));
    } finally {
      setRunning(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Eval-körning</CardTitle>
          <Button onClick={run} disabled={running}>
            {running ? "Kör…" : "Kör eval"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="grid gap-4">
        <p className="text-sm text-text-muted">
          Kör den medföljande eval-datasetet (
          <code className="rounded bg-surface-2 px-1">backend/eval/sample.jsonl</code>) mot
          den nuvarande triage-logiken. Posten Slack-digesten varje söndag är samma
          beräkning över ett större labelat dataset.
        </p>
        {error ? <p className="text-sm text-critical">Fel: {error}</p> : null}
        {result ? (
          <div className="grid gap-3">
            <div className="grid gap-2 md:grid-cols-3">
              <Stat label="Antal" value={result.total} />
              <Stat
                label="Intent accuracy"
                value={`${(result.intent_accuracy * 100).toFixed(1)}%`}
                tone={result.intent_accuracy >= 0.85 ? "success" : "warning"}
              />
              <Stat
                label="Akut false negatives"
                value={result.emergency_false_negatives}
                tone={result.emergency_false_negatives === 0 ? "success" : "critical"}
              />
            </div>
            <div className="rounded-md border border-border bg-surface-2 p-3">
              <div className="text-xs uppercase tracking-wide text-text-muted">
                Distribution
              </div>
              <div className="mt-2 flex flex-wrap gap-2 text-sm">
                {Object.entries(result.by_intent).map(([k, v]) => (
                  <Badge key={k} variant="neutral">
                    {k}: {v}
                  </Badge>
                ))}
              </div>
            </div>
            {result.failures.length > 0 ? (
              <div className="rounded-md border border-border bg-surface-2 p-3">
                <div className="text-xs uppercase tracking-wide text-text-muted">
                  Misslyckanden ({result.failures.length})
                </div>
                <ul className="mt-2 grid gap-1 text-xs">
                  {result.failures.map((f, i) => (
                    <li key={i} className="font-mono">
                      {f.call_id} → intent={f.actual_intent} severity={f.actual_severity}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string | number;
  tone?: "success" | "warning" | "critical";
}) {
  const ringTone =
    tone === "success"
      ? "border-success-soft"
      : tone === "warning"
        ? "border-warning-soft"
        : tone === "critical"
          ? "border-critical-soft"
          : "border-border";
  return (
    <div className={`rounded-md border ${ringTone} bg-surface p-3`}>
      <div className="text-xs uppercase tracking-wide text-text-muted">{label}</div>
      <div className="mt-1 text-lg font-semibold text-text-strong">{value}</div>
    </div>
  );
}

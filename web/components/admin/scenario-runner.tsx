"use client";

import { useState } from "react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { adminApi, type ScenarioPreset, type ScenarioRunResult } from "@/lib/admin-api";

interface Props {
  presets: ScenarioPreset[];
}

const INTENT_VARIANT: Record<string, "critical" | "info" | "accent" | "neutral" | "success"> = {
  akut: "critical",
  offertforfragan: "info",
  bokning: "accent",
  befintlig_kund_fraga: "neutral",
  ovrigt: "neutral",
};

export function ScenarioRunner({ presets }: Props) {
  const [running, setRunning] = useState<string | null>(null);
  const [result, setResult] = useState<{ presetId: string; r: ScenarioRunResult } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async (id: string) => {
    setRunning(id);
    setError(null);
    setResult(null);
    try {
      const r = await adminApi.runScenario(id);
      setResult({ presetId: id, r });
    } catch (e) {
      setError(String(e));
    } finally {
      setRunning(null);
    }
  };

  return (
    <div className="grid gap-4">
      <div className="grid gap-3 md:grid-cols-2">
        {presets.map((p) => (
          <Card key={p.id}>
            <CardHeader>
              <div className="flex items-center justify-between gap-2">
                <CardTitle>{p.name_sv}</CardTitle>
                <Badge variant={INTENT_VARIANT[p.expected_intent] ?? "neutral"}>
                  {p.expected_intent}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <p className="text-sm text-text-muted">{p.description_sv}</p>
              <div className="flex items-center gap-2 text-xs text-text-faint">
                <span>{p.trade.toUpperCase()}</span>
                <span>·</span>
                <span>{p.turn_count} kund-yttranden</span>
                {p.expected_severity ? (
                  <>
                    <span>·</span>
                    <span>severity {p.expected_severity}</span>
                  </>
                ) : null}
              </div>
              <div className="flex items-center justify-between mt-1">
                <span className="text-xs text-text-faint">{p.caller_phone}</span>
                <Button
                  size="sm"
                  onClick={() => run(p.id)}
                  disabled={running !== null}
                >
                  {running === p.id ? "Kör…" : "Kör scenariot"}
                </Button>
              </div>
              {result && result.presetId === p.id ? (
                <div className="mt-2 rounded-md border border-border bg-surface-2 p-3 text-xs">
                  <div className="flex items-center gap-2">
                    <strong className="text-text-strong">Resultat</strong>
                    {result.r.intent ? (
                      <Badge variant={INTENT_VARIANT[result.r.intent] ?? "neutral"}>
                        {result.r.intent}
                      </Badge>
                    ) : null}
                    {result.r.severity ? (
                      <Badge variant="warning">severity: {result.r.severity}</Badge>
                    ) : null}
                  </div>
                  {result.r.summary_short ? (
                    <p className="mt-2 text-text-muted">{result.r.summary_short}</p>
                  ) : null}
                  {result.r.tool_invocations.length > 0 ? (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {result.r.tool_invocations.map((t) => (
                        <code
                          key={t}
                          className="rounded bg-surface px-1.5 py-0.5 text-[11px] font-mono text-text"
                        >
                          {t}
                        </code>
                      ))}
                    </div>
                  ) : null}
                  <div className="mt-2">
                    <Link
                      href={`/calls/${encodeURIComponent(result.r.call_id)}`}
                      className="text-accent hover:underline"
                    >
                      Öppna samtalet i inkorgen →
                    </Link>
                  </div>
                </div>
              ) : null}
            </CardContent>
          </Card>
        ))}
      </div>
      {error ? (
        <p className="text-sm text-critical">Fel: {error}</p>
      ) : null}
    </div>
  );
}

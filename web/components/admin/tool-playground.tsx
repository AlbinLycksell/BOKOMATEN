"use client";

import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { adminApi, type ToolListEntry } from "@/lib/admin-api";

interface Props {
  tools: ToolListEntry[];
}

const SEEDED_ARGS: Record<string, Record<string, unknown>> = {
  lookup_customer: { phone_number: "+46708557777" },
  triage_emergency: {
    problem_description: "vattenläcka, det rinner ner på golvet",
    trade: "vvs",
    indicators_present: ["lacka", "rinner"],
  },
  check_rot_eligibility: {
    is_private_person: true,
    owns_property: true,
    property_age_years: 30,
    work_type: "badrumsrenovering",
  },
  send_sms_followup: {
    to_phone: "+46708555000",
    template: "callback_promise",
    context_data: { name: "Test" },
  },
};

export function ToolPlayground({ tools }: Props) {
  const [name, setName] = useState<string>(tools[0]?.name ?? "");
  const seed = useMemo(
    () => SEEDED_ARGS[name] ?? {},
    [name],
  );
  const [argsText, setArgsText] = useState<string>(JSON.stringify(seed, null, 2));
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<unknown | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onSelect = (next: string) => {
    setName(next);
    const newSeed = SEEDED_ARGS[next] ?? {};
    setArgsText(JSON.stringify(newSeed, null, 2));
    setResult(null);
    setError(null);
  };

  const run = async () => {
    setRunning(true);
    setError(null);
    setResult(null);
    let parsed: Record<string, unknown> = {};
    try {
      parsed = argsText.trim() ? JSON.parse(argsText) : {};
    } catch (e) {
      setError(`Ogiltig JSON: ${e}`);
      setRunning(false);
      return;
    }
    try {
      const r = await adminApi.runTool(name, parsed);
      setResult(r.result);
    } catch (e) {
      setError(String(e));
    } finally {
      setRunning(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Verktygslek</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4">
        <div className="grid gap-1.5">
          <Label htmlFor="tool-select">Verktyg</Label>
          <Select id="tool-select" value={name} onChange={(e) => onSelect(e.target.value)}>
            {tools.map((t) => (
              <option key={t.name} value={t.name}>
                {t.name}
              </option>
            ))}
          </Select>
        </div>

        <div className="grid gap-1.5">
          <Label htmlFor="args">Args (JSON)</Label>
          <Textarea
            id="args"
            value={argsText}
            onChange={(e) => setArgsText(e.target.value)}
            rows={10}
            spellCheck={false}
          />
        </div>

        <div className="flex items-center gap-2">
          <Button onClick={run} disabled={running}>
            {running ? "Kör…" : "Kör verktyget"}
          </Button>
          {error ? <span className="text-sm text-critical">{error}</span> : null}
        </div>

        {result !== null ? (
          <div className="rounded-md border border-border bg-surface-2 p-3">
            <Label>Resultat</Label>
            <pre className="mt-2 max-h-72 overflow-auto text-xs font-mono whitespace-pre-wrap">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

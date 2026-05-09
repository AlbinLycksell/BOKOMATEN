"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { adminApi } from "@/lib/admin-api";

const SMS_TEMPLATES = [
  "callback_promise",
  "booking_confirmation",
  "emergency_ack",
  "photo_upload_link",
  "secure_form_link",
] as const;

const SEVERITIES = ["critical", "high", "medium", "low"] as const;

export function TestActions() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <TestSmsCard />
      <TestEscalationCard />
    </div>
  );
}

function TestSmsCard() {
  const [phone, setPhone] = useState("+46708555000");
  const [template, setTemplate] = useState<string>("callback_promise");
  const [name, setName] = useState("Magnus");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const run = async () => {
    setRunning(true);
    setResult(null);
    try {
      const r = await adminApi.testSms(phone, template, { name });
      setResult(`${r.sent ? "✓ Skickat" : "✗ Misslyckades"} (${r.via}) — sms_id ${r.sms_id}`);
    } catch (e) {
      setResult(`Fel: ${e}`);
    } finally {
      setRunning(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Test-SMS</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3">
        <div className="grid gap-1.5">
          <Label htmlFor="sms-to">Mottagare (E.164)</Label>
          <Input id="sms-to" value={phone} onChange={(e) => setPhone(e.target.value)} />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="sms-template">Mall</Label>
          <Select id="sms-template" value={template} onChange={(e) => setTemplate(e.target.value)}>
            {SMS_TEMPLATES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </Select>
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="sms-name">Mall-variabel: name</Label>
          <Input id="sms-name" value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <Button onClick={run} disabled={running}>
          {running ? "Skickar…" : "Skicka test-SMS"}
        </Button>
        {result ? <p className="text-xs text-text-muted">{result}</p> : null}
      </CardContent>
    </Card>
  );
}

function TestEscalationCard() {
  const [severity, setSeverity] = useState<string>("high");
  const [reason, setReason] = useState("Testäskalering från admin");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const run = async () => {
    setRunning(true);
    setResult(null);
    try {
      const r = await adminApi.testEscalation(severity, reason);
      setResult(
        `Eskalering ${r.escalation_id} skapad. Kontaktade: ${
          r.contacted.length === 0 ? "(ingen on-call konfigurerad)" : r.contacted.join(", ")
        }`,
      );
    } catch (e) {
      setResult(`Fel: ${e}`);
    } finally {
      setRunning(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Test-eskalering</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3">
        <div className="grid gap-1.5">
          <Label htmlFor="esc-severity">Severity</Label>
          <Select
            id="esc-severity"
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
          >
            {SEVERITIES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </Select>
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="esc-reason">Anledning (sv)</Label>
          <Input id="esc-reason" value={reason} onChange={(e) => setReason(e.target.value)} />
        </div>
        <Button variant="critical" onClick={run} disabled={running}>
          {running ? "Eskalerar…" : "Kör test-eskalering"}
        </Button>
        {result ? <p className="text-xs text-text-muted">{result}</p> : null}
      </CardContent>
    </Card>
  );
}

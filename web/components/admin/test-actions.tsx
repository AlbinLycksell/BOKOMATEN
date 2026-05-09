"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { adminApi } from "@/lib/admin-api";
import { Severity, SmsTemplate } from "@/lib/constants/enums";

const SMS_TEMPLATE_VALUES = [
  SmsTemplate.CALLBACK_PROMISE,
  SmsTemplate.BOOKING_CONFIRMATION,
  SmsTemplate.EMERGENCY_ACK,
  SmsTemplate.PHOTO_UPLOAD_LINK,
  SmsTemplate.SECURE_FORM_LINK,
] as const;

const SEVERITY_VALUES = [
  Severity.CRITICAL,
  Severity.HIGH,
  Severity.MEDIUM,
  Severity.LOW,
] as const;

const DEFAULT_TEST_PHONE = "+46708555000";
const DEFAULT_TEST_NAME = "Magnus";
const DEFAULT_REASON_SV = "Testäskalering från admin";

export function TestActions() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <TestSmsCard />
      <TestEscalationCard />
    </div>
  );
}

function TestSmsCard() {
  const [phone, setPhone] = useState(DEFAULT_TEST_PHONE);
  const [template, setTemplate] = useState<SmsTemplate>(SmsTemplate.CALLBACK_PROMISE);
  const [name, setName] = useState(DEFAULT_TEST_NAME);
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
          <Select
            id="sms-template"
            value={template}
            onChange={(e) => setTemplate(e.target.value as SmsTemplate)}
          >
            {SMS_TEMPLATE_VALUES.map((t) => (
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
  const [severity, setSeverity] = useState<string>(Severity.HIGH);
  const [reason, setReason] = useState(DEFAULT_REASON_SV);
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
            {SEVERITY_VALUES.map((s) => (
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

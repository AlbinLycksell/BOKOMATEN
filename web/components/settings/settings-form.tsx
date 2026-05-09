"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { useFirmaQuery } from "@/lib/queries";

const FIRMA_HEADER: Record<string, string> = {
  "X-Firma-Id": "01J0000FIRM0ANDERSSONSVVS00",
  "Content-Type": "application/json",
};

const VOICES = ["Aoede", "Charon", "Leda", "Zephyr", "Kore", "Puck"];

interface FirmaSettingsForm {
  greeting_text: string;
  voice: string;
  open_hours_start: string;
  open_hours_end: string;
  answer_outside_hours: boolean;
  record_calls: boolean;
  recording_retention_days: number;
  persona_overrides: string;
  consent_disclosure_sv: string;
  sms_sender_id: string;
  brand_color_accent: string;
}

interface IntegrationStatus {
  type: string;
  connected: boolean;
}

const INTEGRATION_LABELS: Record<string, { label: string; description: string }> = {
  fortnox: {
    label: "Fortnox",
    description: "Kundregister, fakturor, kalender — synkas dygnet runt.",
  },
  hantverksdata: {
    label: "Hantverksdata Next",
    description: "Projektsystem, arbetsorder, resursplanering. Kräver partneravtal.",
  },
  visma: {
    label: "Visma eEkonomi",
    description: "Bokföring och kalender för Visma-användare.",
  },
  google_calendar: {
    label: "Google Calendar",
    description: "Bidirektionell kalendersynk.",
  },
  outlook: {
    label: "Outlook 365",
    description: "Kommer i Phase 2.",
  },
};

export function SettingsForm() {
  const qc = useQueryClient();
  const firmaQ = useFirmaQuery();
  const integrationsQ = useQuery<IntegrationStatus[]>({
    queryKey: ["integrations-status"],
    queryFn: async () => {
      const r = await fetch("/api/proxy/integrations/status", {
        headers: FIRMA_HEADER,
      });
      if (!r.ok) return [];
      return r.json();
    },
  });

  const firma = firmaQ.data;

  const [form, setForm] = useState<FirmaSettingsForm | null>(null);

  // Sync form once firma loads
  if (firma && form === null) {
    setForm({
      greeting_text: firma.settings.greeting_text,
      voice: firma.settings.voice,
      open_hours_start: firma.settings.open_hours_weekday[0],
      open_hours_end: firma.settings.open_hours_weekday[1],
      answer_outside_hours: firma.settings.answer_outside_hours,
      record_calls: firma.settings.record_calls,
      recording_retention_days: firma.settings.recording_retention_days,
      persona_overrides: firma.settings.persona_overrides,
      consent_disclosure_sv: firma.settings.consent_disclosure_sv ?? "",
      sms_sender_id: firma.settings.sms_sender_id ?? "",
      brand_color_accent: firma.settings.brand_color_accent ?? "",
    });
  }

  const save = useMutation({
    mutationFn: async (payload: FirmaSettingsForm) => {
      const body: Record<string, unknown> = {
        greeting_text: payload.greeting_text,
        voice: payload.voice,
        open_hours_weekday: [payload.open_hours_start, payload.open_hours_end],
        answer_outside_hours: payload.answer_outside_hours,
        record_calls: payload.record_calls,
        recording_retention_days: payload.recording_retention_days,
        persona_overrides: payload.persona_overrides,
        consent_disclosure_sv: payload.consent_disclosure_sv,
        sms_sender_id: payload.sms_sender_id || null,
        brand_color_accent: payload.brand_color_accent || null,
      };
      const r = await fetch("/api/proxy/firma/me/settings", {
        method: "PUT",
        headers: FIRMA_HEADER,
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error(`${r.status}: ${await r.text()}`);
      return r.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["firma"] });
    },
  });

  if (firmaQ.isLoading || !firma || !form) {
    return (
      <Card>
        <CardContent>
          <p className="py-8 text-sm text-text-muted text-center">Laddar inställningar…</p>
        </CardContent>
      </Card>
    );
  }

  const update = <K extends keyof FirmaSettingsForm>(k: K, v: FirmaSettingsForm[K]) =>
    setForm({ ...form, [k]: v });

  return (
    <div className="grid gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Firma</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <Field label="Namn" value={firma.name} />
          <Field label="Org-nummer" value={firma.org_number ?? "—"} />
          <Field label="Ort" value={firma.locality ?? "—"} />
          <Field label="Bransch" value={firma.trade} />
          <Field label="Plan" value={firma.plan} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Hälsning &amp; röst</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="greeting">Standardhälsning</Label>
            <Textarea
              id="greeting"
              value={form.greeting_text}
              onChange={(e) => update("greeting_text", e.target.value)}
              rows={3}
            />
            <p className="text-xs text-text-faint">
              Använd <code className="rounded bg-surface-2 px-1">{"{firma_namn}"}</code> som platshållare.
            </p>
          </div>
          <div className="grid gap-1.5 max-w-sm">
            <Label htmlFor="voice">Röst</Label>
            <Select
              id="voice"
              value={form.voice}
              onChange={(e) => update("voice", e.target.value)}
            >
              {VOICES.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Öppettider &amp; inspelning</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="grid gap-1.5">
              <Label htmlFor="hours-start">Öppnar (vardag)</Label>
              <Input
                id="hours-start"
                value={form.open_hours_start}
                onChange={(e) => update("open_hours_start", e.target.value)}
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="hours-end">Stänger (vardag)</Label>
              <Input
                id="hours-end"
                value={form.open_hours_end}
                onChange={(e) => update("open_hours_end", e.target.value)}
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="retention">Inspelnings­retention (dagar)</Label>
              <Input
                id="retention"
                type="number"
                min={0}
                max={365}
                value={form.recording_retention_days}
                onChange={(e) =>
                  update("recording_retention_days", Number(e.target.value))
                }
              />
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <Toggle
              label="Svara utanför öppettider"
              checked={form.answer_outside_hours}
              onChange={(v) => update("answer_outside_hours", v)}
            />
            <Toggle
              label="Spela in samtal"
              checked={form.record_calls}
              onChange={(v) => update("record_calls", v)}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>GDPR-disclosure</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3">
          <Label htmlFor="consent">Vad AI:n läser upp i början av varje samtal</Label>
          <Textarea
            id="consent"
            value={form.consent_disclosure_sv}
            onChange={(e) => update("consent_disclosure_sv", e.target.value)}
            rows={3}
          />
          <p className="text-xs text-text-faint">
            Standard: PRD §9.2. Lämna tomt för att stänga av (då infogas
            ingen disclosure i system-prompten).
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Persona-anpassning</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3">
          <Label htmlFor="persona">Tonläge / stil-anvisningar</Label>
          <Textarea
            id="persona"
            value={form.persona_overrides}
            onChange={(e) => update("persona_overrides", e.target.value)}
            rows={5}
            placeholder="T.ex. Magnus är rak men varm. Använd 'kanon' när det passar."
          />
          {firma.settings.persona_corrections &&
          firma.settings.persona_corrections.length > 0 ? (
            <div className="rounded-md border border-border bg-surface-2 p-3">
              <Label>Träna AI — rättningar (senaste 15)</Label>
              <ul className="mt-2 grid gap-1 text-xs text-text-muted">
                {firma.settings.persona_corrections
                  .slice(-15)
                  .map((c: string, i: number) => (
                    <li key={i}>• {c}</li>
                  ))}
              </ul>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>SMS &amp; varumärke</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="grid gap-1.5 max-w-sm">
            <Label htmlFor="sender">SMS sender id (per-firma alias)</Label>
            <Input
              id="sender"
              value={form.sms_sender_id}
              onChange={(e) => update("sms_sender_id", e.target.value)}
              placeholder="Anderssons VVS"
            />
            <p className="text-xs text-text-faint">
              Skickas i SMS när 46elks-verifieringen är klar (3–5 arbetsdagar). Tomt
              fält → faller tillbaka på platformens
              <code className="mx-1 rounded bg-surface-2 px-1">Switchboard</code>.
              {firma.settings.sms_sender_id_verified ? (
                <Badge variant="success" className="ml-2">
                  Verifierad
                </Badge>
              ) : (
                <Badge variant="warning" className="ml-2">
                  Inte verifierad
                </Badge>
              )}
            </p>
          </div>
          <Separator />
          <div className="grid gap-1.5 max-w-sm">
            <Label htmlFor="brand-color">Varumärkesfärg (Premium)</Label>
            <div className="flex items-center gap-2">
              <Input
                id="brand-color"
                type="text"
                placeholder="#1E5C3A"
                value={form.brand_color_accent}
                onChange={(e) => update("brand_color_accent", e.target.value)}
              />
              {form.brand_color_accent ? (
                <span
                  aria-hidden
                  className="inline-block h-9 w-9 rounded-md border border-border"
                  style={{ background: form.brand_color_accent }}
                />
              ) : null}
            </div>
            <p className="text-xs text-text-faint">
              Ersätter accent-färgen i hela dashboarden för Premium-tier.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Integrationer</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3">
          {(integrationsQ.data ?? []).map((it, i, arr) => {
            const meta = INTEGRATION_LABELS[it.type] ?? {
              label: it.type,
              description: "",
            };
            return (
              <div key={it.type}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-text-strong">
                        {meta.label}
                      </span>
                      <Badge variant={it.connected ? "success" : "neutral"}>
                        {it.connected ? "Ansluten" : "Inte ansluten"}
                      </Badge>
                    </div>
                    <p className="mt-1 text-sm text-text-muted">{meta.description}</p>
                  </div>
                  <a
                    href={`/api/proxy/integrations/${it.type === "google_calendar" ? "google-calendar" : it.type}/connect`}
                    className="text-sm text-accent hover:underline"
                  >
                    {it.connected ? "Hantera" : "Anslut"}
                  </a>
                </div>
                {i < arr.length - 1 ? <Separator className="mt-3" /> : null}
              </div>
            );
          })}
        </CardContent>
      </Card>

      <div className="sticky bottom-0 -mx-6 px-6 py-4 bg-bg/90 backdrop-blur border-t border-border flex items-center justify-end gap-3">
        {save.isError ? (
          <span className="text-sm text-critical">Kunde inte spara.</span>
        ) : save.isSuccess ? (
          <span className="text-sm text-success">Sparat ✓</span>
        ) : null}
        <Button onClick={() => save.mutate(form)} disabled={save.isPending}>
          {save.isPending ? "Sparar…" : "Spara ändringar"}
        </Button>
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid gap-1.5">
      <Label>{label}</Label>
      <p className="text-sm text-text-strong">{value}</p>
    </div>
  );
}

function Toggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="inline-flex items-center gap-3 cursor-pointer">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="h-4 w-4 accent-accent"
      />
      <span className="text-sm text-text">{label}</span>
    </label>
  );
}

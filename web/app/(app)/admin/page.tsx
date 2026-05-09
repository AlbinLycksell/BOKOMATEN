import { Topbar } from "@/components/shell/topbar";
import { Card, CardContent } from "@/components/ui/card";
import { ScenarioRunner } from "@/components/admin/scenario-runner";
import { ToolPlayground } from "@/components/admin/tool-playground";
import { SystemPromptPreview } from "@/components/admin/system-prompt-preview";
import { TestActions } from "@/components/admin/test-actions";
import { AuditLogViewer } from "@/components/admin/audit-log-viewer";
import { EvalRunner } from "@/components/admin/eval-runner";
import { VoiceTest } from "@/components/admin/voice-test";

export const dynamic = "force-dynamic";

const BACKEND = process.env.SVARSA_API_BASE ?? "http://127.0.0.1:8000";
const FIRMA_ID = "01J0000FIRM0ANDERSSONSVVS00";

async function fetchJson<T>(path: string): Promise<T> {
  const r = await fetch(`${BACKEND}${path}`, {
    headers: { "X-Firma-Id": FIRMA_ID },
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`${r.status}`);
  return (await r.json()) as T;
}

async function loadScenarios() {
  try {
    return await fetchJson<
      Array<{
        id: string;
        name_sv: string;
        description_sv: string;
        trade: string;
        expected_intent: string;
        expected_severity: string | null;
        caller_phone: string;
        turn_count: number;
      }>
    >("/api/admin/scenarios");
  } catch {
    return [];
  }
}

async function loadTools() {
  try {
    return await fetchJson<Array<{ name: string; args_schema: Record<string, unknown> }>>(
      "/api/admin/tools",
    );
  } catch {
    return [];
  }
}

export default async function AdminPage() {
  const [presets, tools] = await Promise.all([loadScenarios(), loadTools()]);

  return (
    <>
      <Topbar
        title="Admin"
        description="Emulera samtal, kör verktyg, skicka test-SMS, läs audit-loggen"
      />
      <div className="flex-1 overflow-y-auto bg-bg">
        <div className="mx-auto max-w-6xl px-6 py-6 grid gap-8">
          <Section title="Röstprov (live)">
            <p className="text-sm text-text-muted mb-4">
              Riktigt ljud, riktig Gemini Live, samma WebSocket-bridge som 46elks
              använder i produktion. Klicka starta och prata med AI:n från
              webbläsaren — transkript och verktygsanrop landar i inkorgen direkt.
            </p>
            <VoiceTest />
          </Section>

          <Section title="Emulera samtal (text)">
            <p className="text-sm text-text-muted mb-4">
              Kör hela pipen deterministiskt — triage, verktygsplaybook,
              post-call-summering, audit-logg, kostnadsspårning. Ingen audio,
              ingen Gemini-anslutning krävs. Bra för CI / utveckling.
            </p>
            {presets.length === 0 ? (
              <Card>
                <CardContent>
                  <p className="py-6 text-sm text-text-muted">
                    Backend kunde inte nås. Starta uvicorn på port 8000.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <ScenarioRunner presets={presets} />
            )}
          </Section>

          <Section title="Verktygslek">
            {tools.length === 0 ? (
              <Card>
                <CardContent>
                  <p className="py-6 text-sm text-text-muted">
                    Inga verktyg laddade. Starta backend och ladda om sidan.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <ToolPlayground tools={tools} />
            )}
          </Section>

          <Section title="System prompt">
            <SystemPromptPreview />
          </Section>

          <Section title="Test-aktioner">
            <TestActions />
          </Section>

          <Section title="Eval">
            <EvalRunner />
          </Section>

          <Section title="Audit log">
            <AuditLogViewer />
          </Section>
        </div>
      </div>
    </>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="text-base font-semibold text-text-strong tracking-tight mb-3">
        {title}
      </h2>
      {children}
    </section>
  );
}

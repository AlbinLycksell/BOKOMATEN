import Link from "next/link";

import { Topbar } from "@/components/shell/topbar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ScenarioRunner } from "@/components/admin/scenario-runner";
import { ToolPlayground } from "@/components/admin/tool-playground";
import { SystemPromptPreview } from "@/components/admin/system-prompt-preview";
import { TestActions } from "@/components/admin/test-actions";
import { AuditLogViewer } from "@/components/admin/audit-log-viewer";
import { EvalRunner } from "@/components/admin/eval-runner";
import { VoiceTest } from "@/components/admin/voice-test";
import { formatTimeSv, formatDateSv, formatDurationSv } from "@/lib/format";
import type { CallRead } from "@/lib/api-models";
import { ServerApiPath } from "@/lib/constants/api-paths";
import { CallSource } from "@/lib/constants/enums";
import { DEMO_FIRMA_ID } from "@/lib/constants/firma";
import { FetchCache, HttpHeader } from "@/lib/constants/headers";

export const dynamic = "force-dynamic";

const BACKEND_BASE_ENV = "SWITCHBOARD_API_BASE";
const DEFAULT_BACKEND_BASE = "http://127.0.0.1:8000";
const TEST_CALLS_PER_SOURCE = 5;
const TEST_CALLS_TOTAL = 8;

const BACKEND = process.env[BACKEND_BASE_ENV] ?? DEFAULT_BACKEND_BASE;

async function fetchJson<T>(path: string): Promise<T> {
  const r = await fetch(`${BACKEND}${path}`, {
    headers: { [HttpHeader.FIRMA_ID]: DEMO_FIRMA_ID },
    cache: FetchCache.NO_STORE,
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
    >(ServerApiPath.ADMIN_SCENARIOS);
  } catch {
    return [];
  }
}

async function loadTools() {
  try {
    return await fetchJson<Array<{ name: string; args_schema: Record<string, unknown> }>>(
      ServerApiPath.ADMIN_TOOLS,
    );
  } catch {
    return [];
  }
}

async function loadTestCalls() {
  try {
    const [voiceCalls, scenarioCalls] = await Promise.all([
      fetchJson<CallRead[]>(ServerApiPath.CALLS_BY_SOURCE(CallSource.VOICE_TEST, TEST_CALLS_PER_SOURCE)),
      fetchJson<CallRead[]>(ServerApiPath.CALLS_BY_SOURCE(CallSource.SCENARIO, TEST_CALLS_PER_SOURCE)),
    ]);
    return [...voiceCalls, ...scenarioCalls].sort(
      (a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime(),
    ).slice(0, TEST_CALLS_TOTAL);
  } catch {
    return [];
  }
}

export default async function AdminPage() {
  const [presets, tools, testCalls] = await Promise.all([loadScenarios(), loadTools(), loadTestCalls()]);

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

          <Section title="Senaste testsamtal">
            {testCalls.length === 0 ? (
              <Card>
                <CardContent>
                  <p className="py-4 text-sm text-text-muted">
                    Inga testsamtal ännu — kör ett röstprov eller ett scenario så dyker det upp här.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="p-0">
                  <ul className="divide-y divide-border">
                    {testCalls.map((c) => (
                      <li key={c.id}>
                        <Link
                          href={`/calls/${encodeURIComponent(c.id)}`}
                          className="flex items-center gap-3 px-4 py-3 hover:bg-surface-2 transition-colors"
                        >
                          <Badge variant="neutral" className="shrink-0">
                            {c.source === CallSource.VOICE_TEST ? "Röstprov" : "Scenario"}
                          </Badge>
                          <span className="text-sm text-text-muted shrink-0">
                            {c.caller_phone ?? "—"}
                          </span>
                          <span className="text-xs text-text-faint">
                            {formatDateSv(c.started_at)} {formatTimeSv(c.started_at)}
                          </span>
                          <span className="text-xs text-text-faint">
                            {formatDurationSv(c.duration_seconds)}
                          </span>
                          <span className="ml-auto text-xs text-text-muted truncate max-w-xs">
                            {c.summary_short ?? "Summering genereras…"}
                          </span>
                          <span className="text-havsbla text-xs shrink-0 font-medium">Öppna →</span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
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

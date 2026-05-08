import { Topbar } from "@/components/shell/topbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { getFirma } from "@/lib/api";

export const dynamic = "force-dynamic";

interface IntegrationCard {
  name: string;
  description: string;
  status: "connected" | "available";
}

const INTEGRATIONS: IntegrationCard[] = [
  {
    name: "Fortnox",
    description: "Kundregister, faktura, kalender — synkas dygnet runt.",
    status: "available",
  },
  {
    name: "Hantverksdata Next",
    description: "Projektsystem, arbetsorder, resursplanering. Kräver partneravtal.",
    status: "available",
  },
  {
    name: "Visma eEkonomi",
    description: "Bokföring och kalender för Visma-användare.",
    status: "available",
  },
  {
    name: "Google Calendar",
    description: "Bidirektionell kalendersynk.",
    status: "available",
  },
];

export default async function SettingsPage() {
  let firma;
  try {
    firma = await getFirma();
  } catch {
    firma = null;
  }
  return (
    <>
      <Topbar
        title="Inställningar"
        description="Din firma, din persona, dina integrationer"
      />
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-6 py-6 flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Firma</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="name">Namn</Label>
                <Input id="name" defaultValue={firma?.name ?? ""} />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="org">Org-nummer</Label>
                <Input id="org" defaultValue={firma?.org_number ?? ""} />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="locality">Ort</Label>
                <Input id="locality" defaultValue={firma?.locality ?? ""} />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="trade">Bransch</Label>
                <Input id="trade" defaultValue={firma?.trade ?? "vvs"} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Hälsning</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <Label htmlFor="greeting">Standardhälsning</Label>
              <textarea
                id="greeting"
                defaultValue={firma?.settings.greeting_text ?? ""}
                className="min-h-24 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              />
              <p className="text-xs text-text-faint">
                Använd <code className="rounded bg-surface-2 px-1">{"{firma_namn}"}</code> som platshållare.
              </p>
              <div className="flex items-center justify-between mt-2">
                <span className="text-xs text-text-muted">
                  Röst: <strong className="text-text-strong">{firma?.settings.voice ?? "Aoede"}</strong>
                </span>
                <Button size="sm" variant="outline">Förhandslyssna</Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Integrationer</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              {INTEGRATIONS.map((it, i) => (
                <div key={it.name}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-text-strong">{it.name}</span>
                        <Badge variant={it.status === "connected" ? "success" : "neutral"}>
                          {it.status === "connected" ? "Ansluten" : "Inte ansluten"}
                        </Badge>
                      </div>
                      <p className="mt-1 text-sm text-text-muted">{it.description}</p>
                    </div>
                    <Button size="sm" variant="outline" disabled>
                      Anslut
                    </Button>
                  </div>
                  {i < INTEGRATIONS.length - 1 ? <Separator className="mt-3" /> : null}
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}

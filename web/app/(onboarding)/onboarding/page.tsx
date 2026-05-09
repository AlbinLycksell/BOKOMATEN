import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import Link from "next/link";

const STEPS = [
  {
    n: 1,
    title: "Firma",
    description: "Verifiera firmans namn, ort och bransch.",
  },
  {
    n: 2,
    title: "Telefon­nummer",
    description: "Välj ett 46elks-nummer eller porta in ditt befintliga.",
  },
  {
    n: 3,
    title: "Integrationer",
    description: "Anslut Fortnox, Visma eller Google Calendar.",
  },
  {
    n: 4,
    title: "Hälsning",
    description: "Välj röst, anpassa hälsningstexten, hör en förhandslyssning.",
  },
  {
    n: 5,
    title: "Eskaleringskedja",
    description: "Bestäm vem som rings vid akut.",
  },
  {
    n: 6,
    title: "Testringa",
    description: "Vi ringer ditt nummer, du svarar — så att du hör hur AI:n låter.",
  },
];

export default function OnboardingPage() {
  return (
    <div className="min-h-screen bg-bg py-10 px-6">
      <div className="mx-auto max-w-3xl">
        <header className="mb-8">
          <h1 className="text-2xl font-semibold text-text-strong tracking-tight">
            Välkommen till Svarsa AI
          </h1>
          <p className="mt-2 text-sm text-text-muted">
            Vi hjälper dig sätta upp Svarsa AI på 30 minuter. När du är klar
            börjar AI:n svara på dina samtal redan i kväll.
          </p>
        </header>

        <Card>
          <CardHeader>
            <CardTitle>1 · Firma</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="name">Firmanamn</Label>
              <Input id="name" placeholder="Anderssons VVS AB" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="org">Org-nummer</Label>
              <Input id="org" placeholder="556789-1234" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="locality">Ort</Label>
              <Input id="locality" placeholder="Bromma" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="trade">Bransch</Label>
              <Input id="trade" defaultValue="vvs" />
            </div>
          </CardContent>
        </Card>

        <Separator className="my-6" />

        <ol className="grid gap-3">
          {STEPS.slice(1).map((s) => (
            <li key={s.n}>
              <Card>
                <CardContent className="flex items-start gap-4 py-4">
                  <span className="grid place-items-center h-8 w-8 rounded-full bg-surface-2 text-text-muted text-sm font-semibold">
                    {s.n}
                  </span>
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-text-strong">
                      {s.title}
                    </div>
                    <p className="mt-0.5 text-sm text-text-muted">
                      {s.description}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </li>
          ))}
        </ol>

        <div className="mt-8 flex justify-end gap-2">
          <Link href="/inbox">
            <Button variant="outline">Hoppa över för nu</Button>
          </Link>
          <Button>Gå vidare till steg 2</Button>
        </div>
      </div>
    </div>
  );
}

import Link from "next/link";

import { Wordmark } from "@/components/brand/wordmark";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Eyebrow } from "@/components/ui/eyebrow";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";

const STEPS = [
  {
    n: 1,
    title: "Firma",
    description: "Verifiera firmans namn, ort och bransch.",
  },
  {
    n: 2,
    title: "Telefonnummer",
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
    <div className="min-h-screen bg-linne py-12 px-6">
      <div className="mx-auto max-w-3xl">
        <header className="mb-12 flex flex-col gap-6">
          <Wordmark size="md" />
          <div className="flex flex-col gap-3">
            <Eyebrow>Sätt upp · 6 steg · cirka 30 min</Eyebrow>
            <h1 className="font-display text-[40px] leading-[1.05] tracking-[-0.02em] font-semibold text-text-strong">
              Välkommen till Switchboard.
            </h1>
            <p className="text-[16px] leading-relaxed text-text max-w-2xl">
              Vi hjälper dig sätta upp på en halvtimme. När du är klar börjar
              AI:n svara på dina samtal redan i kväll.
            </p>
          </div>
        </header>

        <Card>
          <CardContent className="px-6 py-6 grid gap-5">
            <Eyebrow>1 · Firma</Eyebrow>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-2">
                <Label htmlFor="name">Firmanamn</Label>
                <Input id="name" placeholder="Anderssons VVS AB" />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="org">Org-nummer</Label>
                <Input id="org" placeholder="556789-1234" />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="locality">Ort</Label>
                <Input id="locality" placeholder="Bromma" />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="trade">Bransch</Label>
                <Input id="trade" defaultValue="vvs" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Separator className="my-8" />

        <ol className="grid gap-3">
          {STEPS.slice(1).map((s) => (
            <li key={s.n}>
              <Card variant="sunken">
                <CardContent className="flex items-start gap-4 px-6 py-4">
                  <span className="grid place-items-center h-9 w-9 rounded-full bg-havsbla text-linne font-mono text-sm font-medium">
                    {s.n}
                  </span>
                  <div className="min-w-0">
                    <div className="font-display text-[16px] font-medium text-text-strong">
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

        <div className="mt-10 flex justify-end gap-2">
          <Link href="/inbox">
            <Button variant="ghost" size="sm">
              Hoppa över för nu
            </Button>
          </Link>
          <Button variant="primary" size="sm">
            Gå vidare till steg 2
          </Button>
        </div>
      </div>
    </div>
  );
}

import { Fragment } from "react";

import { Topbar } from "@/components/shell/topbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const HOURS = ["07", "08", "09", "10", "11", "12", "13", "14", "15", "16"];
const DAYS = ["Mån", "Tis", "Ons", "Tor", "Fre"];

export default function BookingsPage() {
  return (
    <>
      <Topbar
        title="Bokningar"
        description="Veckovy — synkar med Hantverksdata Next och Google Calendar"
      />
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-6 py-6">
          <Card>
            <CardHeader>
              <CardTitle>Vecka 19 · 2026</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-[60px_repeat(5,1fr)] gap-px bg-border rounded-md overflow-hidden border border-border">
                <div className="bg-surface" />
                {DAYS.map((d) => (
                  <div
                    key={d}
                    className="bg-surface px-3 py-2 text-xs font-medium text-text-muted uppercase tracking-wide"
                  >
                    {d}
                  </div>
                ))}
                {HOURS.map((h) => (
                  <Fragment key={h}>
                    <div className="bg-surface px-3 py-3 text-xs text-text-muted text-right tabular-nums">
                      {h}:00
                    </div>
                    {DAYS.map((d) => (
                      <div
                        key={`${d}-${h}`}
                        className="bg-surface min-h-12 p-1.5 text-[11px] text-text-muted"
                      >
                        {h === "08" && d === "Tor" ? (
                          <div className="rounded-sm bg-accent-soft text-accent border border-accent-soft px-2 py-1">
                            OVK · 4 adress
                          </div>
                        ) : null}
                        {h === "10" && d === "Mån" ? (
                          <div className="rounded-sm bg-warning-soft text-warning border border-warning-soft px-2 py-1">
                            Akut · Storgatan 14
                          </div>
                        ) : null}
                        {h === "13" && d === "Ons" ? (
                          <div className="rounded-sm bg-info-soft text-info border border-info-soft px-2 py-1">
                            Uppmätning · Hökarängsplan 4
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </Fragment>
                ))}
              </div>
              <p className="mt-4 text-xs text-text-faint">
                Vy är demonstrativ — fullt kalender-API ansluts i Phase 1.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}

import { Fragment } from "react";

import { Topbar } from "@/components/shell/topbar";
import { Card, CardContent } from "@/components/ui/card";
import { Eyebrow } from "@/components/ui/eyebrow";

const HOURS = ["07", "08", "09", "10", "11", "12", "13", "14", "15", "16"];
const DAYS = ["mån", "tis", "ons", "tor", "fre"];

export default function BookingsPage() {
  return (
    <>
      <Topbar
        title="Kalender"
        description="Veckovy — synkar med Hantverksdata Next och Google Calendar"
      />
      <div className="flex-1 overflow-y-auto bg-linne">
        <div className="mx-auto max-w-5xl px-8 lg:px-12 py-10">
          <Card>
            <CardContent className="px-6 py-6">
              <div className="flex items-baseline justify-between mb-5">
                <Eyebrow>Vecka 19 · 2026</Eyebrow>
                <span className="text-sm text-text-muted">3 bokningar</span>
              </div>
              <div className="grid grid-cols-[60px_repeat(5,1fr)] border-t border-l border-border rounded-[10px] overflow-hidden">
                <div className="bg-linne-deep border-r border-b border-border" />
                {DAYS.map((d) => (
                  <div
                    key={d}
                    className="bg-linne-deep px-3 py-3 font-mono text-[12px] uppercase tracking-[0.06em] text-text-muted border-r border-b border-border"
                  >
                    {d}
                  </div>
                ))}
                {HOURS.map((h) => (
                  <Fragment key={h}>
                    <div className="bg-surface px-3 py-3 font-mono text-[12px] text-text-muted text-right v-tnum border-r border-b border-border">
                      {h}:00
                    </div>
                    {DAYS.map((d) => (
                      <div
                        key={`${d}-${h}`}
                        className="bg-surface min-h-12 p-1.5 text-[12px] border-r border-b border-border"
                      >
                        {h === "08" && d === "tor" ? (
                          <div className="rounded-[6px] bg-tallgron/12 text-tallgron px-2 py-1 font-mono uppercase tracking-[0.04em]">
                            OVK · 4 adress
                          </div>
                        ) : null}
                        {h === "10" && d === "mån" ? (
                          <div className="rounded-[6px] bg-signaloranje-soft text-signaloranje px-2 py-1 font-mono uppercase tracking-[0.04em]">
                            Akut · Storgatan 14
                          </div>
                        ) : null}
                        {h === "13" && d === "ons" ? (
                          <div className="rounded-[6px] bg-linne-deep text-text px-2 py-1 font-mono uppercase tracking-[0.04em]">
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

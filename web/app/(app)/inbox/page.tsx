import { BriefingHeader } from "@/components/shell/briefing-header";
import { Button } from "@/components/ui/button";
import { Stat, StatGrid } from "@/components/ui/stat";
import { FilterBar } from "@/components/inbox/filter-bar";
import { LiveInbox } from "@/components/inbox/live-inbox";
import { listCalls } from "@/lib/api";
import type { CallRead } from "@/lib/api-models";
import { CallSource } from "@/lib/constants/enums";
import { Intent, Severity } from "@/lib/constants/enums";

export const dynamic = "force-dynamic";

const INBOX_FETCH_LIMIT = 100;

const SE_DATE = new Intl.DateTimeFormat("sv-SE", {
  weekday: "long",
  day: "numeric",
  month: "long",
  timeZone: "Europe/Stockholm",
});

const SE_TIME = new Intl.DateTimeFormat("sv-SE", {
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "Europe/Stockholm",
});

async function loadCalls(): Promise<CallRead[]> {
  try {
    return await listCalls({
      source: CallSource.TELEPHONY,
      limit: INBOX_FETCH_LIMIT,
    });
  } catch {
    return [];
  }
}

export default async function InboxPage() {
  const calls = await loadCalls();
  const now = new Date();
  const akutCount = calls.filter(
    (c) => c.intent === Intent.AKUT || c.severity === Severity.HIGH || c.severity === Severity.CRITICAL,
  ).length;
  const bookedCount = calls.filter((c) => c.intent === Intent.BOKNING).length;
  const missedCount = calls.filter((c) => c.status === "needs_followup").length;

  return (
    <>
      <BriefingHeader
        eyebrow={`${SE_DATE.format(now)} · ${SE_TIME.format(now)}`}
        greeting="God morgon, Lena."
        body={
          akutCount > 0 ? (
            <>
              Du fångade <strong className="text-text-strong font-medium">
                {akutCount} akut{akutCount === 1 ? "jobb" : "jobb"}
              </strong>{" "}
              i natt — kosta dig själv en till kopp kaffe på det.
            </>
          ) : (
            "Det var lugnt i natt. Inget akut, inget missat."
          )
        }
        actions={
          <>
            <Button variant="ghost" size="sm">
              Skicka sammanfattning till Magnus
            </Button>
            <Button variant="secondary" size="sm">
              Ny bokning
            </Button>
          </>
        }
      />

      <div className="bg-linne pt-6 px-8 lg:px-12">
        <StatGrid>
          <Stat
            label="Samtal i natt"
            value={calls.length}
            hint={calls.length > 0 ? "uppdateras live" : "tyst"}
            positive={calls.length > 0}
          />
          <Stat
            label="Akutjobb"
            value={akutCount}
            hint={akutCount > 0 ? "alla bemannade" : "ingen panik"}
            positive
          />
          <Stat label="Bokningar" value={bookedCount} hint="till denna vecka" />
          <Stat
            label="Att följa upp"
            value={missedCount}
            hint={missedCount === 0 ? "senaste 14 dagar" : "väntar på dig"}
            positive={missedCount === 0}
          />
        </StatGrid>
      </div>

      <FilterBar />
      <LiveInbox initialData={calls} />
    </>
  );
}

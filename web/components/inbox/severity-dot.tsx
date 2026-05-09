import { StatusDot } from "@/components/ui/status-dot";
import type { Severity as SeverityType } from "@/lib/api-models";
import { Severity } from "@/lib/constants/enums";

const TONE: Record<SeverityType, "akut" | "critical" | "info" | "bokad"> = {
  [Severity.CRITICAL]: "critical",
  [Severity.HIGH]: "akut",
  [Severity.MEDIUM]: "info",
  [Severity.LOW]: "bokad",
};

export function SeverityDot({ severity }: { severity: SeverityType | null }) {
  if (!severity) {
    return (
      <span
        aria-label="ingen allvarsgrad"
        className="inline-block h-2 w-2 rounded-full bg-grey-300/60"
      />
    );
  }
  return <StatusDot tone={TONE[severity]} ariaLabel={`allvarsgrad ${severity}`} />;
}

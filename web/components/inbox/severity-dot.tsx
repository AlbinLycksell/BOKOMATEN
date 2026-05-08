import { cn } from "@/lib/utils";
import type { Severity } from "@/lib/api-types";

const COLOR: Record<Severity, string> = {
  critical: "bg-critical",
  high: "bg-warning",
  medium: "bg-info",
  low: "bg-success",
};

export function SeverityDot({ severity }: { severity: Severity | null }) {
  if (!severity) {
    return (
      <span
        aria-label="ingen allvarsgrad"
        className="inline-block h-2 w-2 rounded-full bg-surface-3 border border-border"
      />
    );
  }
  return (
    <span
      aria-label={`allvarsgrad ${severity}`}
      title={severity}
      className={cn("inline-block h-2 w-2 rounded-full", COLOR[severity])}
    />
  );
}

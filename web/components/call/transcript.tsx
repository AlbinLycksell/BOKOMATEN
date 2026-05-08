import { cn } from "@/lib/utils";
import type { TranscriptSegmentRead } from "@/lib/api-types";

const ROLE_LABEL: Record<TranscriptSegmentRead["role"], string> = {
  caller: "Kund",
  ai: "Svarsa",
  system: "System",
};

export function Transcript({ segments }: { segments: TranscriptSegmentRead[] }) {
  if (segments.length === 0) {
    return (
      <p className="text-sm text-text-muted">Ingen transkription tillgänglig.</p>
    );
  }
  return (
    <ol className="flex flex-col gap-3">
      {segments.map((seg, i) => (
        <li key={i} className="flex gap-3">
          <span
            className={cn(
              "mt-1 inline-block h-1.5 w-1.5 shrink-0 rounded-full",
              seg.role === "ai" ? "bg-accent" : "bg-text-muted",
            )}
          />
          <div className="min-w-0 flex-1">
            <div className="flex items-baseline gap-2 text-xs text-text-faint">
              <span className="font-medium text-text-muted uppercase tracking-wide">
                {ROLE_LABEL[seg.role]}
              </span>
              <span>{Math.floor(seg.ts_ms_offset / 1000)}s</span>
            </div>
            <p className="text-sm text-text leading-relaxed mt-0.5">{seg.text}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}

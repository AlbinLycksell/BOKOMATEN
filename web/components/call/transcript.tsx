import { cn } from "@/lib/utils";
import type { TranscriptSegmentRead } from "@/lib/api-models";
import { TranscriptRole } from "@/lib/constants/enums";

const ROLE_LABEL: Record<TranscriptSegmentRead["role"], string> = {
  [TranscriptRole.CALLER]: "Kund",
  [TranscriptRole.AI]: "AI",
  [TranscriptRole.SYSTEM]: "System",
};

function formatOffset(ms: number): string {
  const total = Math.floor(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export function Transcript({ segments }: { segments: TranscriptSegmentRead[] }) {
  if (segments.length === 0) {
    return (
      <p className="text-sm text-text-muted">Ingen transkription tillgänglig.</p>
    );
  }
  return (
    <div className="grid gap-2 text-[14px] leading-[1.5]">
      {segments.map((seg, i) => (
        <div
          key={i}
          className="grid grid-cols-[44px_56px_1fr] gap-2.5 items-baseline"
        >
          <span className="font-mono text-[12px] text-text-muted v-tnum">
            {formatOffset(seg.ts_ms_offset)}
          </span>
          <span
            className={cn(
              "font-mono text-[12px] font-medium uppercase tracking-[0.04em]",
              seg.role === TranscriptRole.AI
                ? "text-signaloranje"
                : "text-text-strong",
            )}
          >
            {ROLE_LABEL[seg.role]}
          </span>
          <span className="text-text">{seg.text}</span>
        </div>
      ))}
    </div>
  );
}

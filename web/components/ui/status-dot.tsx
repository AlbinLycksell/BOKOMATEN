import { cn } from "@/lib/utils";

type Tone = "akut" | "bokad" | "info" | "neutral" | "critical";

const TONES: Record<Tone, string> = {
  akut: "bg-signaloranje",
  bokad: "bg-tallgron",
  info: "bg-havsbla-70",
  neutral: "bg-grey-300",
  critical: "bg-larmrod",
};

interface StatusDotProps {
  tone?: Tone;
  className?: string;
  ariaLabel?: string;
  size?: number;
}

export function StatusDot({
  tone = "neutral",
  className,
  ariaLabel,
  size = 8,
}: StatusDotProps) {
  return (
    <span
      role={ariaLabel ? "img" : undefined}
      aria-label={ariaLabel}
      aria-hidden={!ariaLabel}
      className={cn("inline-block rounded-full", TONES[tone], className)}
      style={{ width: size, height: size }}
    />
  );
}

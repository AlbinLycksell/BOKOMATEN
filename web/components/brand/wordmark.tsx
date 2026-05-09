import { cn } from "@/lib/utils";

type Tone = "ink" | "linne";
type Size = "sm" | "md" | "lg" | "xl";

const SIZES: Record<Size, string> = {
  sm: "text-base",
  md: "text-lg",
  lg: "text-2xl",
  xl: "text-[28px]",
};

const TONES: Record<Tone, string> = {
  ink: "text-havsbla",
  linne: "text-linne",
};

interface WordmarkProps {
  tone?: Tone;
  size?: Size;
  className?: string;
  ariaLabel?: string;
}

export function Wordmark({
  tone = "ink",
  size = "md",
  className,
  ariaLabel = "Switchboard",
}: WordmarkProps) {
  return (
    <span
      role="img"
      aria-label={ariaLabel}
      className={cn(
        "font-display font-semibold tracking-[-0.025em] inline-flex items-baseline whitespace-nowrap leading-none",
        SIZES[size],
        TONES[tone],
        className,
      )}
    >
      Switchboard
      <span
        aria-hidden
        className="ml-[0.04em] inline-block rounded-full bg-signaloranje"
        style={{
          width: "0.36em",
          height: "0.36em",
          transform: "translateY(0.04em)",
        }}
      />
    </span>
  );
}

import { cn } from "@/lib/utils";

interface BrandMarkProps {
  size?: number;
  className?: string;
  ariaLabel?: string;
}

export function BrandMark({
  size = 32,
  className,
  ariaLabel = "Switchboard",
}: BrandMarkProps) {
  return (
    <span
      role="img"
      aria-label={ariaLabel}
      className={cn(
        "relative inline-grid place-items-center bg-havsbla text-linne font-display font-bold leading-none",
        className,
      )}
      style={{
        width: size,
        height: size,
        borderRadius: Math.round(size * 0.22),
        fontSize: Math.round(size * 0.62),
        letterSpacing: "-0.04em",
      }}
    >
      <span style={{ transform: `translate(${-size * 0.06}px, ${size * 0.04}px)` }}>S</span>
      <span
        aria-hidden
        className="absolute rounded-full bg-signaloranje"
        style={{
          width: Math.max(4, Math.round(size * 0.22)),
          height: Math.max(4, Math.round(size * 0.22)),
          right: Math.round(size * 0.18),
          top: Math.round(size * 0.34),
        }}
      />
    </span>
  );
}

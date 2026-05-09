import { type HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type Variant =
  | "neutral"
  | "akut"
  | "info"
  | "bokad"
  | "critical"
  | "warning"
  | "success"
  | "accent";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: Variant;
}

/**
 * Verkstad status pill — mono uppercase, tinted background.
 * Bg is 12% tint of the foreground per design system rules.
 */
const VARIANTS: Record<Variant, string> = {
  neutral: "text-grey-500 bg-[var(--linne-deep)]",
  akut: "text-signaloranje bg-[var(--signaloranje-soft)]",
  info: "text-grey-500 bg-[var(--linne-deep)]",
  bokad: "text-tallgron bg-[var(--tallgron-soft)]",
  critical: "text-larmrod bg-[var(--larmrod-soft)]",
  warning: "text-signaloranje bg-[var(--signaloranje-soft)]",
  success: "text-tallgron bg-[var(--tallgron-soft)]",
  accent: "text-signaloranje bg-[var(--signaloranje-soft)]",
};

export function Badge({
  className,
  variant = "neutral",
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center justify-center rounded-pill font-mono font-medium uppercase",
        "h-[22px] px-2 text-[11px] tracking-[0.06em]",
        VARIANTS[variant],
        className,
      )}
      {...props}
    />
  );
}

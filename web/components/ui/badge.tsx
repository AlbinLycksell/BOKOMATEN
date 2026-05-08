import { type HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type Variant = "neutral" | "accent" | "critical" | "warning" | "success" | "info";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: Variant;
}

const VARIANTS: Record<Variant, string> = {
  neutral: "bg-surface-2 text-text-muted border-border",
  accent: "bg-accent-soft text-accent border-accent-soft",
  critical: "bg-critical-soft text-critical border-critical-soft",
  warning: "bg-warning-soft text-warning border-warning-soft",
  success: "bg-success-soft text-success border-success-soft",
  info: "bg-info-soft text-info border-info-soft",
};

export function Badge({
  className,
  variant = "neutral",
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium",
        VARIANTS[variant],
        className,
      )}
      {...props}
    />
  );
}

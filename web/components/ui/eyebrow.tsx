import { type HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

/**
 * Mono uppercase eyebrow label — Verkstad signature.
 * Used above headlines, on stat panels, in transcript labels.
 */
export function Eyebrow({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "font-mono uppercase text-text-muted",
        "text-[12px] tracking-[0.08em] leading-[1.4]",
        "v-tnum",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

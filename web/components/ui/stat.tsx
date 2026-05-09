import { type ReactNode } from "react";

import { cn } from "@/lib/utils";
import { Eyebrow } from "./eyebrow";

interface StatProps {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  positive?: boolean;
  className?: string;
}

export function Stat({ label, value, hint, positive, className }: StatProps) {
  return (
    <div
      className={cn(
        "p-5 border-b border-border last:border-b-0",
        "lg:border-b-0 lg:border-r lg:last:border-r-0",
        className,
      )}
    >
      <Eyebrow className="mb-2">{label}</Eyebrow>
      <div className="font-display font-semibold text-[40px] leading-none tracking-[-0.02em] text-text-strong v-tnum">
        {value}
      </div>
      {hint ? (
        <div
          className={cn(
            "mt-2 text-sm",
            positive ? "text-tallgron" : "text-text-muted",
          )}
        >
          {hint}
        </div>
      ) : null}
    </div>
  );
}

export function StatGrid({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 lg:grid-cols-4",
        "rounded-[14px] border border-border bg-surface overflow-hidden",
        className,
      )}
    >
      {children}
    </div>
  );
}

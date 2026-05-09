import { type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Eyebrow } from "@/components/ui/eyebrow";
import { cn } from "@/lib/utils";

interface PriceCardProps {
  name: string;
  price: ReactNode;
  period?: string;
  description: string;
  features: string[];
  cta?: string;
  featured?: boolean;
}

export function PriceCard({
  name,
  price,
  period = "/ mån",
  description,
  features,
  cta = "Kom igång",
  featured = false,
}: PriceCardProps) {
  return (
    <div
      className={cn(
        "relative rounded-[14px] border p-7 flex flex-col",
        featured
          ? "bg-havsbla border-havsbla text-linne"
          : "bg-surface border-border text-text",
      )}
    >
      {featured ? (
        <div className="absolute -top-3 left-6 bg-signaloranje text-white font-mono text-[11px] uppercase tracking-[0.08em] px-2.5 py-1 rounded-pill">
          Vanligast
        </div>
      ) : null}

      <Eyebrow
        className={cn(
          "mb-3.5",
          featured ? "text-linne/70" : "text-text-muted",
        )}
      >
        {name}
      </Eyebrow>

      <div className="flex items-baseline gap-1.5">
        <span className="font-display font-semibold tracking-[-0.02em] text-[56px] leading-none v-tnum">
          {price}
        </span>
        <span className={cn("text-base", featured ? "text-linne/70" : "text-text-muted")}>
          {period}
        </span>
      </div>

      <p
        className={cn(
          "mt-4 text-[15px] leading-[1.5]",
          featured ? "text-linne/85" : "text-text",
        )}
      >
        {description}
      </p>

      <ul className="my-6 grid gap-2.5 list-none p-0 flex-1">
        {features.map((f, i) => (
          <li key={i} className="flex gap-2.5 text-[15px] leading-[1.5]">
            <span
              className={cn(
                "font-mono font-semibold w-4 shrink-0",
                featured ? "text-signaloranje" : "text-tallgron",
              )}
            >
              —
            </span>
            <span>{f}</span>
          </li>
        ))}
      </ul>

      <Button
        variant={featured ? "primary" : "navy"}
        size="md"
        className="w-full"
      >
        {cta}
      </Button>
    </div>
  );
}

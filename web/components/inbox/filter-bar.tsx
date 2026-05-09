"use client";

import { useState } from "react";

import { cn } from "@/lib/utils";
import { InboxFilter } from "@/lib/constants/admin";

const OPTIONS: { value: InboxFilter; label: string }[] = [
  { value: InboxFilter.ALL, label: "Alla" },
  { value: InboxFilter.AKUT, label: "Akuta" },
  { value: InboxFilter.NEEDS_FOLLOWUP, label: "Att följa upp" },
  { value: InboxFilter.HANDLED, label: "Hanterade" },
];

interface FilterBarProps {
  value?: InboxFilter;
  onChange?: (value: InboxFilter) => void;
}

export function FilterBar({ value: controlled, onChange }: FilterBarProps) {
  const [local, setLocal] = useState<InboxFilter>(InboxFilter.ALL);
  const value = controlled ?? local;
  const setValue = (next: InboxFilter) => {
    setLocal(next);
    onChange?.(next);
  };
  return (
    <div className="flex flex-wrap items-center gap-2 px-8 lg:px-12 py-4 bg-linne border-b border-border">
      {OPTIONS.map((opt) => {
        const active = value === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => setValue(opt.value)}
            className={cn(
              "rounded-pill h-9 px-4 text-sm transition-colors border",
              "duration-[120ms] ease-[cubic-bezier(0.2,0,0,1)]",
              active
                ? "bg-havsbla text-linne border-havsbla"
                : "bg-transparent text-text-muted border-border-strong/60 hover:bg-linne-deep hover:text-text",
            )}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

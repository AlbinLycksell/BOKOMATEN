"use client";

import { useState } from "react";

import { cn } from "@/lib/utils";

export type Filter = "all" | "akut" | "offert" | "bokning" | "handled";

const OPTIONS: { value: Filter; label: string }[] = [
  { value: "all", label: "Alla" },
  { value: "akut", label: "Akut" },
  { value: "offert", label: "Offert" },
  { value: "bokning", label: "Bokning" },
  { value: "handled", label: "Hanterade" },
];

interface FilterBarProps {
  value?: Filter;
  onChange?: (value: Filter) => void;
}

export function FilterBar({ value: controlled, onChange }: FilterBarProps) {
  const [local, setLocal] = useState<Filter>("all");
  const value = controlled ?? local;
  const setValue = (next: Filter) => {
    setLocal(next);
    onChange?.(next);
  };
  return (
    <div className="flex flex-wrap items-center gap-2 px-5 py-3 border-b border-border bg-surface">
      {OPTIONS.map((opt) => (
        <button
          key={opt.value}
          type="button"
          onClick={() => setValue(opt.value)}
          className={cn(
            "rounded-pill h-8 px-4 text-sm transition-colors border",
            value === opt.value
              ? "bg-accent-soft text-accent border-accent-soft"
              : "bg-transparent text-text-muted border-border hover:bg-surface-2 hover:text-text",
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

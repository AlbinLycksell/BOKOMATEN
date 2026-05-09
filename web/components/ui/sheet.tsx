"use client";

import { type ReactNode, useEffect } from "react";

import { cn } from "@/lib/utils";

interface SheetProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  side?: "right" | "bottom";
  width?: number;
  ariaLabel?: string;
}

export function Sheet({
  open,
  onClose,
  children,
  side = "right",
  width = 560,
  ariaLabel,
}: SheetProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={ariaLabel}
      className="fixed inset-0 z-50 flex v-scrim"
      onClick={onClose}
      style={{
        animation: "v-fade-in 120ms cubic-bezier(0.2, 0, 0, 1)",
        justifyContent: side === "right" ? "flex-end" : "stretch",
        alignItems: side === "bottom" ? "flex-end" : "stretch",
      }}
    >
      <aside
        className={cn(
          "bg-bg overflow-y-auto",
          side === "right" ? "h-full" : "w-full",
        )}
        style={{
          width: side === "right" ? `min(${width}px, 100%)` : "100%",
          animation: "v-slide-in-right 240ms cubic-bezier(0.2, 0, 0, 1)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </aside>
    </div>
  );
}

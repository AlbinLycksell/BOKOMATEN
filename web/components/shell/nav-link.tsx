"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface NavLinkProps {
  href: string;
  label: string;
  icon: ReactNode;
  badge?: string;
}

export function NavLink({ href, label, icon, badge }: NavLinkProps) {
  const pathname = usePathname();
  const isActive = pathname === href || pathname.startsWith(`${href}/`);
  return (
    <Link
      href={href}
      className={cn(
        "group flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
        isActive
          ? "bg-accent-soft text-accent font-medium"
          : "text-text-muted hover:bg-surface-2 hover:text-text",
      )}
    >
      <span className={cn("flex h-4 w-4", isActive ? "text-accent" : "text-text-muted")}>
        {icon}
      </span>
      <span className="flex-1">{label}</span>
      {badge ? (
        <span
          className={cn(
            "rounded-full px-1.5 py-0.5 text-[10px] font-semibold",
            isActive
              ? "bg-accent text-on-accent"
              : "bg-surface-3 text-text-muted",
          )}
        >
          {badge}
        </span>
      ) : null}
    </Link>
  );
}

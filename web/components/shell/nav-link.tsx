"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface NavLinkProps {
  href: string;
  label: string;
  icon: ReactNode;
}

export function NavLink({ href, label, icon }: NavLinkProps) {
  const pathname = usePathname();
  const isActive = pathname === href || pathname.startsWith(`${href}/`);
  return (
    <Link
      href={href}
      className={cn(
        "group flex items-center gap-2.5 rounded-pill px-3 py-2.5 text-sm transition-colors",
        isActive
          ? "bg-havsbla text-linne font-medium"
          : "text-text hover:bg-linne-deep",
      )}
    >
      <span aria-hidden className="inline-flex items-center justify-center">
        {icon}
      </span>
      <span className="flex-1">{label}</span>
    </Link>
  );
}

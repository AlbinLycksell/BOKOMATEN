import Link from "next/link";

import { Wordmark } from "@/components/brand/wordmark";
import {
  CalendarIcon,
  CustomersIcon,
  InboxIcon,
  PhoneIcon,
  SettingsIcon,
  AdminIcon,
  StarIcon,
} from "@/components/icons";
import { Avatar } from "@/components/ui/avatar";
import { NavLink } from "./nav-link";

interface SidebarProps {
  userName?: string;
  firmaName?: string;
}

export function Sidebar({
  userName = "Lena Andersson",
  firmaName = "Anderssons VVS AB",
}: SidebarProps) {
  return (
    <aside className="hidden md:flex md:w-60 md:flex-col bg-linne border-r border-border h-screen sticky top-0">
      <div className="px-4 pt-6 pb-6">
        <Link href="/inbox" className="inline-flex items-center px-2 py-1">
          <Wordmark size="md" />
        </Link>
      </div>

      <nav className="flex-1 flex flex-col gap-[2px] px-3">
        <NavLink href="/inbox" label="Briefing" icon={<InboxIcon className="h-[18px] w-[18px]" />} />
        <NavLink href="/calls" label="Samtal" icon={<PhoneIcon className="h-[18px] w-[18px]" />} />
        <NavLink href="/bookings" label="Kalender" icon={<CalendarIcon className="h-[18px] w-[18px]" />} />
        <NavLink href="/customers" label="Kunder" icon={<CustomersIcon className="h-[18px] w-[18px]" />} />
        <NavLink href="/admin" label="Jourtekniker" icon={<StarIcon className="h-[18px] w-[18px]" />} />
      </nav>

      <div className="border-t border-border mx-3 mt-3 pt-3 pb-4 px-1">
        <NavLink
          href="/settings"
          label="Inställningar"
          icon={<SettingsIcon className="h-[18px] w-[18px]" />}
        />
        <NavLink
          href="/admin"
          label="Admin & test"
          icon={<AdminIcon className="h-[18px] w-[18px]" />}
        />
        <div className="flex items-center gap-3 px-3 py-2.5 mt-1">
          <Avatar name={userName} size="sm" />
          <div className="min-w-0 leading-tight">
            <div className="text-[13px] font-medium text-text-strong truncate">
              {userName}
            </div>
            <div className="text-xs text-text-muted truncate">{firmaName}</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

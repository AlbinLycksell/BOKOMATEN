import {
  AdminIcon,
  CalendarIcon,
  CustomersIcon,
  InboxIcon,
  SettingsIcon,
} from "@/components/icons";
import { NavLink } from "./nav-link";

export function Sidebar() {
  return (
    <aside className="hidden md:flex md:w-60 md:flex-col border-r border-border bg-surface">
      <div className="flex items-center gap-2 px-5 py-5 border-b border-border">
        <div className="h-8 w-8 rounded-md bg-accent text-on-accent grid place-items-center font-semibold">
          S
        </div>
        <div className="flex flex-col leading-tight">
          <span className="text-sm font-semibold text-text-strong">Switchboard</span>
          <span className="text-[11px] text-text-muted">Anderssons VVS AB</span>
        </div>
      </div>

      <nav className="flex-1 flex flex-col gap-1 px-3 py-4">
        <NavLink href="/inbox" label="Inkorg" icon={<InboxIcon className="h-4 w-4" />} />
        <NavLink href="/bookings" label="Bokningar" icon={<CalendarIcon className="h-4 w-4" />} />
        <NavLink href="/customers" label="Kunder" icon={<CustomersIcon className="h-4 w-4" />} />
        <NavLink href="/admin" label="Admin & Test" icon={<AdminIcon className="h-4 w-4" />} />
        <NavLink href="/settings" label="Inställningar" icon={<SettingsIcon className="h-4 w-4" />} />
      </nav>

      <div className="px-5 py-4 border-t border-border text-[11px] text-text-faint">
        v0.1.0 · MVP
      </div>
    </aside>
  );
}

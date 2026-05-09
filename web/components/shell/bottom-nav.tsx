import {
  CalendarIcon,
  CustomersIcon,
  InboxIcon,
  SettingsIcon,
} from "@/components/icons";
import { NavLink } from "./nav-link";

export function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 flex md:hidden border-t border-border bg-surface">
      <NavLink href="/inbox" label="Inkorg" icon={<InboxIcon className="h-5 w-5" />} mobile />
      <NavLink href="/bookings" label="Bokningar" icon={<CalendarIcon className="h-5 w-5" />} mobile />
      <NavLink href="/customers" label="Kunder" icon={<CustomersIcon className="h-5 w-5" />} mobile />
      <NavLink href="/settings" label="Inställningar" icon={<SettingsIcon className="h-5 w-5" />} mobile />
    </nav>
  );
}

import { Sidebar } from "@/components/shell/sidebar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 flex flex-col">{children}</main>
    </div>
  );
}

import { Avatar } from "@/components/ui/avatar";

interface TopbarProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}

export function Topbar({ title, description, actions }: TopbarProps) {
  return (
    <header className="border-b border-border bg-surface">
      <div className="flex items-center justify-between gap-4 px-6 py-5">
        <div className="flex flex-col gap-1">
          <h1 className="text-lg font-semibold tracking-tight text-text-strong">{title}</h1>
          {description ? (
            <p className="text-sm text-text-muted">{description}</p>
          ) : null}
        </div>
        <div className="flex items-center gap-3">
          {actions}
          <Avatar name="Magnus Andersson" />
        </div>
      </div>
    </header>
  );
}

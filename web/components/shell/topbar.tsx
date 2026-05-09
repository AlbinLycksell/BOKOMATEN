interface TopbarProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}

export function Topbar({ title, description, actions }: TopbarProps) {
  return (
    <header className="bg-linne border-b border-border">
      <div className="flex items-end justify-between gap-6 px-8 lg:px-12 py-8">
        <div className="flex flex-col gap-2 min-w-0">
          <h1 className="font-display text-[32px] leading-[1.05] tracking-[-0.015em] font-semibold text-text-strong">
            {title}
          </h1>
          {description ? (
            <p className="text-[15px] text-text-muted">{description}</p>
          ) : null}
        </div>
        {actions ? (
          <div className="flex items-center gap-2 shrink-0">{actions}</div>
        ) : null}
      </div>
    </header>
  );
}

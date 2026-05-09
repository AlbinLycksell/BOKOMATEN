import { type ReactNode } from "react";

import { Eyebrow } from "@/components/ui/eyebrow";

interface BriefingHeaderProps {
  greeting: string;
  eyebrow: string;
  body?: ReactNode;
  actions?: ReactNode;
}

export function BriefingHeader({
  greeting,
  eyebrow,
  body,
  actions,
}: BriefingHeaderProps) {
  return (
    <header className="bg-linne border-b border-border">
      <div className="flex items-end justify-between gap-6 px-8 lg:px-12 py-12">
        <div className="flex flex-col min-w-0">
          <Eyebrow className="mb-3">{eyebrow}</Eyebrow>
          <h1 className="font-display text-[44px] lg:text-[56px] leading-[1.02] tracking-[-0.02em] font-semibold text-text-strong">
            {greeting}
          </h1>
          {body ? (
            <p className="mt-3 text-[17px] leading-[1.5] text-text max-w-[60ch]">
              {body}
            </p>
          ) : null}
        </div>
        {actions ? (
          <div className="flex items-center gap-2 shrink-0 pb-1">{actions}</div>
        ) : null}
      </div>
    </header>
  );
}

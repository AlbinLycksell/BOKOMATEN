import { type SelectHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/utils";

export const Select = forwardRef<
  HTMLSelectElement,
  SelectHTMLAttributes<HTMLSelectElement>
>(({ className, children, ...props }, ref) => (
  <select
    ref={ref}
    suppressHydrationWarning
    className={cn(
      "h-10 w-full rounded-md border border-border bg-surface px-3 text-sm text-text",
      "focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent",
      className,
    )}
    {...props}
  >
    {children}
  </select>
));
Select.displayName = "Select";

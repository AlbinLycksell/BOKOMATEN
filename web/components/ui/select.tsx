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
      "h-12 w-full rounded-[10px] border border-border-strong bg-white px-4 text-base text-text",
      "focus:outline-none focus:border-havsbla",
      "disabled:opacity-50",
      className,
    )}
    {...props}
  >
    {children}
  </select>
));
Select.displayName = "Select";

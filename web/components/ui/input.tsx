import { type InputHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/utils";

export const Input = forwardRef<
  HTMLInputElement,
  InputHTMLAttributes<HTMLInputElement>
>(({ className, type = "text", ...props }, ref) => (
  <input
    ref={ref}
    type={type}
    suppressHydrationWarning
    className={cn(
      "h-10 w-full rounded-md border border-border bg-surface px-3 text-sm text-text",
      "placeholder:text-text-faint",
      "focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent",
      "disabled:opacity-50",
      className,
    )}
    {...props}
  />
));
Input.displayName = "Input";

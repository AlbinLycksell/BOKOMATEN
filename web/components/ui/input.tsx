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
      "h-12 w-full rounded-[10px] border border-border-strong bg-white px-4 text-base text-text",
      "placeholder:text-text-faint v-tnum",
      "focus:outline-none focus:border-havsbla",
      "disabled:opacity-50",
      className,
    )}
    {...props}
  />
));
Input.displayName = "Input";

import { type TextareaHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/utils";

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    suppressHydrationWarning
    className={cn(
      "min-h-28 w-full rounded-[10px] border border-border-strong bg-white px-4 py-3 text-base text-text",
      "placeholder:text-text-faint",
      "focus:outline-none focus:border-havsbla",
      className,
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";

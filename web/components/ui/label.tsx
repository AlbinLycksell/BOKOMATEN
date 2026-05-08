import { type LabelHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/utils";

export const Label = forwardRef<HTMLLabelElement, LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...props }, ref) => (
    <label
      ref={ref}
      className={cn("text-xs font-medium uppercase tracking-wide text-text-muted", className)}
      {...props}
    />
  ),
);
Label.displayName = "Label";

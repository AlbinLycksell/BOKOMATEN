import { type ButtonHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/utils";

type Variant = "default" | "outline" | "ghost" | "critical" | "subtle";
type Size = "sm" | "md" | "lg" | "icon";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

const VARIANTS: Record<Variant, string> = {
  default:
    "bg-accent text-on-accent hover:bg-accent-hover border border-accent disabled:opacity-50",
  outline:
    "bg-surface text-text border border-border-strong hover:bg-surface-2 disabled:opacity-50",
  ghost:
    "bg-transparent text-text hover:bg-surface-2 border border-transparent disabled:opacity-50",
  subtle:
    "bg-accent-soft text-accent hover:bg-accent-soft-hover border border-transparent disabled:opacity-50",
  critical:
    "bg-critical text-white hover:opacity-90 border border-critical disabled:opacity-50",
};

const SIZES: Record<Size, string> = {
  sm: "h-8 px-3 text-sm",
  md: "h-10 px-4 text-sm",
  lg: "h-11 px-6 text-base",
  icon: "h-9 w-9 p-0",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "md", type = "button", ...props }, ref) => (
    <button
      ref={ref}
      type={type}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-1",
        "disabled:pointer-events-none",
        VARIANTS[variant],
        SIZES[size],
        className,
      )}
      {...props}
    />
  ),
);
Button.displayName = "Button";

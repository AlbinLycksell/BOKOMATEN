import { type ButtonHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/utils";

type Variant =
  | "primary"
  | "navy"
  | "secondary"
  | "ghost"
  | "critical"
  /** Legacy aliases — map onto Verkstad variants. Keep callers compiling. */
  | "default"
  | "outline"
  | "subtle";
type Size = "sm" | "md" | "lg" | "icon";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

const VARIANTS: Record<Variant, string> = {
  primary:
    "bg-signaloranje text-white border-signaloranje hover:bg-signaloranje-press hover:border-signaloranje-press",
  navy:
    "bg-havsbla text-linne border-havsbla hover:bg-havsbla-85 hover:border-havsbla-85",
  secondary:
    "bg-transparent text-havsbla border-havsbla hover:bg-havsbla hover:text-linne",
  ghost:
    "bg-transparent text-havsbla border-transparent hover:bg-linne-deep",
  critical:
    "bg-larmrod text-white border-larmrod hover:opacity-90",
  default:
    "bg-signaloranje text-white border-signaloranje hover:bg-signaloranje-press hover:border-signaloranje-press",
  outline:
    "bg-transparent text-havsbla border-havsbla hover:bg-havsbla hover:text-linne",
  subtle:
    "bg-linne-deep text-havsbla border-transparent hover:bg-grey-100",
};

const SIZES: Record<Size, string> = {
  sm: "h-9 px-4 text-sm gap-1.5",
  md: "h-12 px-6 text-base gap-2",
  lg: "h-14 px-8 text-lg gap-2",
  icon: "h-10 w-10 p-0",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    { className, variant = "primary", size = "md", type = "button", ...props },
    ref,
  ) => (
    <button
      ref={ref}
      type={type}
      className={cn(
        "inline-flex items-center justify-center rounded-pill border font-medium",
        "transition-[background,border-color,color] duration-[120ms] ease-[cubic-bezier(0.2,0,0,1)]",
        "disabled:pointer-events-none disabled:opacity-50",
        "select-none cursor-pointer",
        VARIANTS[variant],
        SIZES[size],
        className,
      )}
      {...props}
    />
  ),
);
Button.displayName = "Button";

/**
 * Backwards-compat alias for legacy `variant="default"` etc. callers.
 * Prefer the explicit Verkstad variants going forward.
 */
export type ButtonVariant = Variant;

import { cn } from "@/lib/utils";

interface AvatarProps {
  name: string;
  className?: string;
  size?: "sm" | "md" | "lg";
}

const SIZES = {
  sm: "h-7 w-7 text-xs",
  md: "h-9 w-9 text-sm",
  lg: "h-12 w-12 text-base",
};

export function Avatar({ name, className, size = "md" }: AvatarProps) {
  const initials = name
    .split(" ")
    .map((part) => part[0]?.toUpperCase() ?? "")
    .filter(Boolean)
    .slice(0, 2)
    .join("");
  return (
    <span
      aria-hidden
      className={cn(
        "inline-grid place-items-center rounded-full bg-havsbla text-linne font-display font-medium",
        SIZES[size],
        className,
      )}
    >
      {initials || "·"}
    </span>
  );
}

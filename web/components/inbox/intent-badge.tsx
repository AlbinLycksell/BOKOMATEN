import { Badge } from "@/components/ui/badge";
import type { Intent as IntentType } from "@/lib/api-models";
import { Intent } from "@/lib/constants/enums";

const LABEL: Record<IntentType, string> = {
  [Intent.AKUT]: "Akut",
  [Intent.OFFERT]: "Offert",
  [Intent.BOKNING]: "Bokad",
  [Intent.BEFINTLIG_KUND]: "Kundfråga",
  [Intent.OVRIGT]: "Info",
};

const VARIANT: Record<
  IntentType,
  "akut" | "info" | "bokad" | "neutral"
> = {
  [Intent.AKUT]: "akut",
  [Intent.OFFERT]: "info",
  [Intent.BOKNING]: "bokad",
  [Intent.BEFINTLIG_KUND]: "neutral",
  [Intent.OVRIGT]: "info",
};

export function IntentBadge({ intent }: { intent: IntentType | null }) {
  if (!intent) return <Badge variant="neutral">—</Badge>;
  return <Badge variant={VARIANT[intent]}>{LABEL[intent]}</Badge>;
}

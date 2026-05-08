import { Badge } from "@/components/ui/badge";
import type { Intent } from "@/lib/api-types";

const LABEL: Record<Intent, string> = {
  akut: "Akut",
  offertforfragan: "Offert",
  bokning: "Bokning",
  befintlig_kund_fraga: "Kundfråga",
  ovrigt: "Övrigt",
};

const VARIANT: Record<Intent, "critical" | "info" | "accent" | "neutral" | "success"> = {
  akut: "critical",
  offertforfragan: "info",
  bokning: "accent",
  befintlig_kund_fraga: "neutral",
  ovrigt: "neutral",
};

export function IntentBadge({ intent }: { intent: Intent | null }) {
  if (!intent) return <Badge variant="neutral">—</Badge>;
  return <Badge variant={VARIANT[intent]}>{LABEL[intent]}</Badge>;
}

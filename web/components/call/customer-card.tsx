import { Card, CardContent } from "@/components/ui/card";
import { Avatar } from "@/components/ui/avatar";
import { Eyebrow } from "@/components/ui/eyebrow";
import { formatPhoneSv } from "@/lib/format";

interface CustomerCardProps {
  name: string | null;
  phone: string | null;
  email?: string | null;
  notesSummary?: string | null;
}

export function CustomerCard({ name, phone, email, notesSummary }: CustomerCardProps) {
  return (
    <Card>
      <CardContent className="px-6 py-6">
        <Eyebrow className="mb-4">Kund</Eyebrow>
        <div className="flex items-center gap-3">
          <Avatar name={name ?? "?"} size="lg" />
          <div className="min-w-0">
            <div className="font-display text-[18px] font-medium tracking-[-0.005em] text-text-strong truncate">
              {name ?? "Okänd ringare"}
            </div>
            {phone ? (
              <div className="text-sm text-text-muted v-tnum">
                {formatPhoneSv(phone)}
              </div>
            ) : null}
            {email ? (
              <div className="text-sm text-text-muted">{email}</div>
            ) : null}
          </div>
        </div>
        {notesSummary ? (
          <p className="mt-5 text-[15px] leading-relaxed text-text">{notesSummary}</p>
        ) : null}
      </CardContent>
    </Card>
  );
}

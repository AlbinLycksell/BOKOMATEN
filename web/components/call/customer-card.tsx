import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar } from "@/components/ui/avatar";
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
      <CardHeader>
        <CardTitle>Kund</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-3">
          <Avatar name={name ?? "?"} className="h-10 w-10 text-sm" />
          <div className="min-w-0">
            <div className="text-sm font-medium text-text-strong truncate">
              {name ?? "Okänd ringare"}
            </div>
            {phone ? (
              <div className="text-xs text-text-muted">{formatPhoneSv(phone)}</div>
            ) : null}
            {email ? (
              <div className="text-xs text-text-muted">{email}</div>
            ) : null}
          </div>
        </div>
        {notesSummary ? (
          <p className="mt-4 text-sm text-text-muted leading-relaxed">{notesSummary}</p>
        ) : null}
      </CardContent>
    </Card>
  );
}

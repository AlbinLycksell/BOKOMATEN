import { Topbar } from "@/components/shell/topbar";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { listCustomers } from "@/lib/api";
import { CustomerType } from "@/lib/constants/enums";
import { formatPhoneSv } from "@/lib/format";
import type { CustomerRead } from "@/lib/api-models";

export const dynamic = "force-dynamic";

export default async function CustomersPage() {
  let customers: CustomerRead[];
  try {
    customers = await listCustomers();
  } catch {
    customers = [];
  }
  return (
    <>
      <Topbar
        title="Kunder"
        description={`${customers.length} kund${customers.length === 1 ? "" : "er"} i firmans register`}
      />
      <div className="flex-1 overflow-y-auto bg-linne">
        <div className="mx-auto max-w-4xl px-8 lg:px-12 py-10 grid gap-3">
          {customers.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center px-6">
                <p className="font-display text-[18px] text-text-strong">
                  Inga kunder ännu.
                </p>
                <p className="mt-2 text-sm text-text-muted">
                  De dyker upp här när AI:n hittar dem i samtal.
                </p>
              </CardContent>
            </Card>
          ) : (
            customers.map((c) => (
              <Card key={c.id}>
                <CardContent className="flex items-center gap-4 px-6 py-5">
                  <Avatar name={c.name} size="md" />
                  <div className="min-w-0 flex-1">
                    <div className="font-display text-[16px] font-medium tracking-[-0.005em] text-text-strong truncate">
                      {c.name}
                    </div>
                    <div className="text-sm text-text-muted v-tnum">
                      {formatPhoneSv(c.phone)}
                      {c.org_number ? ` · org ${c.org_number}` : ""}
                    </div>
                    {c.notes_summary ? (
                      <p className="mt-1 text-sm text-text-muted truncate">
                        {c.notes_summary}
                      </p>
                    ) : null}
                  </div>
                  <Badge variant="neutral">
                    {c.type === CustomerType.COMPANY ? "Företag" : "Privat"}
                  </Badge>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </>
  );
}

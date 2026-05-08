import { Topbar } from "@/components/shell/topbar";
import { Card, CardContent } from "@/components/ui/card";
import { listCustomers } from "@/lib/api";
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
        description={`${customers.length} kund${customers.length === 1 ? "" : "er"} i databasen`}
      />
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-4xl px-6 py-6 grid gap-3">
          {customers.length === 0 ? (
            <Card>
              <CardContent>
                <p className="py-8 text-center text-sm text-text-muted">
                  Inga kunder ännu.
                </p>
              </CardContent>
            </Card>
          ) : (
            customers.map((c) => (
              <Card key={c.id}>
                <CardContent className="flex items-center justify-between gap-4 py-4">
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-text-strong truncate">
                      {c.name}
                    </div>
                    <div className="text-xs text-text-muted">
                      {formatPhoneSv(c.phone)}
                      {c.org_number ? ` · org ${c.org_number}` : ""}
                    </div>
                    {c.notes_summary ? (
                      <p className="mt-1 text-xs text-text-muted truncate">
                        {c.notes_summary}
                      </p>
                    ) : null}
                  </div>
                  <span className="text-xs text-text-faint capitalize">
                    {c.type === "company" ? "Företag" : "Privat"}
                  </span>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </>
  );
}

import { Topbar } from "@/components/shell/topbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CallSimulator } from "@/components/admin/call-simulator";

export default function AdminPage() {
  return (
    <>
      <Topbar title="Admin & Test" description="Verktyg för test och felsökning" />
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-2xl px-6 py-6 flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Samtalsimulator</CardTitle>
            </CardHeader>
            <CardContent>
              <CallSimulator />
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}

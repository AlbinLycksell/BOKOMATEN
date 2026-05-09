import { Topbar } from "@/components/shell/topbar";
import { InboxClient } from "@/components/inbox/inbox-client";
import { listCalls } from "@/lib/api";
import type { CallRead } from "@/lib/api-models";

export const dynamic = "force-dynamic";

async function loadCalls(): Promise<CallRead[]> {
  try {
    return await listCalls({ limit: 100 });
  } catch {
    return [];
  }
}

export default async function InboxPage() {
  const calls = await loadCalls();
  return (
    <>
      <Topbar
        title="Inkorg"
        description={`${calls.length} samtal — uppdateras live`}
      />
      <InboxClient initialData={calls} />
    </>
  );
}

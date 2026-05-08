import { Topbar } from "@/components/shell/topbar";
import { CallRow } from "@/components/inbox/call-row";
import { FilterBar } from "@/components/inbox/filter-bar";
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
        description={`${calls.length} samtal — uppdaterad just nu`}
      />
      <FilterBar />
      <div className="flex-1 overflow-y-auto bg-bg">
        <div className="mx-auto max-w-4xl border-x border-border bg-surface">
          {calls.length === 0 ? (
            <EmptyState />
          ) : (
            calls.map((c) => <CallRow key={c.id} call={c} />)
          )}
        </div>
      </div>
    </>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
      <div className="text-4xl">📭</div>
      <h2 className="mt-4 text-base font-medium text-text-strong">Inga samtal ännu</h2>
      <p className="mt-1 max-w-sm text-sm text-text-muted">
        Backend-API:t kunde inte nås, eller så har inga samtal kommit in idag.
        Starta backend med <code className="rounded bg-surface-2 px-1">uv run uvicorn svarsa.app:create_app --factory --reload --port 8000</code>.
      </p>
    </div>
  );
}

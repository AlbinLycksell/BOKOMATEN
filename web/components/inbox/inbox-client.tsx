"use client";

import { useState } from "react";

import { FilterBar, type Filter } from "./filter-bar";
import { LiveInbox } from "./live-inbox";
import type { CallRead, Intent } from "@/lib/api-models";

interface InboxClientProps {
  initialData: CallRead[];
}

function filterToParams(f: Filter): { intent?: Intent; status?: string } {
  if (f === "akut") return { intent: "akut" as Intent };
  if (f === "offert") return { intent: "offertforfragan" as Intent };
  if (f === "bokning") return { intent: "bokning" as Intent };
  if (f === "handled") return { status: "handled" };
  return {};
}

export function InboxClient({ initialData }: InboxClientProps) {
  const [filter, setFilter] = useState<Filter>("all");
  const params = filterToParams(filter);
  return (
    <>
      <FilterBar value={filter} onChange={setFilter} />
      <LiveInbox initialData={initialData} intent={params.intent} status={params.status} />
    </>
  );
}

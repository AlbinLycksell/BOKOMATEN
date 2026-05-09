"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { adminApi, type AuditEntry } from "@/lib/admin-api";
import { formatTimeAgoSv } from "@/lib/format";

export function AuditLogViewer() {
  const [rows, setRows] = useState<AuditEntry[]>([]);
  const [actionPrefix, setActionPrefix] = useState("");
  const [hours, setHours] = useState(24);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await adminApi.auditLog({
        actionPrefix: actionPrefix || undefined,
        hours,
        limit: 200,
      });
      setRows(data);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Audit log</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4">
        <div className="grid gap-3 md:grid-cols-3 items-end">
          <div className="grid gap-1.5">
            <Label htmlFor="audit-prefix">Filtrera på action-prefix</Label>
            <Input
              id="audit-prefix"
              placeholder="t.ex. scenario."
              value={actionPrefix}
              onChange={(e) => setActionPrefix(e.target.value)}
            />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="audit-hours">Tidsfönster (timmar)</Label>
            <Input
              id="audit-hours"
              type="number"
              min={1}
              max={720}
              value={hours}
              onChange={(e) => setHours(Number(e.target.value))}
            />
          </div>
          <Button variant="outline" onClick={() => void load()} disabled={loading}>
            {loading ? "Laddar…" : "Sök"}
          </Button>
        </div>

        {error ? <p className="text-sm text-critical">{error}</p> : null}

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-text-muted border-b border-border">
                <th className="py-2 pr-2">När</th>
                <th className="py-2 pr-2">Aktör</th>
                <th className="py-2 pr-2">Action</th>
                <th className="py-2 pr-2">Mål</th>
                <th className="py-2">Payload</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-text-muted">
                    Inga rader i fönstret
                  </td>
                </tr>
              ) : (
                rows.map((r) => (
                  <tr key={r.id} className="border-b border-border last:border-b-0">
                    <td className="py-2 pr-2 text-text-muted whitespace-nowrap">
                      {formatTimeAgoSv(r.created_at)}
                    </td>
                    <td className="py-2 pr-2">
                      <Badge variant="neutral">{r.actor}</Badge>
                    </td>
                    <td className="py-2 pr-2 font-mono text-xs">{r.action}</td>
                    <td className="py-2 pr-2 text-text-muted text-xs">
                      {r.target_type}
                      {r.target_id ? `:${r.target_id.slice(-8)}` : ""}
                    </td>
                    <td className="py-2 text-xs text-text-muted">
                      <code className="font-mono">
                        {Object.keys(r.payload).length === 0
                          ? "—"
                          : JSON.stringify(r.payload).slice(0, 80) +
                            (JSON.stringify(r.payload).length > 80 ? "…" : "")}
                      </code>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

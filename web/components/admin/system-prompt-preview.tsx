"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { adminApi } from "@/lib/admin-api";

export function SystemPromptPreview() {
  const [text, setText] = useState<string>("");
  const [chars, setChars] = useState<number>(0);
  const [tokens, setTokens] = useState<number>(0);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const r = await adminApi.systemPrompt();
      setText(r.text);
      setChars(r.length_chars);
      setTokens(r.estimated_tokens);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>System prompt (live för din firma)</CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="neutral">{chars.toLocaleString("sv-SE")} tecken</Badge>
            <Badge variant="neutral">~{tokens.toLocaleString("sv-SE")} tokens</Badge>
            <Button size="sm" variant="outline" onClick={() => void load()} disabled={loading}>
              Ladda om
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <pre className="rounded-md border border-border bg-surface-2 p-4 max-h-[60vh] overflow-auto text-xs font-mono whitespace-pre-wrap leading-relaxed">
          {loading ? "Laddar…" : text}
        </pre>
        <p className="mt-3 text-xs text-text-muted">
          Detta är vad Gemini Live ser vid varje sessionsstart för Anderssons VVS AB.
          Persona-rättningar (från Träna AI-flödet) bakas in automatiskt.
        </p>
      </CardContent>
    </Card>
  );
}

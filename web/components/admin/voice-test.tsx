"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const FIRMA_ID = "01J0000FIRM0ANDERSSONSVVS00";
const PLAYBACK_RATE = 24_000; // matches Gemini Live audio output
const TEST_PHONE = "+46708000000";

type ConnState = "idle" | "requesting_mic" | "connecting" | "live" | "ending" | "ended";

interface Stats {
  framesSent: number;
  framesReceived: number;
  bytesSent: number;
  bytesReceived: number;
  startedAt: number | null;
}

const blankStats: Stats = {
  framesSent: 0,
  framesReceived: 0,
  bytesSent: 0,
  bytesReceived: 0,
  startedAt: null,
};

export function VoiceTest() {
  const [state, setState] = useState<ConnState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [callId, setCallId] = useState<string | null>(null);
  const [stats, setStats] = useState<Stats>(blankStats);
  const [muted, setMuted] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const workletRef = useRef<AudioWorkletNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const playCursorRef = useRef<number>(0);

  const cleanup = () => {
    try {
      wsRef.current?.close();
    } catch {
      /* ignore */
    }
    workletRef.current?.disconnect();
    sourceRef.current?.disconnect();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    void audioCtxRef.current?.close();
    wsRef.current = null;
    workletRef.current = null;
    sourceRef.current = null;
    streamRef.current = null;
    audioCtxRef.current = null;
  };

  useEffect(() => () => cleanup(), []);

  useEffect(() => {
    workletRef.current?.port.postMessage({ enabled: !muted });
  }, [muted]);

  const start = async () => {
    setError(null);
    setStats({ ...blankStats, startedAt: Date.now() });
    setState("requesting_mic");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,
        },
      });
      streamRef.current = stream;
    } catch (e) {
      setError(`Mikrofontillstånd nekat: ${e}`);
      setState("idle");
      return;
    }

    setState("connecting");

    const audioCtx = new AudioContext();
    audioCtxRef.current = audioCtx;
    try {
      await audioCtx.audioWorklet.addModule("/voice-capture-worklet.js");
    } catch (e) {
      setError(`AudioWorklet kunde inte laddas: ${e}`);
      cleanup();
      setState("idle");
      return;
    }

    const source = audioCtx.createMediaStreamSource(streamRef.current!);
    sourceRef.current = source;
    const worklet = new AudioWorkletNode(audioCtx, "voice-capture", {
      processorOptions: { targetRate: 24_000 },
    });
    workletRef.current = worklet;
    playCursorRef.current = audioCtx.currentTime;

    const id = `test-${Date.now().toString(36)}`;
    setCallId(id);

    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const ws = new WebSocket(
      `${proto}//${host}/ws/bridge/${encodeURIComponent(FIRMA_ID)}/${encodeURIComponent(id)}`,
    );
    wsRef.current = ws;
    ws.binaryType = "arraybuffer";

    ws.onopen = () => {
      ws.send(
        JSON.stringify({
          t: "hello",
          callid: id,
          from: TEST_PHONE,
          to: "+46812345678",
        }),
      );
      setState("live");
    };

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(typeof e.data === "string" ? e.data : "{}");
        if (msg.t === "audio" && typeof msg.data === "string") {
          const ab = base64ToArrayBuffer(msg.data);
          schedulePcm24k(audioCtx, ab);
          setStats((s) => ({
            ...s,
            framesReceived: s.framesReceived + 1,
            bytesReceived: s.bytesReceived + ab.byteLength,
          }));
        } else if (msg.t === "bye") {
          cleanup();
          setState("ended");
        }
      } catch {
        /* non-JSON or non-audio frame */
      }
    };

    ws.onerror = () => {
      setError("Bridge-WS fel — kontrollera att backend kör + GEMINI_API_KEY satt");
    };

    ws.onclose = (ev) => {
      if (state !== "ended") {
        setState("ended");
        if (!ev.wasClean) {
          setError(
            `WebSocket stängd (kod ${ev.code}). Vanligaste orsaker: GEMINI_API_KEY saknas, ` +
              `firma okänd, eller backend nere.`,
          );
        }
      }
    };

    worklet.port.onmessage = (ev) => {
      if (ws.readyState !== WebSocket.OPEN) return;
      const ab = ev.data as ArrayBuffer;
      const b64 = arrayBufferToBase64(ab);
      ws.send(JSON.stringify({ t: "audio", data: b64 }));
      setStats((s) => ({
        ...s,
        framesSent: s.framesSent + 1,
        bytesSent: s.bytesSent + ab.byteLength,
      }));
    };

    source.connect(worklet);
    // worklet does not connect to destination — no monitoring/feedback
  };

  const stop = () => {
    setState("ending");
    try {
      wsRef.current?.send(JSON.stringify({ t: "bye" }));
    } catch {
      /* ignore */
    }
    cleanup();
    setState("ended");
  };

  const schedulePcm24k = (ctx: AudioContext, ab: ArrayBuffer) => {
    const int16 = new Int16Array(ab);
    if (int16.length === 0) return;
    const float32 = new Float32Array(int16.length);
    for (let i = 0; i < int16.length; i++) float32[i] = (int16[i] ?? 0) / 0x8000;
    const buffer = ctx.createBuffer(1, float32.length, PLAYBACK_RATE);
    buffer.copyToChannel(float32, 0);
    const node = ctx.createBufferSource();
    node.buffer = buffer;
    node.connect(ctx.destination);
    const startAt = Math.max(ctx.currentTime, playCursorRef.current);
    node.start(startAt);
    playCursorRef.current = startAt + buffer.duration;
  };

  const elapsed =
    stats.startedAt && state === "live"
      ? Math.floor((Date.now() - stats.startedAt) / 1000)
      : 0;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <CardTitle>Röstprov — emulera ett samtal från webbläsaren</CardTitle>
          <StatePill state={state} />
        </div>
      </CardHeader>
      <CardContent className="grid gap-4">
        <p className="text-sm text-text-muted">
          Använder <strong>din mikrofon</strong> som kund-sida och samma
          WebSocket-bridge som 46elks pratar med i produktion. Bryggan kopplar
          mot riktig <strong>Gemini Live</strong> — du behöver
          <code className="mx-1 rounded bg-surface-2 px-1">GEMINI_API_KEY</code>
          (eller Vertex-konfig) satt på backenden för att samtalet ska gå
          igenom. Säg något (t.ex. "Hej, jag har en vattenläcka") så svarar AI:n
          i högtalaren.
        </p>

        <div className="grid gap-3 md:grid-cols-2">
          <div className="grid gap-1.5 rounded-md border border-border bg-surface-2 p-3 text-xs">
            <strong className="text-text-strong text-sm">Förutsättningar</strong>
            <ul className="grid gap-0.5 text-text-muted">
              <li>· Backend kör på samma domän (eller via /api/proxy-rewrite)</li>
              <li>· Mikrofontillstånd från webbläsaren</li>
              <li>· HTTPS eller localhost (getUserMedia-krav)</li>
              <li>· GEMINI_API_KEY eller Vertex-IAM på backend</li>
            </ul>
          </div>
          <div className="grid gap-1.5 rounded-md border border-border bg-surface-2 p-3 text-xs">
            <strong className="text-text-strong text-sm">Vad detta testar</strong>
            <ul className="grid gap-0.5 text-text-muted">
              <li>✓ Bridge-WS &amp; pcm_24000-protokollet</li>
              <li>✓ Audio-uppsampling 48k → 24k → bridge</li>
              <li>✓ Verklig Gemini Live-tur</li>
              <li>✓ Tool-anrop, transkript, post-call-summering</li>
            </ul>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {state === "idle" || state === "ended" ? (
            <Button onClick={() => void start()}>Starta test-samtal</Button>
          ) : (
            <>
              <Button variant="critical" onClick={stop} disabled={state === "ending"}>
                Avsluta samtalet
              </Button>
              <Button
                variant="outline"
                onClick={() => setMuted((m) => !m)}
                disabled={state !== "live"}
              >
                {muted ? "Aktivera mic" : "Tysta mic"}
              </Button>
            </>
          )}
          {state === "live" ? (
            <span className="text-xs text-text-muted ml-auto">{elapsed}s aktivt</span>
          ) : null}
        </div>

        {error ? (
          <p className="text-sm text-critical">{error}</p>
        ) : null}

        {state === "live" || state === "ended" ? (
          <div className="grid gap-2 md:grid-cols-4 text-xs">
            <Stat label="Skickade frames" value={stats.framesSent.toLocaleString("sv-SE")} />
            <Stat label="Mottagna frames" value={stats.framesReceived.toLocaleString("sv-SE")} />
            <Stat label="Skickat" value={`${(stats.bytesSent / 1024).toFixed(1)} KB`} />
            <Stat label="Mottaget" value={`${(stats.bytesReceived / 1024).toFixed(1)} KB`} />
          </div>
        ) : null}

        {callId && state === "ended" ? (
          <div className="rounded-md border border-border bg-surface-2 p-3 text-sm">
            Samtalet sparades som{" "}
            <Link
              href={`/calls/${encodeURIComponent(callId)}`}
              className="text-accent hover:underline"
            >
              {callId}
            </Link>{" "}
            — där hittar du transkriptet, verktygsanropen och AI-summeringen.
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function StatePill({ state }: { state: ConnState }) {
  const map: Record<ConnState, [string, "neutral" | "warning" | "success" | "critical"]> = {
    idle: ["Inaktiv", "neutral"],
    requesting_mic: ["Begär mic…", "warning"],
    connecting: ["Ansluter…", "warning"],
    live: ["LIVE", "success"],
    ending: ["Avslutar…", "warning"],
    ended: ["Avslutat", "neutral"],
  };
  const [label, variant] = map[state];
  return <Badge variant={variant}>{label}</Badge>;
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-surface p-2">
      <div className="text-[11px] uppercase tracking-wide text-text-muted">{label}</div>
      <div className="mt-0.5 font-medium text-text-strong tabular-nums">{value}</div>
    </div>
  );
}

function arrayBufferToBase64(ab: ArrayBuffer): string {
  const bytes = new Uint8Array(ab);
  let bin = "";
  const chunkSize = 0x8000;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    bin += String.fromCharCode(...bytes.subarray(i, i + chunkSize));
  }
  return btoa(bin);
}

function base64ToArrayBuffer(b64: string): ArrayBuffer {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes.buffer;
}

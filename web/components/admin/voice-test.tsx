"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { adminApi } from "@/lib/admin-api";
import { bridgeWsUrl } from "@/lib/backend-url";

const FIRMA_ID = "01J0000FIRM0ANDERSSONSVVS00";
const PLAYBACK_RATE = 24_000; // matches Gemini Live audio output
const TEST_PHONE = "+46708000000";

type ConnState =
  | "idle"
  | "checking"
  | "requesting_mic"
  | "connecting"
  | "live"
  | "ending"
  | "ended";

const REASON_MESSAGES: Record<string, string> = {
  gemini_auth_failed:
    "Gemini avvisade autentiseringen. GEMINI_API_KEY är ogiltig, utgången, eller i fel projekt.",
  gemini_model_unavailable:
    "Gemini-modellen är otillgänglig för det här projektet. Kontrollera SWITCHBOARD_GEMINI_MODEL.",
  gemini_quota_exhausted:
    "Gemini-quota är slut för det här projektet eller minuten. Vänta en stund eller höj rate-limit.",
  gemini_connect_failed:
    "Bryggan kunde inte ansluta till Gemini Live. Vanligtvis nätverk eller GEMINI_API_KEY saknas.",
  unknown_firma: "Okänd firma — bridge fick fel firma_id.",
};

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
  const [providerLabel, setProviderLabel] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const workletRef = useRef<AudioWorkletNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const playCursorRef = useRef<number>(0);
  const userClosingRef = useRef(false);
  const serverReasonRef = useRef<string | null>(null);

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
    userClosingRef.current = false;
    serverReasonRef.current = null;
    setStats({ ...blankStats, startedAt: Date.now() });
    setState("checking");

    // Pre-flight: verify Gemini is configured before opening the WS.
    try {
      const ready = await adminApi.voiceTestReady();
      setProviderLabel(`${ready.provider} · ${ready.model}`);
      if (!ready.ready) {
        setError(
          ready.reason ??
            "Voice test inte konfigurerat på backenden. Sätt GEMINI_API_KEY och starta om.",
        );
        setState("idle");
        return;
      }
    } catch (e) {
      setError(
        `Kunde inte nå backenden för pre-flight: ${e}. Kontrollera att uvicorn kör på port 8000.`,
      );
      setState("idle");
      return;
    }

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

    const url = bridgeWsUrl(FIRMA_ID, id);
    // Visible in the browser console so connection problems are obvious.
    // eslint-disable-next-line no-console
    console.info("[voice-test] opening", url);
    const ws = new WebSocket(url);
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
          // Server-initiated bye carries a reason. Surface it immediately.
          if (typeof msg.reason === "string" && msg.reason) {
            serverReasonRef.current = msg.reason;
            setError(REASON_MESSAGES[msg.reason] ?? `Bridge avslutade: ${msg.reason}`);
          }
        }
      } catch {
        /* non-JSON or non-audio frame */
      }
    };

    ws.onerror = () => {
      // Don't show a generic message here — `onclose` runs right after with
      // more useful info (and any server bye reason already set).
    };

    ws.onclose = (ev) => {
      // User pressed Stop → graceful close, no error.
      if (userClosingRef.current) {
        setState("ended");
        return;
      }
      // Server already told us why via {t:"bye",reason} → keep that error.
      if (serverReasonRef.current) {
        setState("ended");
        return;
      }
      // Otherwise it's an unexpected drop — surface code + best guess.
      setState("ended");
      if (!ev.wasClean) {
        setError(
          `WebSocket föll (kod ${ev.code}). Backenden tappade förbindelsen oväntat — ` +
            `kontrollera uvicorn-loggen.`,
        );
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
    userClosingRef.current = true;
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
              <li className="text-text-faint">— 46elks bypassas helt</li>
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
          {providerLabel ? (
            <Badge variant="neutral" className="ml-auto">
              {providerLabel}
            </Badge>
          ) : null}
        </div>

        {error ? <p className="text-sm text-critical">{error}</p> : null}

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
    checking: ["Pre-flight…", "warning"],
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

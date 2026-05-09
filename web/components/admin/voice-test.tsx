"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { adminApi } from "@/lib/admin-api";
import { bridgeWsUrl } from "@/lib/backend-url";
import { BRIDGE_BYE_MESSAGES_SV, VoiceTestState } from "@/lib/constants/admin";
import { AudioContextState, AudioRate, VoiceCaptureWorklet } from "@/lib/constants/audio";
import { CallSource } from "@/lib/constants/enums";
import { DEMO_FIRMA_ID, TEST_PHONE_E164, TEST_TARGET_PHONE_E164 } from "@/lib/constants/firma";
import {
  BridgeBye,
  BridgeFrameField,
  BridgeQueryParam,
  BridgeWSEvent,
} from "@/lib/constants/ws";
import { TranscriptRole } from "@/lib/constants/enums";

const PLAYBACK_RATE = AudioRate.PCM_24K;
const SUMMARY_HINT_MS = 4_000;
const CAPTION_MERGE_WINDOW_MS = 4_000;
const BASE64_CHUNK_SIZE = 0x8000;
const PCM16_FULL_SCALE = 0x8000;

type ConnState = (typeof VoiceTestState)[keyof typeof VoiceTestState];

type CaptionRole = typeof TranscriptRole.CALLER | typeof TranscriptRole.AI;

interface CaptionLine {
  role: CaptionRole;
  text: string;
  receivedAt: number;
}

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
  const [state, setState] = useState<ConnState>(VoiceTestState.IDLE);
  const [error, setError] = useState<string | null>(null);
  const [callId, setCallId] = useState<string | null>(null);
  const [stats, setStats] = useState<Stats>(blankStats);
  const [muted, setMuted] = useState(false);
  const [providerLabel, setProviderLabel] = useState<string | null>(null);
  const [captions, setCaptions] = useState<CaptionLine[]>([]);
  const [summaryWait, setSummaryWait] = useState(false);

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
    setState(VoiceTestState.CHECKING);

    try {
      const ready = await adminApi.voiceTestReady();
      setProviderLabel(`${ready.provider} · ${ready.model}`);
      if (!ready.ready) {
        setError(
          ready.reason ??
            "Voice test inte konfigurerat på backenden. Sätt GEMINI_API_KEY och starta om.",
        );
        setState(VoiceTestState.IDLE);
        return;
      }
    } catch (e) {
      setError(
        `Kunde inte nå backenden för pre-flight: ${e}. Kontrollera att uvicorn kör på port 8000.`,
      );
      setState(VoiceTestState.IDLE);
      return;
    }

    setState(VoiceTestState.REQUESTING_MIC);

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
      setState(VoiceTestState.IDLE);
      return;
    }

    setState(VoiceTestState.CONNECTING);

    const audioCtx = new AudioContext();
    audioCtxRef.current = audioCtx;
    if (audioCtx.state === AudioContextState.SUSPENDED) {
      await audioCtx.resume();
    }
    try {
      await audioCtx.audioWorklet.addModule(VoiceCaptureWorklet.PATH);
    } catch (e) {
      setError(`AudioWorklet kunde inte laddas: ${e}`);
      cleanup();
      setState(VoiceTestState.IDLE);
      return;
    }

    const source = audioCtx.createMediaStreamSource(streamRef.current!);
    sourceRef.current = source;
    const worklet = new AudioWorkletNode(audioCtx, VoiceCaptureWorklet.PROCESSOR_NAME, {
      processorOptions: { targetRate: AudioRate.PCM_24K },
    });
    workletRef.current = worklet;
    playCursorRef.current = audioCtx.currentTime;

    const id = `test-${Date.now().toString(36)}`;
    setCallId(id);
    setCaptions([]);

    const url =
      bridgeWsUrl(DEMO_FIRMA_ID, id) +
      `?${BridgeQueryParam.SOURCE}=${CallSource.VOICE_TEST}`;
    // eslint-disable-next-line no-console
    console.info("[voice-test] opening", url);
    const ws = new WebSocket(url);
    wsRef.current = ws;
    ws.binaryType = "arraybuffer";

    ws.onopen = () => {
      ws.send(
        JSON.stringify({
          [BridgeFrameField.TYPE]: BridgeWSEvent.HELLO,
          [BridgeFrameField.CALLID]: id,
          [BridgeFrameField.FROM]: TEST_PHONE_E164,
          [BridgeFrameField.TO]: TEST_TARGET_PHONE_E164,
        }),
      );
      setState(VoiceTestState.LIVE);
    };

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(typeof e.data === "string" ? e.data : "{}");
        const t = msg[BridgeFrameField.TYPE];
        if (t === BridgeWSEvent.AUDIO && typeof msg[BridgeFrameField.DATA] === "string") {
          const ab = base64ToArrayBuffer(msg[BridgeFrameField.DATA]);
          schedulePcm24k(audioCtx, ab);
          setStats((s) => ({
            ...s,
            framesReceived: s.framesReceived + 1,
            bytesReceived: s.bytesReceived + ab.byteLength,
          }));
        } else if (
          t === BridgeWSEvent.TRANSCRIPT &&
          typeof msg[BridgeFrameField.TEXT] === "string"
        ) {
          const role: CaptionRole =
            msg[BridgeFrameField.ROLE] === TranscriptRole.CALLER
              ? TranscriptRole.CALLER
              : TranscriptRole.AI;
          const text = String(msg[BridgeFrameField.TEXT]);
          if (text.trim()) {
            setCaptions((c) => mergeCaption(c, role, text));
          }
        } else if (t === BridgeWSEvent.BYE) {
          const reason = msg[BridgeFrameField.REASON];
          if (typeof reason === "string" && reason) {
            serverReasonRef.current = reason;
            setError(
              BRIDGE_BYE_MESSAGES_SV[reason as BridgeBye] ?? `Bridge avslutade: ${reason}`,
            );
          }
        }
      } catch {
        /* non-JSON or non-audio frame */
      }
    };

    ws.onerror = () => {
      /* `onclose` runs right after with more useful info */
    };

    ws.onclose = (ev) => {
      if (userClosingRef.current) {
        setState(VoiceTestState.ENDED);
        return;
      }
      if (serverReasonRef.current) {
        setState(VoiceTestState.ENDED);
        return;
      }
      setState(VoiceTestState.ENDED);
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
      ws.send(
        JSON.stringify({
          [BridgeFrameField.TYPE]: BridgeWSEvent.AUDIO,
          [BridgeFrameField.DATA]: b64,
        }),
      );
      setStats((s) => ({
        ...s,
        framesSent: s.framesSent + 1,
        bytesSent: s.bytesSent + ab.byteLength,
      }));
    };

    source.connect(worklet);
  };

  const stop = () => {
    userClosingRef.current = true;
    setState(VoiceTestState.ENDING);
    try {
      wsRef.current?.send(
        JSON.stringify({ [BridgeFrameField.TYPE]: BridgeWSEvent.BYE }),
      );
    } catch {
      /* ignore */
    }
    cleanup();
    setState(VoiceTestState.ENDED);
    setSummaryWait(true);
    setTimeout(() => setSummaryWait(false), SUMMARY_HINT_MS);
  };

  const schedulePcm24k = (ctx: AudioContext, ab: ArrayBuffer) => {
    if (ctx.state === AudioContextState.SUSPENDED) void ctx.resume();
    const int16 = new Int16Array(ab);
    if (int16.length === 0) return;
    const float32 = new Float32Array(int16.length);
    for (let i = 0; i < int16.length; i++)
      float32[i] = (int16[i] ?? 0) / PCM16_FULL_SCALE;
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
    stats.startedAt && state === VoiceTestState.LIVE
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
          {state === VoiceTestState.IDLE || state === VoiceTestState.ENDED ? (
            <Button onClick={() => void start()}>Starta test-samtal</Button>
          ) : (
            <>
              <Button
                variant="critical"
                onClick={stop}
                disabled={state === VoiceTestState.ENDING}
              >
                Avsluta samtalet
              </Button>
              <Button
                variant="outline"
                onClick={() => setMuted((m) => !m)}
                disabled={state !== VoiceTestState.LIVE}
              >
                {muted ? "Aktivera mic" : "Tysta mic"}
              </Button>
            </>
          )}
          {state === VoiceTestState.LIVE ? (
            <span className="text-xs text-text-muted ml-auto">{elapsed}s aktivt</span>
          ) : null}
          {providerLabel ? (
            <Badge variant="neutral" className="ml-auto">
              {providerLabel}
            </Badge>
          ) : null}
        </div>

        {error ? <p className="text-sm text-critical">{error}</p> : null}

        {state === VoiceTestState.LIVE || state === VoiceTestState.ENDED ? (
          <div className="grid gap-2 md:grid-cols-4 text-xs">
            <Stat label="Skickade frames" value={stats.framesSent.toLocaleString("sv-SE")} />
            <Stat label="Mottagna frames" value={stats.framesReceived.toLocaleString("sv-SE")} />
            <Stat label="Skickat" value={`${(stats.bytesSent / 1024).toFixed(1)} KB`} />
            <Stat label="Mottaget" value={`${(stats.bytesReceived / 1024).toFixed(1)} KB`} />
          </div>
        ) : null}

        {captions.length > 0 ? (
          <div className="rounded-md border border-border bg-surface-2 p-3">
            <div className="text-xs uppercase tracking-wide text-text-muted mb-2">
              Live-transkript
            </div>
            <div className="grid gap-2 max-h-72 overflow-y-auto">
              {captions.map((c, i) => (
                <div key={i} className="flex gap-2 text-sm">
                  <span
                    className={
                      c.role === TranscriptRole.AI
                        ? "font-mono text-[11px] uppercase tracking-[0.04em] text-signaloranje w-16 shrink-0 pt-0.5"
                        : "text-xs uppercase tracking-wide text-text-muted w-16 shrink-0 pt-0.5"
                    }
                  >
                    {c.role === TranscriptRole.AI ? "Switchboard" : "Du"}
                  </span>
                  <span className="text-text">{c.text}</span>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {callId && state === VoiceTestState.ENDED ? (
          <div className="rounded-[10px] border border-border bg-linne-deep p-4 flex items-start justify-between gap-4">
            <div className="text-sm">
              <p className="font-medium text-text-strong">Samtalet är sparat</p>
              <p className="mt-0.5 text-text-muted">
                Transkript, verktygsanrop och AI-summering finns på samtalssidan.
              </p>
              {summaryWait ? (
                <p className="mt-1 text-xs text-text-faint">
                  Sammanfattningen genereras i bakgrunden (~1–3 s)
                </p>
              ) : null}
            </div>
            <Link
              href={`/calls/${encodeURIComponent(callId)}`}
              className="shrink-0"
            >
              <Button variant="outline" size="sm">
                Öppna samtalet →
              </Button>
            </Link>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function StatePill({ state }: { state: ConnState }) {
  const map: Record<ConnState, [string, "neutral" | "warning" | "success" | "critical"]> = {
    [VoiceTestState.IDLE]: ["Inaktiv", "neutral"],
    [VoiceTestState.CHECKING]: ["Pre-flight…", "warning"],
    [VoiceTestState.REQUESTING_MIC]: ["Begär mic…", "warning"],
    [VoiceTestState.CONNECTING]: ["Ansluter…", "warning"],
    [VoiceTestState.LIVE]: ["LIVE", "success"],
    [VoiceTestState.ENDING]: ["Avslutar…", "warning"],
    [VoiceTestState.ENDED]: ["Avslutat", "neutral"],
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

function mergeCaption(
  prev: CaptionLine[],
  role: CaptionRole,
  text: string,
): CaptionLine[] {
  const last = prev[prev.length - 1];
  const now = Date.now();
  if (last && last.role === role && now - last.receivedAt < CAPTION_MERGE_WINDOW_MS) {
    const updated = { ...last, text: `${last.text} ${text}`.trim(), receivedAt: now };
    return [...prev.slice(0, -1), updated];
  }
  return [...prev, { role, text, receivedAt: now }];
}

function arrayBufferToBase64(ab: ArrayBuffer): string {
  const bytes = new Uint8Array(ab);
  let bin = "";
  for (let i = 0; i < bytes.length; i += BASE64_CHUNK_SIZE) {
    bin += String.fromCharCode(...bytes.subarray(i, i + BASE64_CHUNK_SIZE));
  }
  return btoa(bin);
}

function base64ToArrayBuffer(b64: string): ArrayBuffer {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes.buffer;
}

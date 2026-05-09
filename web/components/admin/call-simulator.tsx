"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { PhoneCallIcon, PhoneIcon } from "@/components/icons";

type Status = "idle" | "connecting" | "connected" | "ended";

const FIRMA_ID = "01J0000FIRM0ANDERSSONSVVS00";
const CALLER_PHONE = "+46700000001";

function newCallId(): string {
  // Crockford base32 characters
  const chars = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";
  let id = "";
  for (let i = 0; i < 26; i++) id += chars[Math.floor(Math.random() * 32)];
  return id;
}

function float32ToInt16(float32: Float32Array): Int16Array {
  const int16 = new Int16Array(float32.length);
  for (let i = 0; i < float32.length; i++) {
    int16[i] = Math.max(-32768, Math.min(32767, Math.round(float32[i] * 32767)));
  }
  return int16;
}

function toBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let bin = "";
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin);
}

function fromBase64(b64: string): Int16Array {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new Int16Array(bytes.buffer);
}

export function CallSimulator() {
  const [status, setStatus] = useState<Status>("idle");
  const [log, setLog] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const nextPlayTimeRef = useRef<number>(0);

  const addLog = (msg: string) =>
    setLog((prev) => [...prev.slice(-50), `${new Date().toLocaleTimeString()} ${msg}`]);

  async function startCall() {
    setStatus("connecting");
    setLog([]);

    const callId = newCallId();
    const wsUrl = `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/api/proxy/ws/bridge/${FIRMA_ID}/${callId}`;
    addLog(`Ansluter… ${callId}`);

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    } catch {
      addLog("Mikrofonåtkomst nekad.");
      setStatus("idle");
      return;
    }
    streamRef.current = stream;

    const ctx = new AudioContext({ sampleRate: 24000 });
    audioCtxRef.current = ctx;
    nextPlayTimeRef.current = ctx.currentTime;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ t: "hello", callid: callId, from: CALLER_PHONE, to: "+46000000000" }));
    };

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data as string);
      if (msg.t === "sending" || msg.t === "listening") {
        addLog(`Bridge: ${msg.t} (${msg.format})`);
        if (msg.t === "listening") {
          setStatus("connected");
          addLog("Ansluten — tala nu.");
          startMic(ctx, ws);
        }
      } else if (msg.t === "audio") {
        playChunk(ctx, fromBase64(msg.data as string));
      } else if (msg.t === "interrupt") {
        nextPlayTimeRef.current = ctx.currentTime;
      } else if (msg.t === "bye") {
        addLog("Samtalet avslutades av servern.");
        hangUp();
      } else if (msg.t === "sync") {
        ws.send(JSON.stringify({ t: "sync" }));
      }
    };

    ws.onerror = () => addLog("WebSocket-fel.");
    ws.onclose = (e) => {
      if (status !== "idle") addLog(`Frånkopplad (${e.code}).`);
      cleanup();
    };
  }

  function startMic(ctx: AudioContext, ws: WebSocket) {
    if (!streamRef.current) return;
    const source = ctx.createMediaStreamSource(streamRef.current);
    // eslint-disable-next-line @typescript-eslint/no-deprecated
    const processor = ctx.createScriptProcessor(2048, 1, 1);
    processorRef.current = processor;
    processor.onaudioprocess = (e) => {
      if (ws.readyState !== WebSocket.OPEN) return;
      const int16 = float32ToInt16(e.inputBuffer.getChannelData(0));
      ws.send(JSON.stringify({ t: "audio", data: toBase64(int16.buffer) }));
    };
    source.connect(processor);
    processor.connect(ctx.destination);
  }

  function playChunk(ctx: AudioContext, int16: Int16Array) {
    const float32 = new Float32Array(int16.length);
    for (let i = 0; i < int16.length; i++) float32[i] = int16[i] / 32767;
    const buffer = ctx.createBuffer(1, float32.length, 24000);
    buffer.copyToChannel(float32, 0);
    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(ctx.destination);
    const startAt = Math.max(nextPlayTimeRef.current, ctx.currentTime);
    source.start(startAt);
    nextPlayTimeRef.current = startAt + buffer.duration;
  }

  function cleanup() {
    processorRef.current?.disconnect();
    processorRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    audioCtxRef.current?.close();
    audioCtxRef.current = null;
    setStatus("ended");
  }

  function hangUp() {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ t: "bye", reason: "hangup" }));
      wsRef.current.close();
    }
    cleanup();
    addLog("Samtal avslutat.");
  }

  useEffect(() => () => { hangUp(); }, []);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-3">
        {status === "idle" || status === "ended" ? (
          <Button onClick={startCall} className="flex items-center gap-2">
            <PhoneCallIcon className="h-4 w-4" />
            Starta testsamtal
          </Button>
        ) : (
          <Button onClick={hangUp} variant="destructive" className="flex items-center gap-2">
            <PhoneIcon className="h-4 w-4" />
            Lägg på
          </Button>
        )}
        <span className={`text-sm font-medium ${
          status === "connected" ? "text-green-600" :
          status === "connecting" ? "text-yellow-600" :
          "text-text-muted"
        }`}>
          {status === "idle" && "Redo"}
          {status === "connecting" && "Ansluter…"}
          {status === "connected" && "● Uppkopplad"}
          {status === "ended" && "Avslutat"}
        </span>
      </div>

      {log.length > 0 && (
        <div className="rounded-md border border-border bg-surface-2 p-3 font-mono text-xs text-text-muted flex flex-col gap-0.5 max-h-48 overflow-y-auto">
          {log.map((line, i) => <span key={i}>{line}</span>)}
        </div>
      )}

      <p className="text-xs text-text-faint">
        Samtalet syns live i{" "}
        <a href="/inbox" className="underline">Inkorgen</a>{" "}
        och sparas med transkription och sammanfattning när du lägger på.
      </p>
    </div>
  );
}

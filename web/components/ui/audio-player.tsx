"use client";

import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { PauseIcon, PlayIcon } from "@/components/icons";
import { formatDurationSv } from "@/lib/format";

interface AudioPlayerProps {
  src: string | null;
  duration?: number;
}

export function AudioPlayer({ src, duration }: AudioPlayerProps) {
  const ref = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const onTime = () =>
      setProgress(el.duration ? el.currentTime / el.duration : 0);
    const onEnd = () => setPlaying(false);
    el.addEventListener("timeupdate", onTime);
    el.addEventListener("ended", onEnd);
    return () => {
      el.removeEventListener("timeupdate", onTime);
      el.removeEventListener("ended", onEnd);
    };
  }, []);

  const toggle = () => {
    const el = ref.current;
    if (!el) return;
    if (playing) {
      el.pause();
      setPlaying(false);
    } else {
      void el.play();
      setPlaying(true);
    }
  };

  return (
    <div className="rounded-md border border-border bg-surface-2 px-4 py-3 flex items-center gap-3">
      <Button
        variant="ghost"
        size="icon"
        onClick={toggle}
        disabled={!src}
        aria-label={playing ? "Pausa" : "Spela"}
      >
        {playing ? <PauseIcon className="h-4 w-4" /> : <PlayIcon className="h-4 w-4" />}
      </Button>
      <div className="flex-1">
        <div className="h-1 rounded-full bg-surface-3 overflow-hidden">
          <div
            className="h-full bg-accent transition-[width] duration-150"
            style={{ width: `${Math.round(progress * 100)}%` }}
          />
        </div>
        <div className="mt-1 text-xs text-text-muted">
          {src ? "Inspelning tillgänglig" : "Inspelning saknas"}
          {duration ? ` · ${formatDurationSv(duration)}` : null}
        </div>
      </div>
      {src ? <audio ref={ref} src={src} preload="metadata" /> : null}
    </div>
  );
}

"""Capture both legs of a call, encode to MP3-safe PCM container, persist
to the firma's bucket, set `Call.recording_url` to a signed URL.

MP3 encoding requires `ffmpeg` available on the host. If not, we fall
back to writing a WAV file — playable everywhere, larger footprint
(~960 KB/min vs ~30 KB/min), acceptable for MVP since Cloud Run images
will install `ffmpeg` (P9).
"""

from __future__ import annotations

import io
import shutil
import struct
import subprocess
from dataclasses import dataclass, field
from datetime import timedelta

import numpy as np

from svarsa.bridge.audio import GEMINI_OUT_RATE, MULAW_RATE
from svarsa.core.config import Settings, get_settings
from svarsa.core.logging import get_logger
from svarsa.integrations.storage import TenantBlobStore, make_storage

log = get_logger("svarsa.recording")


@dataclass
class RecordingBuffer:
    """Stitches caller (μ-law 8 kHz) + AI (PCM 24 kHz) audio into a stereo PCM 24 kHz mix.

    Caller is upsampled to 24 kHz on-the-fly so we don't have to keep two
    separate timelines. Both legs sit in the same monotonic time axis tied
    to call.started_at.
    """

    call_id: str
    firma_id: str
    caller_chunks: list[bytes] = field(default_factory=list)
    ai_chunks: list[bytes] = field(default_factory=list)

    def add_caller_pcm16k(self, pcm16k: bytes) -> None:
        # Resample 16k → 24k by polyphase. Cheap on the audio thread.
        if not pcm16k:
            return
        from scipy.signal import resample_poly  # type: ignore[import-untyped]

        samples = np.frombuffer(pcm16k, dtype=np.int16).astype(np.float32)
        out = resample_poly(samples, GEMINI_OUT_RATE, 16000)
        self.caller_chunks.append(np.clip(out, -32768, 32767).astype(np.int16).tobytes())

    def add_ai_pcm24k(self, pcm24k: bytes) -> None:
        if pcm24k:
            self.ai_chunks.append(pcm24k)


def _wav_header(num_samples: int, *, channels: int = 1, rate: int = GEMINI_OUT_RATE) -> bytes:
    byte_rate = rate * channels * 2
    block_align = channels * 2
    data_size = num_samples * channels * 2
    riff_size = 36 + data_size
    return (
        b"RIFF"
        + struct.pack("<I", riff_size)
        + b"WAVE"
        + b"fmt "
        + struct.pack("<IHHIIHH", 16, 1, channels, rate, byte_rate, block_align, 16)
        + b"data"
        + struct.pack("<I", data_size)
    )


def _mix_to_mono_wav(buffer: RecordingBuffer) -> bytes:
    caller = b"".join(buffer.caller_chunks)
    ai = b"".join(buffer.ai_chunks)
    a = np.frombuffer(caller, dtype=np.int16).astype(np.int32)
    b = np.frombuffer(ai, dtype=np.int16).astype(np.int32)
    n = max(a.size, b.size)
    if a.size < n:
        a = np.pad(a, (0, n - a.size))
    if b.size < n:
        b = np.pad(b, (0, n - b.size))
    mono = ((a + b) // 2).clip(-32768, 32767).astype(np.int16)
    return _wav_header(mono.size) + mono.tobytes()


def _wav_to_mp3(wav_bytes: bytes) -> bytes | None:
    """Encode WAV → MP3 64kbps mono via ffmpeg if available."""
    if shutil.which("ffmpeg") is None:
        return None
    proc = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-codec:a", "libmp3lame",
         "-b:a", "64k", "-ac", "1", "-f", "mp3", "pipe:1"],
        input=wav_bytes,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        log.warning("recording.ffmpeg_failed", stderr=proc.stderr.decode("utf-8", "replace"))
        return None
    return proc.stdout


def finalize_and_persist(
    buffer: RecordingBuffer,
    *,
    settings: Settings | None = None,
    storage: TenantBlobStore | None = None,
) -> tuple[str, str]:
    """Encode the buffer, write to storage, return (key, signed_url)."""
    s = settings or get_settings()
    store = storage or make_storage(s)
    store.ensure_bucket(buffer.firma_id)

    wav = _mix_to_mono_wav(buffer)
    mp3 = _wav_to_mp3(wav)
    if mp3 is not None:
        ext, content_type, payload = "mp3", "audio/mpeg", mp3
    else:
        ext, content_type, payload = "wav", "audio/wav", wav

    key = f"calls/{buffer.call_id}.{ext}"
    store.write(buffer.firma_id, key, payload, content_type)
    url = store.signed_url(buffer.firma_id, key, timedelta(hours=1))
    log.info(
        "recording.persisted",
        call_id=buffer.call_id,
        firma_id=buffer.firma_id,
        bytes=len(payload),
        codec=ext,
    )
    return key, url

"""Audio transcoding between telephony G.711 μ-law 8kHz and Gemini PCM 16/24kHz.

The hot path uses `audioop` for μ-law ↔ linear PCM (C-implementation, fast)
and `scipy.signal.resample_poly` for sample-rate conversion. Worst-case
end-to-end transcode latency on warm pods is <8 ms per direction (PRD §8.2.3).
"""

from __future__ import annotations

import audioop  # type: ignore[import-untyped]

import numpy as np
from scipy.signal import resample_poly  # type: ignore[import-untyped]

MULAW_RATE = 8000
GEMINI_IN_RATE = 16000
GEMINI_OUT_RATE = 24000

MULAW_FRAME_BYTES = 160  # 20ms at 8kHz, 1 byte/sample


def _resample_pcm16(pcm16: bytes, from_rate: int, to_rate: int) -> bytes:
    if from_rate == to_rate:
        return pcm16
    samples = np.frombuffer(pcm16, dtype=np.int16)
    if samples.size == 0:
        return b""
    # resample_poly handles arbitrary integer ratios with anti-aliasing.
    from math import gcd
    g = gcd(to_rate, from_rate)
    up = to_rate // g
    down = from_rate // g
    out = resample_poly(samples.astype(np.float32), up, down)
    out_clipped = np.clip(out, -32768, 32767).astype(np.int16)
    return out_clipped.tobytes()


def mulaw_to_pcm16k(mulaw_frames: bytes) -> bytes:
    """Telephony → Gemini input: μ-law 8kHz → PCM16 16kHz."""
    pcm8k = audioop.ulaw2lin(mulaw_frames, 2)
    return _resample_pcm16(pcm8k, MULAW_RATE, GEMINI_IN_RATE)


def pcm24k_to_mulaw(pcm24k: bytes) -> bytes:
    """Gemini output → telephony: PCM16 24kHz → μ-law 8kHz."""
    pcm8k = _resample_pcm16(pcm24k, GEMINI_OUT_RATE, MULAW_RATE)
    return audioop.lin2ulaw(pcm8k, 2)


def chunk_mulaw_frames(mulaw: bytes, frame_size: int = MULAW_FRAME_BYTES) -> list[bytes]:
    """Split μ-law audio into provider-friendly 20ms frames."""
    return [mulaw[i : i + frame_size] for i in range(0, len(mulaw), frame_size)]


def pcm24k_to_pcm16k(pcm24k: bytes) -> bytes:
    """46elks (and the in-browser voice-test) → Gemini input rate.

    Caller leg already arrives at 24 kHz from the pcm_24000-speaking
    provider — we just need to downsample for Gemini Live's 16 kHz input.
    """
    return _resample_pcm16(pcm24k, GEMINI_OUT_RATE, GEMINI_IN_RATE)

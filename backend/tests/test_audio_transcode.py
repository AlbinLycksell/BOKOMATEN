from __future__ import annotations

import math

import numpy as np

from svarsa.bridge.audio import (
    GEMINI_IN_RATE,
    GEMINI_OUT_RATE,
    MULAW_RATE,
    chunk_mulaw_frames,
    mulaw_to_pcm16k,
    pcm24k_to_mulaw,
)


def _sine_pcm16(freq: float, rate: int, seconds: float) -> bytes:
    t = np.arange(int(rate * seconds)) / rate
    samples = (np.sin(2 * math.pi * freq * t) * 0.5 * 32767).astype(np.int16)
    return samples.tobytes()


def test_mulaw_to_pcm16k_doubles_sample_count() -> None:
    mulaw_2000_samples = bytes(2000)
    pcm = mulaw_to_pcm16k(mulaw_2000_samples)
    expected_samples = 2000 * GEMINI_IN_RATE // MULAW_RATE
    assert len(pcm) == expected_samples * 2  # 16-bit


def test_pcm24k_to_mulaw_compresses_3_to_1() -> None:
    pcm24k = _sine_pcm16(440.0, GEMINI_OUT_RATE, 0.1)
    mulaw = pcm24k_to_mulaw(pcm24k)
    expected = (len(pcm24k) // 2) * MULAW_RATE // GEMINI_OUT_RATE
    assert abs(len(mulaw) - expected) <= 2


def test_round_trip_preserves_signal_within_tolerance() -> None:
    pcm24k = _sine_pcm16(440.0, GEMINI_OUT_RATE, 0.5)
    mulaw = pcm24k_to_mulaw(pcm24k)
    pcm16k = mulaw_to_pcm16k(mulaw)
    assert len(pcm16k) > 0
    samples_in = np.frombuffer(pcm24k, dtype=np.int16)
    samples_out = np.frombuffer(pcm16k, dtype=np.int16)
    rms_in = float(np.sqrt(np.mean(samples_in.astype(np.float32) ** 2)))
    rms_out = float(np.sqrt(np.mean(samples_out.astype(np.float32) ** 2)))
    assert 0.4 < rms_out / rms_in < 1.6


def test_chunk_mulaw_frames_default_20ms() -> None:
    frames = chunk_mulaw_frames(bytes(720))
    assert len(frames) == 5
    assert all(len(f) == 160 for f in frames[:-1])
    assert len(frames[-1]) == 80

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from svarsa.bridge.audio import GEMINI_OUT_RATE
from svarsa.integrations.storage import LocalStorage
from svarsa.services.recording_service import (
    RecordingBuffer,
    finalize_and_persist,
)


def _silence_pcm16(rate: int, seconds: float) -> bytes:
    n = int(rate * seconds)
    return np.zeros(n, dtype=np.int16).tobytes()


def test_recording_buffer_round_trip_writes_audio(tmp_path: Path) -> None:
    buf = RecordingBuffer(call_id="01J-call", firma_id="01J-firma")
    buf.add_caller_pcm16k(_silence_pcm16(16000, 0.5))
    buf.add_ai_pcm24k(_silence_pcm16(GEMINI_OUT_RATE, 0.3))

    store = LocalStorage(root=tmp_path)
    key, url = finalize_and_persist(buf, storage=store)

    assert key.startswith("calls/01J-call.")
    assert key.endswith(".mp3") or key.endswith(".wav")
    assert store.exists("01J-firma", key)
    body = store.read("01J-firma", key)
    assert len(body) > 0


def test_recording_handles_empty_buffer(tmp_path: Path) -> None:
    buf = RecordingBuffer(call_id="01J-empty", firma_id="01J-firma")
    store = LocalStorage(root=tmp_path)
    key, _ = finalize_and_persist(buf, storage=store)
    assert store.exists("01J-firma", key)

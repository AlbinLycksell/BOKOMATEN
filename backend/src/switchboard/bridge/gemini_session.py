"""Gemini Live session factory — config + connect helpers.

Two provider paths:

- ``api_key`` (dev / eval): hits ``generativelanguage.googleapis.com`` with
  the ``GEMINI_API_KEY`` env var. Lowest setup, US-hosted, no DPA.
- ``vertex`` (prod): hits Vertex AI in ``europe-west4`` via the project's
  Workload Identity / service account. EU residency, Customer Data Use
  commitments, audit logs. PRD §8.3.1 / §8.10.

The bridge picks the path from ``Settings.gemini_provider``.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from google import genai
from google.genai import types as gtypes

from switchboard.bridge.system_prompt import build_system_prompt
from switchboard.core.config import Settings, get_settings
from switchboard.core.logging import get_logger
from switchboard.models import Firma
from switchboard.tools.declarations import TOOL_DECLARATIONS

log = get_logger("switchboard.gemini")


def build_live_config(firma: Firma, settings: Settings) -> gtypes.LiveConnectConfig:
    voice = (firma.settings or {}).get("voice", settings.gemini_voice)
    return gtypes.LiveConnectConfig(
        response_modalities=[gtypes.Modality.AUDIO],
        speech_config=gtypes.SpeechConfig(
            language_code=settings.gemini_language,
            voice_config=gtypes.VoiceConfig(
                prebuilt_voice_config=gtypes.PrebuiltVoiceConfig(voice_name=voice)
            ),
        ),
        system_instruction=gtypes.Content(
            parts=[gtypes.Part(text=build_system_prompt(firma))],
            role="system",
        ),
        tools=TOOL_DECLARATIONS,
        output_audio_transcription=gtypes.AudioTranscriptionConfig(),
        input_audio_transcription=gtypes.AudioTranscriptionConfig(),
        session_resumption=gtypes.SessionResumptionConfig(),
        context_window_compression=gtypes.ContextWindowCompressionConfig(
            trigger_tokens=100_000,
            sliding_window=gtypes.SlidingWindow(target_tokens=12_000),
        ),
    )


def make_client(settings: Settings | None = None) -> genai.Client:
    s = settings or get_settings()
    if s.gemini_provider == "vertex":
        if not s.vertex_project:
            msg = "SWITCHBOARD_VERTEX_PROJECT must be set when SWITCHBOARD_GEMINI_PROVIDER=vertex"
            raise RuntimeError(msg)
        log.info(
            "gemini.client.vertex",
            project=s.vertex_project,
            location=s.vertex_location,
        )
        return genai.Client(
            vertexai=True,
            project=s.vertex_project,
            location=s.vertex_location,
        )
    log.info("gemini.client.api_key")
    return genai.Client(
        http_options={"api_version": "v1beta"},
        api_key=s.gemini_api_key or None,
    )


def model_name(settings: Settings | None = None) -> str:
    s = settings or get_settings()
    # Vertex API uses bare model id without the `models/` prefix.
    if s.gemini_provider == "vertex":
        return s.gemini_model.removeprefix("models/")
    return s.gemini_model


@asynccontextmanager
async def connect(firma: Firma, settings: Settings | None = None):  # type: ignore[no-untyped-def]
    s = settings or get_settings()
    client = make_client(s)
    config = build_live_config(firma, s)
    async with client.aio.live.connect(model=model_name(s), config=config) as session:
        yield session

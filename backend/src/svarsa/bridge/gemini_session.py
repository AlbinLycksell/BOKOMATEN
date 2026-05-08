"""Gemini Live session factory — config + connect helpers."""

from __future__ import annotations

from contextlib import asynccontextmanager

from google import genai
from google.genai import types as gtypes

from svarsa.core.config import Settings, get_settings
from svarsa.models import Firma
from svarsa.bridge.system_prompt import build_system_prompt
from svarsa.tools.declarations import TOOL_DECLARATIONS


def build_live_config(firma: Firma, settings: Settings) -> gtypes.LiveConnectConfig:
    return gtypes.LiveConnectConfig(
        response_modalities=[gtypes.Modality.AUDIO],
        speech_config=gtypes.SpeechConfig(
            language_code=settings.gemini_language,
            voice_config=gtypes.VoiceConfig(
                prebuilt_voice_config=gtypes.PrebuiltVoiceConfig(
                    voice_name=firma.settings.get("voice", settings.gemini_voice)
                    if firma.settings
                    else settings.gemini_voice
                )
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
    return genai.Client(
        http_options={"api_version": "v1beta"},
        api_key=s.gemini_api_key or None,
    )


@asynccontextmanager
async def connect(firma: Firma, settings: Settings | None = None):  # type: ignore[no-untyped-def]
    s = settings or get_settings()
    client = make_client(s)
    config = build_live_config(firma, s)
    async with client.aio.live.connect(model=s.gemini_model, config=config) as session:
        yield session

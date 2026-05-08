"""Telephony-provider-agnostic Realtime Bridge WebSocket.

Frame protocol (lowest common denominator across 46elks + Twilio):
  client → server: {"event":"start","payload":{"caller_phone":"+46…"}}
                   {"event":"media","payload":{"audio_b64":"..."}}      (μ-law 8kHz)
                   {"event":"stop"}
  server → client: {"event":"media","payload":{"audio_b64":"..."}}      (μ-law 8kHz)
                   {"event":"summary_ready","payload":{"call_id":"..."}}

Provider adapters wrap their own framing into this shape upstream.
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from google.genai import types as gtypes
from sqlmodel import Session

from svarsa.bridge import audio as audio_codec
from svarsa.bridge.gemini_session import connect as connect_gemini
from svarsa.bridge.usage_tracker import UsageTracker
from svarsa.core.logging import get_logger
from svarsa.core.time import utcnow
from svarsa.db.session import get_engine
from svarsa.models import Call, CallStatus, Firma, TranscriptRole, TranscriptSegment
from svarsa.tools.handlers import ToolContext, dispatch

log = get_logger("svarsa.bridge")
router = APIRouter()


@router.websocket("/ws/bridge/{firma_id}/{call_id}")
async def bridge(websocket: WebSocket, firma_id: str, call_id: str) -> None:
    await websocket.accept()
    log.info("bridge.connected", firma=firma_id, call=call_id)

    with Session(get_engine()) as db:
        firma = db.get(Firma, firma_id)
        if firma is None:
            await websocket.send_json({"event": "error", "payload": {"reason": "unknown_firma"}})
            await websocket.close(code=1008)
            return

        call = Call(id=call_id, firma_id=firma_id, status=CallStatus.IN_PROGRESS)
        db.add(call)
        db.commit()
        db.refresh(call)

        tracker = UsageTracker(call_id=call.id)
        ctx = ToolContext(session=db, firma_id=firma_id, call_id=call_id)
        ts0 = utcnow()

        try:
            async with connect_gemini(firma) as session:
                receive_task = asyncio.create_task(
                    _drain_gemini(websocket, session, db, call, tracker, ctx, ts0)
                )
                try:
                    await _drain_provider(websocket, session, call, ts0, db)
                finally:
                    receive_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await receive_task
        except WebSocketDisconnect:
            log.info("bridge.disconnected", call=call.id)
        except Exception:  # noqa: BLE001
            log.exception("bridge.error", call=call.id)
        finally:
            call.ended_at = utcnow()
            call.status = CallStatus.COMPLETED
            call.billing_seconds = int((call.ended_at - call.started_at).total_seconds())
            db.add(call)
            db.commit()
            from svarsa.agents.runner import schedule_post_call_summary

            schedule_post_call_summary(call.id)


async def _drain_provider(
    websocket: WebSocket,
    session,  # type: ignore[no-untyped-def]
    call: Call,
    ts0,  # type: ignore[no-untyped-def]
    db: Session,
) -> None:
    while True:
        msg = await websocket.receive_json()
        event = msg.get("event")
        payload: dict[str, Any] = msg.get("payload") or {}
        if event == "start":
            caller_phone = payload.get("caller_phone")
            if caller_phone:
                call.caller_phone = caller_phone
                db.add(call)
                db.commit()
            continue
        if event == "media":
            audio_b64 = payload.get("audio_b64", "")
            if not audio_b64:
                continue
            mulaw = base64.b64decode(audio_b64)
            pcm16 = audio_codec.mulaw_to_pcm16k(mulaw)
            await session.send_realtime_input(
                audio=gtypes.Blob(data=pcm16, mime_type="audio/pcm;rate=16000")
            )
            continue
        if event == "stop":
            break


async def _drain_gemini(
    websocket: WebSocket,
    session,  # type: ignore[no-untyped-def]
    db: Session,
    call: Call,
    tracker: UsageTracker,
    ctx: ToolContext,
    ts0,  # type: ignore[no-untyped-def]
) -> None:
    while True:
        turn = session.receive()
        async for response in turn:
            tracker.update(response.usage_metadata)

            if response.tool_call:
                for fc in response.tool_call.function_calls or []:
                    args: dict[str, Any] = dict(fc.args or {})
                    result = dispatch(ctx, fc.name or "", args)
                    await session.send_tool_response(
                        function_responses=[
                            gtypes.FunctionResponse(
                                name=fc.name,
                                id=fc.id,
                                response=result,
                            )
                        ]
                    )
                continue

            data = response.data
            if data:
                mulaw = audio_codec.pcm24k_to_mulaw(data)
                await websocket.send_json(
                    {
                        "event": "media",
                        "payload": {"audio_b64": base64.b64encode(mulaw).decode()},
                    }
                )

            text = response.text
            if text:
                _persist_text(db, call.id, TranscriptRole.AI, text, ts0)

            if response.server_content and response.server_content.input_transcription:
                t = response.server_content.input_transcription.text or ""
                if t:
                    _persist_text(db, call.id, TranscriptRole.CALLER, t, ts0)
        tracker.end_turn()


def _persist_text(
    db: Session,
    call_id: str,
    role: TranscriptRole,
    text: str,
    ts0,  # type: ignore[no-untyped-def]
) -> None:
    offset_ms = int((utcnow() - ts0).total_seconds() * 1000)
    db.add(TranscriptSegment(call_id=call_id, role=role, text=text, ts_ms_offset=offset_ms))
    db.commit()

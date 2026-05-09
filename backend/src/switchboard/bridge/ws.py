"""Telephony Realtime Bridge WebSocket — speaks 46elks Voice Streaming natively.

Per the official 46elks protocol (https://46elks.fi/tutorials/real-time-two-way-voice-calls-with-websocket):

  client → server (46elks):
    {"t":"hello","callid":"...","from":"+46...","to":"+46..."}     once at start
    {"t":"audio","data":"<base64 PCM 24kHz mono int16>"}           streamed
    {"t":"sync"}                                                   periodic keep-alive
    {"t":"bye","reason":"hangup"|"done"|"error"}                   call ends

  server → client (us):
    {"t":"sending","format":"pcm_24000"}                            initial declarations
    {"t":"listening","format":"pcm_24000"}
    {"t":"audio","data":"<base64 PCM 24kHz mono int16>"}           streamed
    {"t":"interrupt"}                                              barge-in stop
    {"t":"bye"}                                                    we hang up

Other providers wrap their framing into the same shape (Twilio adapter
deferred — its μ-law path is in `audio.py`).
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
from typing import Any

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from google.genai import types as gtypes
from sqlmodel import Session

from switchboard.bridge import audio as audio_codec
from switchboard.bridge.gemini_session import connect as connect_gemini
from switchboard.bridge.usage_tracker import UsageTracker
from switchboard.core.logging import get_logger
from switchboard.core.tenant import firma_context
from switchboard.core.time import utcnow
from switchboard.db.session import get_engine
from switchboard.models import Call, CallStatus, Firma, TranscriptRole, TranscriptSegment
from switchboard.services import cost_service, recording_service, redaction_service
from switchboard.tools.client import ToolClient, make_tool_client

log = get_logger("switchboard.bridge")
router = APIRouter()


@router.websocket("/ws/bridge/{firma_id}/{call_id}")
async def bridge(websocket: WebSocket, firma_id: str, call_id: str) -> None:
    await websocket.accept()

    with firma_context(firma_id), Session(get_engine()) as db:
        structlog.contextvars.bind_contextvars(call_id=call_id)
        log.info("bridge.connected")
        firma = db.get(Firma, firma_id)
        if firma is None:
            await websocket.send_json({"t": "bye", "reason": "unknown_firma"})
            await websocket.close(code=1008)
            return

        call = Call(id=call_id, firma_id=firma_id, status=CallStatus.IN_PROGRESS)
        db.add(call)
        db.commit()
        db.refresh(call)

        from switchboard.api.ws_inbox import publish

        await publish(
            firma_id,
            "inbox.call.created",
            {"id": call.id, "started_at": call.started_at.isoformat()},
        )

        # Declare bidirectional PCM 24kHz immediately.
        await websocket.send_json({"t": "sending", "format": "pcm_24000"})
        await websocket.send_json({"t": "listening", "format": "pcm_24000"})

        tracker = UsageTracker(call_id=call.id)
        tool_client = make_tool_client(db)
        recording = recording_service.RecordingBuffer(call_id=call.id, firma_id=firma_id)
        ts0 = utcnow()

        try:
            async with connect_gemini(firma) as session:
                receive_task = asyncio.create_task(
                    _drain_gemini(
                        websocket, session, db, call, tracker, tool_client,
                        recording, firma_id, ts0,
                    )
                )
                try:
                    await _drain_provider(websocket, session, call, ts0, db, recording)
                finally:
                    receive_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await receive_task
        except WebSocketDisconnect:
            log.info("bridge.disconnected")
        except Exception:  # noqa: BLE001
            log.exception("bridge.error")
        finally:
            call.ended_at = utcnow()
            call.status = CallStatus.COMPLETED
            call.billing_seconds = int((call.ended_at - call.started_at).total_seconds())

            consent_disabled = getattr(tool_client, "consent_disabled", False)
            if consent_disabled:
                log.info("recording.skipped.consent_disabled", call_id=call.id)
            else:
                try:
                    _key, url = recording_service.finalize_and_persist(recording)
                    call.recording_url = url
                except Exception:  # noqa: BLE001
                    log.exception("recording.persist_failed", call_id=call.id)

            try:
                from sqlmodel import select

                from switchboard.models import ToolInvocation

                sms_count = len(
                    db.exec(
                        select(ToolInvocation)
                        .where(ToolInvocation.call_id == call.id)
                        .where(ToolInvocation.name == "send_sms_followup")
                    ).all()
                )
                breakdown = cost_service.compute(
                    usage=tracker.snapshot(),
                    duration_seconds=call.billing_seconds,
                    sms_count=sms_count,
                )
                call.cost_breakdown = breakdown.to_dict()
                call.cost_total_sek = breakdown.total_sek
                log.info(
                    "cost.computed",
                    call_id=call.id,
                    total_sek=breakdown.total_sek,
                    minutes=round(call.billing_seconds / 60, 2),
                )
            except Exception:  # noqa: BLE001
                log.exception("cost.compute_failed", call_id=call.id)

            db.add(call)
            db.commit()
            if hasattr(tool_client, "aclose"):
                await tool_client.aclose()  # type: ignore[no-untyped-call]
            from switchboard.agents.runner import schedule_post_call_summary
            from switchboard.api.ws_inbox import publish

            schedule_post_call_summary(call.id)
            await publish(
                firma_id,
                "inbox.call.updated",
                {
                    "id": call.id,
                    "status": call.status.value,
                    "intent": call.intent.value if call.intent else None,
                    "severity": call.severity.value if call.severity else None,
                    "duration_seconds": call.billing_seconds,
                    "cost_total_sek": call.cost_total_sek,
                },
            )
            structlog.contextvars.unbind_contextvars("call_id")


async def _drain_provider(
    websocket: WebSocket,
    session,  # type: ignore[no-untyped-def]
    call: Call,
    ts0,  # type: ignore[no-untyped-def]
    db: Session,
    recording,  # type: ignore[no-untyped-def]
) -> None:
    while True:
        msg = await websocket.receive_json()
        event = msg.get("t") or msg.get("event")  # `t` is 46elks; `event` is dev/test
        if event == "hello":
            caller_phone = msg.get("from")
            if caller_phone:
                call.caller_phone = caller_phone
                db.add(call)
                db.commit()
            log.info("bridge.hello", caller=caller_phone, callid=msg.get("callid"))
            continue
        if event == "audio":
            audio_b64 = msg.get("data") or (msg.get("payload") or {}).get("audio_b64", "")
            if not audio_b64:
                continue
            pcm24 = base64.b64decode(audio_b64)
            recording.add_caller_pcm24k(pcm24)
            pcm16 = audio_codec.pcm24k_to_pcm16k(pcm24)
            await session.send_realtime_input(
                audio=gtypes.Blob(data=pcm16, mime_type="audio/pcm;rate=16000")
            )
            continue
        if event == "sync":
            await websocket.send_json({"t": "sync"})
            continue
        if event in ("bye", "stop"):
            log.info("bridge.bye", reason=msg.get("reason"))
            break


async def _drain_gemini(
    websocket: WebSocket,
    session,  # type: ignore[no-untyped-def]
    db: Session,
    call: Call,
    tracker: UsageTracker,
    tool_client: ToolClient,
    recording,  # type: ignore[no-untyped-def]
    firma_id: str,
    ts0,  # type: ignore[no-untyped-def]
) -> None:
    while True:
        turn = session.receive()
        async for response in turn:
            tracker.update(response.usage_metadata)

            if response.tool_call:
                for fc in response.tool_call.function_calls or []:
                    args: dict[str, Any] = dict(fc.args or {})
                    result = await tool_client.dispatch(
                        firma_id=firma_id,
                        call_id=call.id,
                        name=fc.name or "",
                        args=args,
                    )
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
                recording.add_ai_pcm24k(data)
                # Gemini emits PCM 24k mono — same wire format 46elks expects.
                await websocket.send_json(
                    {"t": "audio", "data": base64.b64encode(data).decode()}
                )

            sc = response.server_content
            if sc is not None:
                # Server-side transcripts (in/out)
                if sc.input_transcription and (t_in := sc.input_transcription.text or ""):
                    _persist_text(db, call.id, TranscriptRole.CALLER, t_in, ts0)
                if sc.output_transcription and (t_out := sc.output_transcription.text or ""):
                    _persist_text(db, call.id, TranscriptRole.AI, t_out, ts0)
                if getattr(sc, "interrupted", False):
                    # Stop our outbound playback at the provider so the model
                    # can hear the caller again immediately.
                    await websocket.send_json({"t": "interrupt"})

            if response.text:
                _persist_text(db, call.id, TranscriptRole.AI, response.text, ts0)
        tracker.end_turn()


def _persist_text(
    db: Session,
    call_id: str,
    role: TranscriptRole,
    text: str,
    ts0,  # type: ignore[no-untyped-def]
) -> None:
    redaction = redaction_service.redact(text)
    offset_ms = int((utcnow() - ts0).total_seconds() * 1000)
    db.add(
        TranscriptSegment(
            call_id=call_id,
            role=role,
            text=redaction.redacted,
            ts_ms_offset=offset_ms,
        )
    )
    db.commit()
    if redaction.spans:
        from switchboard.services import audit_service

        audit_service.record(
            db,
            actor="system",
            action="transcript.redacted",
            target_type="call",
            target_id=call_id,
            payload={
                "labels": [label for label, _ in redaction.spans],
                "role": role.value,
                "ts_ms_offset": offset_ms,
            },
        )

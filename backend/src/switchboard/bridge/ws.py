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
from switchboard.core.time import to_utc_aware, utcnow
from switchboard.db.session import get_engine
from switchboard.models import (
    AudioFormat,
    AudioMimeType,
    AuditAction,
    AuditActor,
    AuditTargetType,
    BridgeBye,
    BridgeWSEvent,
    Call,
    CallSource,
    CallStatus,
    Firma,
    InboxEvent,
    ToolName,
    TranscriptRole,
    TranscriptSegment,
)
from switchboard.services import cost_service, recording_service, redaction_service
from switchboard.tools.client import ToolClient, make_tool_client

log = get_logger("switchboard.bridge")
router = APIRouter()


_BYE_FIELD_REASON = "reason"
_AUDIO_FIELD_DATA = "data"
_HELLO_FIELD_FROM = "from"
_HELLO_FIELD_CALLID = "callid"
_TRANSCRIPT_FIELD_ROLE = "role"
_TRANSCRIPT_FIELD_TEXT = "text"
_FRAME_FIELD_TYPE = "t"
_FRAME_FIELD_FORMAT = "format"
_LEGACY_EVENT_KEY = "event"
_LEGACY_PAYLOAD_KEY = "payload"
_LEGACY_AUDIO_FIELD = "audio_b64"

_WS_CLOSE_POLICY = 1008
_WS_CLOSE_INTERNAL = 1011


def _classify_exception_for_client(exc: BaseException) -> BridgeBye | str:
    msg = str(exc).lower()
    if "api key" in msg or "unauthorized" in msg or "permission" in msg or "401" in msg:
        return BridgeBye.GEMINI_AUTH_FAILED
    if "model" in msg and ("not found" in msg or "permission" in msg):
        return BridgeBye.GEMINI_MODEL_UNAVAILABLE
    if "quota" in msg or "rate" in msg or "exhausted" in msg:
        return BridgeBye.GEMINI_QUOTA_EXHAUSTED
    if "websocket" in msg or "connection" in msg:
        return BridgeBye.GEMINI_CONNECT_FAILED
    return f"bridge_error:{exc.__class__.__name__}"


@router.websocket("/ws/bridge/{firma_id}/{call_id}")
async def bridge(websocket: WebSocket, firma_id: str, call_id: str) -> None:
    await websocket.accept()

    try:
        source = CallSource(websocket.query_params.get("source"))
    except ValueError:
        source = CallSource.TELEPHONY

    with firma_context(firma_id), Session(get_engine()) as db:
        structlog.contextvars.bind_contextvars(call_id=call_id, source=source)
        log.info("bridge.connected")
        firma = db.get(Firma, firma_id)
        if firma is None:
            await websocket.send_json(
                {_FRAME_FIELD_TYPE: BridgeWSEvent.BYE.value, _BYE_FIELD_REASON: BridgeBye.UNKNOWN_FIRMA.value}
            )
            await websocket.close(code=_WS_CLOSE_POLICY)
            return

        call = Call(
            id=call_id,
            firma_id=firma_id,
            status=CallStatus.IN_PROGRESS,
            source=source,
            gemini_session_id=f"{source.value}:{call_id}",
        )
        db.add(call)
        db.commit()
        db.refresh(call)

        from switchboard.api.ws_inbox import publish

        await publish(
            firma_id,
            InboxEvent.CALL_CREATED.value,
            {"id": call.id, "started_at": call.started_at.isoformat()},
        )

        await websocket.send_json(
            {_FRAME_FIELD_TYPE: BridgeWSEvent.SENDING.value, _FRAME_FIELD_FORMAT: AudioFormat.PCM_24K.value}
        )
        await websocket.send_json(
            {_FRAME_FIELD_TYPE: BridgeWSEvent.LISTENING.value, _FRAME_FIELD_FORMAT: AudioFormat.PCM_24K.value}
        )

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
        except Exception as exc:  # noqa: BLE001
            log.exception("bridge.error")
            reason = _classify_exception_for_client(exc)
            reason_str = reason.value if isinstance(reason, BridgeBye) else reason
            with contextlib.suppress(Exception):
                await websocket.send_json(
                    {_FRAME_FIELD_TYPE: BridgeWSEvent.BYE.value, _BYE_FIELD_REASON: reason_str}
                )
                await websocket.close(code=_WS_CLOSE_INTERNAL)
        finally:
            call.ended_at = utcnow()
            call.status = CallStatus.COMPLETED
            call.billing_seconds = int(
                (call.ended_at - to_utc_aware(call.started_at)).total_seconds()
            )

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
                        .where(ToolInvocation.name == ToolName.SEND_SMS_FOLLOWUP.value)
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
                InboxEvent.CALL_UPDATED.value,
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
        raw_event = msg.get(_FRAME_FIELD_TYPE) or msg.get(_LEGACY_EVENT_KEY)
        try:
            event = BridgeWSEvent(raw_event) if raw_event else None
        except ValueError:
            event = None
        if event is BridgeWSEvent.HELLO:
            caller_phone = msg.get(_HELLO_FIELD_FROM)
            if caller_phone:
                call.caller_phone = caller_phone
                db.add(call)
                db.commit()
            log.info("bridge.hello", caller=caller_phone, callid=msg.get(_HELLO_FIELD_CALLID))
            continue
        if event is BridgeWSEvent.AUDIO:
            audio_b64 = msg.get(_AUDIO_FIELD_DATA) or (msg.get(_LEGACY_PAYLOAD_KEY) or {}).get(
                _LEGACY_AUDIO_FIELD, ""
            )
            if not audio_b64:
                continue
            pcm24 = base64.b64decode(audio_b64)
            recording.add_caller_pcm24k(pcm24)
            pcm16 = audio_codec.pcm24k_to_pcm16k(pcm24)
            await session.send_realtime_input(
                audio=gtypes.Blob(data=pcm16, mime_type=AudioMimeType.PCM_16K.value)
            )
            continue
        if event is BridgeWSEvent.SYNC:
            await websocket.send_json({_FRAME_FIELD_TYPE: BridgeWSEvent.SYNC.value})
            continue
        if event in (BridgeWSEvent.BYE, BridgeWSEvent.STOP):
            log.info("bridge.bye", reason=msg.get(_BYE_FIELD_REASON))
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
                await websocket.send_json(
                    {
                        _FRAME_FIELD_TYPE: BridgeWSEvent.AUDIO.value,
                        _AUDIO_FIELD_DATA: base64.b64encode(data).decode(),
                    }
                )

            sc = response.server_content
            if sc is not None:
                if sc.input_transcription and (t_in := sc.input_transcription.text or ""):
                    _persist_text(db, call.id, TranscriptRole.CALLER, t_in, ts0)
                    await _forward_transcript(websocket, TranscriptRole.CALLER, t_in)
                if sc.output_transcription and (t_out := sc.output_transcription.text or ""):
                    _persist_text(db, call.id, TranscriptRole.AI, t_out, ts0)
                    await _forward_transcript(websocket, TranscriptRole.AI, t_out)
                if getattr(sc, "interrupted", False):
                    await websocket.send_json({_FRAME_FIELD_TYPE: BridgeWSEvent.INTERRUPT.value})

            if response.text:
                _persist_text(db, call.id, TranscriptRole.AI, response.text, ts0)
                await _forward_transcript(websocket, TranscriptRole.AI, response.text)
        tracker.end_turn()


async def _forward_transcript(websocket: WebSocket, role: TranscriptRole, text: str) -> None:
    if not text.strip():
        return
    try:
        await websocket.send_json(
            {
                _FRAME_FIELD_TYPE: BridgeWSEvent.TRANSCRIPT.value,
                _TRANSCRIPT_FIELD_ROLE: role.value,
                _TRANSCRIPT_FIELD_TEXT: text,
            }
        )
    except Exception:  # noqa: BLE001
        pass


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
            actor=AuditActor.SYSTEM,
            action=AuditAction.TRANSCRIPT_REDACTED,
            target_type=AuditTargetType.CALL,
            target_id=call_id,
            payload={
                "labels": [label for label, _ in redaction.spans],
                "role": role.value,
                "ts_ms_offset": offset_ms,
            },
        )

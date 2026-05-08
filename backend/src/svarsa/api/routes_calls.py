from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from svarsa.api.deps import get_current_firma, get_db
from svarsa.models import (
    Call,
    CallDetailRead,
    CallRead,
    CallStatus,
    CallSummary,
    Customer,
    Firma,
    Intent,
    Severity,
    ToolInvocation,
    ToolInvocationRead,
    TranscriptSegment,
    TranscriptSegmentRead,
)

router = APIRouter(prefix="/api/calls", tags=["calls"])


def _to_read(call: Call, customer_name: str | None) -> CallRead:
    summary_short: str | None = None
    if call.summary:
        summary_short = call.summary.get("short_sv")
    duration = 0
    if call.ended_at and call.started_at:
        duration = int((call.ended_at - call.started_at).total_seconds())
    return CallRead(
        id=call.id,
        customer_id=call.customer_id,
        customer_name=customer_name,
        caller_phone=call.caller_phone,
        started_at=call.started_at,
        ended_at=call.ended_at,
        duration_seconds=duration,
        intent=call.intent,
        severity=call.severity,
        status=call.status,
        summary_short=summary_short,
    )


@router.get("", response_model=list[CallRead])
def list_calls(
    firma: Annotated[Firma, Depends(get_current_firma)],
    db: Annotated[Session, Depends(get_db)],
    intent: Intent | None = None,
    severity: Severity | None = None,
    status_filter: Annotated[CallStatus | None, Query(alias="status")] = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[CallRead]:
    stmt = select(Call).where(Call.firma_id == firma.id)
    if intent is not None:
        stmt = stmt.where(Call.intent == intent)
    if severity is not None:
        stmt = stmt.where(Call.severity == severity)
    if status_filter is not None:
        stmt = stmt.where(Call.status == status_filter)
    stmt = stmt.order_by(Call.started_at.desc()).offset(offset).limit(limit)  # type: ignore[attr-defined]
    calls = db.exec(stmt).all()
    out: list[CallRead] = []
    for call in calls:
        name: str | None = None
        if call.customer_id:
            cust = db.get(Customer, call.customer_id)
            name = cust.name if cust else None
        out.append(_to_read(call, name))
    return out


@router.get("/{call_id}", response_model=CallDetailRead)
def get_call(
    call_id: str,
    firma: Annotated[Firma, Depends(get_current_firma)],
    db: Annotated[Session, Depends(get_db)],
) -> CallDetailRead:
    call = db.get(Call, call_id)
    if call is None or call.firma_id != firma.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="call_not_found")

    customer_name = None
    if call.customer_id:
        cust = db.get(Customer, call.customer_id)
        customer_name = cust.name if cust else None
    base = _to_read(call, customer_name)

    segments = db.exec(
        select(TranscriptSegment)
        .where(TranscriptSegment.call_id == call_id)
        .order_by(TranscriptSegment.ts_ms_offset)  # type: ignore[arg-type]
    ).all()
    transcript = [
        TranscriptSegmentRead(role=s.role, text=s.text, ts_ms_offset=s.ts_ms_offset)
        for s in segments
    ]
    invocations = db.exec(
        select(ToolInvocation)
        .where(ToolInvocation.call_id == call_id)
        .order_by(ToolInvocation.invoked_at)  # type: ignore[arg-type]
    ).all()
    tools = [
        ToolInvocationRead(
            name=i.name,
            args=i.args,
            result=i.result,
            latency_ms=i.latency_ms,
            error=i.error,
            invoked_at=i.invoked_at,
        )
        for i in invocations
    ]
    summary = CallSummary.model_validate(call.summary) if call.summary else None

    return CallDetailRead(
        **base.model_dump(),
        summary=summary,
        transcript=transcript,
        tool_invocations=tools,
        recording_url=call.recording_url,
    )


@router.post("/{call_id}/mark-handled", response_model=CallRead)
def mark_handled(
    call_id: str,
    firma: Annotated[Firma, Depends(get_current_firma)],
    db: Annotated[Session, Depends(get_db)],
) -> CallRead:
    call = db.get(Call, call_id)
    if call is None or call.firma_id != firma.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="call_not_found")
    call.status = CallStatus.HANDLED
    db.add(call)
    db.commit()
    db.refresh(call)
    customer_name = None
    if call.customer_id:
        cust = db.get(Customer, call.customer_id)
        customer_name = cust.name if cust else None
    return _to_read(call, customer_name)

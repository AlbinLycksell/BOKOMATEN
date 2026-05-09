"""Dispatch table mapping tool name → typed handler.

Each handler accepts (`ToolContext`, validated args model) and returns the
result model. Pydantic validation happens at the dispatch boundary so that
malformed model output surfaces as a tool error rather than a crash.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlmodel import Session

from svarsa.core.ids import new_id
from svarsa.core.logging import get_logger
from svarsa.models import ToolInvocation
from svarsa.services import (
    booking_service,
    customer_service,
    escalation_service,
    notification_service,
    rot_service,
    triage_service,
)
from svarsa.tools.schemas import (
    BookAppointmentArgs,
    BookAppointmentResult,
    CheckAvailabilityArgs,
    CheckAvailabilityResult,
    CheckRotEligibilityArgs,
    CheckRotEligibilityResult,
    CreateLeadArgs,
    CreateLeadResult,
    DisableRecordingArgs,
    DisableRecordingResult,
    EscalateToOwnerArgs,
    EscalateToOwnerResult,
    LookupCustomerArgs,
    LookupCustomerResult,
    LookupJobStatusArgs,
    LookupJobStatusResult,
    RequestPhotoUploadArgs,
    RequestPhotoUploadResult,
    SendSmsFollowupArgs,
    SendSmsFollowupResult,
    TakeMessageArgs,
    TakeMessageResult,
    TransferToHumanArgs,
    TransferToHumanResult,
    TriageEmergencyArgs,
    TriageEmergencyResult,
)

log = get_logger("svarsa.tools")


@dataclass
class ToolContext:
    session: Session
    firma_id: str
    call_id: str | None = None
    consent_disabled: bool = False


Handler = Callable[[ToolContext, dict[str, Any]], dict[str, Any]]


def _h_lookup_customer(ctx: ToolContext, raw: dict[str, Any]) -> dict[str, Any]:
    args = LookupCustomerArgs.model_validate(raw)
    customer = None
    if args.phone_number:
        customer = customer_service.lookup_by_phone(ctx.session, ctx.firma_id, args.phone_number)
    if customer is None and args.org_number:
        customer = customer_service.lookup_by_org(ctx.session, ctx.firma_id, args.org_number)
    if customer is None and args.name_query:
        customer = customer_service.lookup_by_name(ctx.session, ctx.firma_id, args.name_query)
    if customer is None:
        return LookupCustomerResult(found=False).model_dump()
    return LookupCustomerResult(
        found=True,
        customer_id=customer.id,
        name=customer.name,
        type=customer.type.value,  # type: ignore[arg-type]
        last_job_summary=customer.notes_summary,
        notes=customer.notes_summary,
    ).model_dump()


def _h_triage_emergency(ctx: ToolContext, raw: dict[str, Any]) -> dict[str, Any]:
    args = TriageEmergencyArgs.model_validate(raw)
    res: TriageEmergencyResult = triage_service.assess(
        args.problem_description, args.trade, args.indicators_present
    )
    return res.model_dump()


def _h_check_availability(ctx: ToolContext, raw: dict[str, Any]) -> dict[str, Any]:
    args = CheckAvailabilityArgs.model_validate(raw)
    res: CheckAvailabilityResult = booking_service.check_availability(
        ctx.session,
        ctx.firma_id,
        duration_minutes=args.duration_minutes,
        earliest_date=args.earliest_date,
        latest_date=args.latest_date,
        required_skills=args.required_skills,
        address=args.address,
    )
    return res.model_dump(mode="json")


def _h_book_appointment(ctx: ToolContext, raw: dict[str, Any]) -> dict[str, Any]:
    args = BookAppointmentArgs.model_validate(raw)
    res: BookAppointmentResult = booking_service.book(
        ctx.session,
        ctx.firma_id,
        customer_id=args.customer_id,
        start_iso=args.start_iso,
        duration_minutes=args.duration_minutes,
        technician_id=args.technician_id,
        address=args.address,
        problem_summary_sv=args.problem_summary_sv,
        rot_eligible=args.rot_eligible,
        call_id=ctx.call_id,
    )
    return res.model_dump()


def _h_create_lead(ctx: ToolContext, raw: dict[str, Any]) -> dict[str, Any]:
    args = CreateLeadArgs.model_validate(raw)
    customer = customer_service.create_lead(
        ctx.session,
        ctx.firma_id,
        name=args.name,
        phone=args.phone,
        type_=args.type,
        email=args.email,
        address=args.address,
        org_number=args.org_number,
        problem_summary_sv=args.problem_summary_sv,
    )
    return CreateLeadResult(customer_id=customer.id, created=True).model_dump()


def _h_escalate(ctx: ToolContext, raw: dict[str, Any]) -> dict[str, Any]:
    args = EscalateToOwnerArgs.model_validate(raw)
    if ctx.call_id is None:
        return EscalateToOwnerResult(
            escalation_id=new_id(), contacted=[], next_in_chain_minutes=0
        ).model_dump()
    res: EscalateToOwnerResult = escalation_service.escalate(
        ctx.session,
        ctx.firma_id,
        ctx.call_id,
        severity=args.severity,  # type: ignore[arg-type]
        reason_sv=args.reason_sv,
    )
    return res.model_dump()


def _h_send_sms(ctx: ToolContext, raw: dict[str, Any]) -> dict[str, Any]:
    args = SendSmsFollowupArgs.model_validate(raw)
    res: SendSmsFollowupResult = notification_service.send_sms(
        to_phone=args.to_phone, template=args.template, context_data=args.context_data
    )
    return res.model_dump()


def _h_photo_upload(ctx: ToolContext, raw: dict[str, Any]) -> dict[str, Any]:
    args = RequestPhotoUploadArgs.model_validate(raw)
    res: RequestPhotoUploadResult = notification_service.request_photo_upload(
        to_phone=args.to_phone,
        lead_or_customer_id=args.lead_or_customer_id,
        expires_hours=args.expires_hours,
    )
    return res.model_dump()


def _h_lookup_job_status(ctx: ToolContext, raw: dict[str, Any]) -> dict[str, Any]:
    args = LookupJobStatusArgs.model_validate(raw)
    return LookupJobStatusResult(
        found=False,
        summary_sv=f"Ingen aktiv arbetsorder hittad för kund {args.customer_id}.",
    ).model_dump()


def _h_check_rot(ctx: ToolContext, raw: dict[str, Any]) -> dict[str, Any]:
    args = CheckRotEligibilityArgs.model_validate(raw)
    res: CheckRotEligibilityResult = rot_service.assess(
        is_private_person=args.is_private_person,
        owns_property=args.owns_property,
        property_age_years=args.property_age_years,
        work_type=args.work_type,
    )
    return res.model_dump()


def _h_transfer_to_human(ctx: ToolContext, raw: dict[str, Any]) -> dict[str, Any]:
    args = TransferToHumanArgs.model_validate(raw)
    log.info("transfer.requested", target=args.target, summary=args.context_summary_sv)
    return TransferToHumanResult(transferred=False, target_phone=None).model_dump()


def _h_take_message(ctx: ToolContext, raw: dict[str, Any]) -> dict[str, Any]:
    args = TakeMessageArgs.model_validate(raw)
    log.info("message.taken", phone=args.caller_phone, urgency=args.urgency, topic=args.topic_sv)
    return TakeMessageResult(message_id=new_id(), forwarded_to_user_id=None).model_dump()


def _h_disable_recording(ctx: ToolContext, raw: dict[str, Any]) -> dict[str, Any]:
    args = DisableRecordingArgs.model_validate(raw)
    ctx.consent_disabled = True
    log.warning("consent.recording_disabled", call_id=ctx.call_id, reason=args.reason_sv)
    if ctx.call_id is not None:
        from svarsa.services import audit_service

        audit_service.record(
            ctx.session,
            actor="ai",
            action="recording.disabled",
            target_type="call",
            target_id=ctx.call_id,
            payload={"reason_sv": args.reason_sv},
        )
    return DisableRecordingResult(disabled=True).model_dump()


HANDLERS: dict[str, Handler] = {
    "lookup_customer": _h_lookup_customer,
    "triage_emergency": _h_triage_emergency,
    "check_availability": _h_check_availability,
    "book_appointment": _h_book_appointment,
    "create_lead": _h_create_lead,
    "escalate_to_owner": _h_escalate,
    "send_sms_followup": _h_send_sms,
    "request_photo_upload": _h_photo_upload,
    "lookup_job_status": _h_lookup_job_status,
    "check_rot_eligibility": _h_check_rot,
    "transfer_to_human": _h_transfer_to_human,
    "take_message": _h_take_message,
    "disable_recording_for_call": _h_disable_recording,
}


def dispatch(ctx: ToolContext, name: str, args: dict[str, Any]) -> dict[str, Any]:
    handler = HANDLERS.get(name)
    if handler is None:
        return {"error": f"unknown_tool:{name}"}
    started = time.perf_counter()
    error: str | None = None
    try:
        result = handler(ctx, args)
    except Exception as exc:  # noqa: BLE001
        log.exception("tool.error", name=name, args=args)
        result = {"error": str(exc)}
        error = str(exc)
    latency_ms = int((time.perf_counter() - started) * 1000)
    if ctx.call_id is not None:
        ctx.session.add(
            ToolInvocation(
                firma_id=ctx.firma_id,
                call_id=ctx.call_id,
                name=name,
                args=args,
                result=result,
                latency_ms=latency_ms,
                error=error,
            )
        )
        ctx.session.commit()
    log.info("tool.invoked", name=name, latency_ms=latency_ms, ok=error is None)
    return result

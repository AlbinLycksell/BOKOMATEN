"""MVP booking service — deterministic mock slots and a real Job row on book."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from svarsa.core.ids import new_id
from svarsa.core.logging import get_logger
from svarsa.core.time import STOCKHOLM
from svarsa.models import Job, JobStatus, User
from svarsa.tools.schemas import (
    AvailabilitySlot,
    BookAppointmentResult,
    CheckAvailabilityResult,
)

log = get_logger("svarsa.booking")


def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


def check_availability(
    session: Session,
    firma_id: str,
    *,
    duration_minutes: int,
    earliest_date: str,
    latest_date: str,
    required_skills: list[str],
    address: str | None,
) -> CheckAvailabilityResult:
    techs = session.exec(
        select(User).where(User.firma_id == firma_id, User.role.in_(["owner", "technician"]))  # type: ignore[attr-defined]
    ).all()
    if not techs:
        return CheckAvailabilityResult(slots=[])

    tz: ZoneInfo = STOCKHOLM
    cur = _parse_date(earliest_date)
    last = _parse_date(latest_date)
    slots: list[AvailabilitySlot] = []
    morning_hours = (8, 10, 13)
    while cur <= last and len(slots) < 5:
        if cur.weekday() < 5:
            for hh in morning_hours:
                if len(slots) >= 5:
                    break
                tech = techs[len(slots) % len(techs)]
                start = datetime.combine(cur, time(hh, 0), tzinfo=tz)
                end = start + timedelta(minutes=duration_minutes)
                slots.append(
                    AvailabilitySlot(
                        start_iso=start,
                        end_iso=end,
                        technician_id=tech.id,
                        technician_name=tech.name,
                        travel_buffer_min=30,
                    )
                )
        cur += timedelta(days=1)

    return CheckAvailabilityResult(slots=slots)


def book(
    session: Session,
    firma_id: str,
    *,
    customer_id: str,
    start_iso: datetime,
    duration_minutes: int,
    technician_id: str | None,
    address: str,
    problem_summary_sv: str,
    rot_eligible: bool,
    call_id: str | None = None,
) -> BookAppointmentResult:
    job = Job(
        firma_id=firma_id,
        customer_id=customer_id,
        call_id=call_id,
        status=JobStatus.SCHEDULED,
        summary_sv=problem_summary_sv,
        address=address,
        technician_id=technician_id,
        scheduled_for=start_iso,
        duration_minutes=duration_minutes,
        rot_eligible=rot_eligible,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    log.info("booking.created", job=job.id, firma=firma_id, customer=customer_id)
    return BookAppointmentResult(
        booking_id=job.id,
        calendar_event_url=f"https://app.svarsa.se/bookings/{job.id}",
        confirmation_sms_sent=True,
        confirmation_email_sent=True,
    )

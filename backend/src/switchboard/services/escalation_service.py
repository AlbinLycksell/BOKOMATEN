from __future__ import annotations

from sqlmodel import Session, select

from switchboard.core.logging import get_logger
from switchboard.models import Escalation, EscalationStatus, Severity, User
from switchboard.tools.schemas import EscalateToOwnerResult

log = get_logger("switchboard.escalation")


def escalate(
    session: Session,
    firma_id: str,
    call_id: str,
    *,
    severity: Severity,
    reason_sv: str,
) -> EscalateToOwnerResult:
    on_call = session.exec(
        select(User).where(User.firma_id == firma_id, User.on_call.is_(True))  # type: ignore[attr-defined]
    ).all()
    contacted = [u.phone for u in on_call if u.phone]
    user_ids = [u.id for u in on_call]

    esc = Escalation(
        firma_id=firma_id,
        call_id=call_id,
        severity=severity,
        reason_sv=reason_sv,
        contacted_user_ids=user_ids,
        status=EscalationStatus.CONTACTED if contacted else EscalationStatus.PENDING,
        next_in_chain_minutes=5,
    )
    session.add(esc)
    session.commit()
    session.refresh(esc)
    log.info(
        "escalation.fired",
        id=esc.id,
        firma=firma_id,
        severity=severity.value,
        contacted=len(contacted),
    )
    return EscalateToOwnerResult(
        escalation_id=esc.id,
        contacted=contacted,
        next_in_chain_minutes=esc.next_in_chain_minutes,
    )

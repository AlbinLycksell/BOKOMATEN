"""Append to AuditLog. Always tenant-scoped; refuses to write without context."""

from __future__ import annotations

from typing import Any

from sqlmodel import Session

from switchboard.core.logging import get_logger
from switchboard.core.tenant import require_firma_id
from switchboard.models import AuditAction, AuditActor, AuditLog, AuditTargetType

log = get_logger("switchboard.audit")


def record(
    session: Session,
    *,
    actor: AuditActor | str,
    action: AuditAction | str,
    target_type: AuditTargetType | str | None = None,
    target_id: str | None = None,
    payload: dict[str, Any] | None = None,
    firma_id: str | None = None,
) -> AuditLog:
    fid = firma_id or require_firma_id()
    row = AuditLog(
        firma_id=fid,
        actor=str(actor),
        action=str(action),
        target_type=str(target_type) if target_type is not None else None,
        target_id=target_id,
        payload=payload or {},
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    log.info(
        "audit.recorded",
        action=str(action),
        actor=str(actor),
        target_type=str(target_type) if target_type is not None else None,
        target_id=target_id,
    )
    return row

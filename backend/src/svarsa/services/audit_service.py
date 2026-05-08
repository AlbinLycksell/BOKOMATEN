"""Append to AuditLog. Always tenant-scoped; refuses to write without context."""

from __future__ import annotations

from typing import Any

from sqlmodel import Session

from svarsa.core.logging import get_logger
from svarsa.core.tenant import require_firma_id
from svarsa.models import AuditLog

log = get_logger("svarsa.audit")


def record(
    session: Session,
    *,
    actor: str,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    payload: dict[str, Any] | None = None,
    firma_id: str | None = None,
) -> AuditLog:
    fid = firma_id or require_firma_id()
    row = AuditLog(
        firma_id=fid,
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=target_id,
        payload=payload or {},
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    log.info(
        "audit.recorded",
        action=action,
        actor=actor,
        target_type=target_type,
        target_id=target_id,
    )
    return row

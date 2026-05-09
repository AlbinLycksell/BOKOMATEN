"""Träna AI — owner-driven feedback that adjusts the firma persona prompt.

PRD §7.7: "Träna AI"-knapp. The owner reviews a call, marks something the
AI got wrong, and types a correction. The text appends to
`Firma.settings.persona_corrections` and is woven into the next system prompt
build at call connect.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session

from svarsa.api.deps import get_current_firma, get_db
from svarsa.core.logging import get_logger
from svarsa.core.tenant import firma_context
from svarsa.core.time import utcnow
from svarsa.models import Call, Firma, FirmaSettings
from svarsa.services import audit_service

router = APIRouter(prefix="/api/calls", tags=["training"])
log = get_logger("svarsa.training")

_MAX_CORRECTIONS = 50


class CorrectionRequest(BaseModel):
    correction_sv: str = Field(min_length=4, max_length=500)
    label: str = Field(default="general", max_length=40)


class CorrectionResponse(BaseModel):
    accepted: bool
    total_corrections: int


@router.post("/{call_id}/train", response_model=CorrectionResponse)
def submit_correction(
    call_id: str,
    payload: CorrectionRequest,
    firma: Annotated[Firma, Depends(get_current_firma)],
    db: Annotated[Session, Depends(get_db)],
) -> CorrectionResponse:
    call = db.get(Call, call_id)
    if call is None or call.firma_id != firma.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="call_not_found")

    settings = FirmaSettings.model_validate(firma.settings or {})
    corrections = list(settings.persona_corrections or [])
    entry = f"[{payload.label}] {payload.correction_sv.strip()}"
    if entry in corrections:
        return CorrectionResponse(accepted=True, total_corrections=len(corrections))
    corrections.append(entry)
    if len(corrections) > _MAX_CORRECTIONS:
        corrections = corrections[-_MAX_CORRECTIONS:]
    settings.persona_corrections = corrections
    firma.settings = settings.model_dump()
    firma.updated_at = utcnow()
    db.add(firma)
    db.commit()

    with firma_context(firma.id):
        audit_service.record(
            db,
            actor="owner",
            action="training.correction",
            target_type="call",
            target_id=call_id,
            payload={"correction_sv": payload.correction_sv, "label": payload.label},
        )

    log.info("training.correction.added", firma=firma.id, total=len(corrections))
    return CorrectionResponse(accepted=True, total_corrections=len(corrections))

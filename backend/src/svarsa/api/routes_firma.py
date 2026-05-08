from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from svarsa.api.deps import get_current_firma, get_db
from svarsa.core.time import utcnow
from svarsa.models import Firma, FirmaRead, FirmaSettings, FirmaSettingsUpdate

router = APIRouter(prefix="/api/firma/me", tags=["firma"])


def _to_read(firma: Firma) -> FirmaRead:
    return FirmaRead(
        id=firma.id,
        name=firma.name,
        org_number=firma.org_number,
        trade=firma.trade,
        plan=firma.plan,
        locality=firma.locality,
        settings=FirmaSettings.model_validate(firma.settings or {}),
        created_at=firma.created_at,
    )


@router.get("", response_model=FirmaRead)
def get_me(firma: Annotated[Firma, Depends(get_current_firma)]) -> FirmaRead:
    return _to_read(firma)


@router.put("/settings", response_model=FirmaRead)
def update_settings(
    payload: FirmaSettingsUpdate,
    firma: Annotated[Firma, Depends(get_current_firma)],
    db: Annotated[Session, Depends(get_db)],
) -> FirmaRead:
    current = FirmaSettings.model_validate(firma.settings or {})
    merged = current.model_copy(update={k: v for k, v in payload.model_dump().items() if v is not None})
    firma.settings = merged.model_dump()
    firma.updated_at = utcnow()
    db.add(firma)
    db.commit()
    db.refresh(firma)
    return _to_read(firma)

"""Integration OAuth callbacks + status endpoints."""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlmodel import Session

from svarsa.api.deps import get_current_firma, get_db
from svarsa.core.config import get_settings
from svarsa.core.logging import get_logger
from svarsa.integrations import fortnox
from svarsa.models import Firma, Integration, IntegrationType

router = APIRouter(prefix="/api/integrations", tags=["integrations"])
log = get_logger("svarsa.integrations.api")

# In-memory state store keyed by `state` parameter. Production swaps this
# for a Redis/SQL-backed store with a 5-min TTL — for MVP single-instance
# Cloud Run, in-memory is fine.
_oauth_state: dict[str, str] = {}


class IntegrationStatus(BaseModel):
    type: str
    connected: bool


@router.get("/fortnox/connect")
def fortnox_connect(
    firma: Annotated[Firma, Depends(get_current_firma)],
) -> RedirectResponse:
    settings = get_settings()
    if not settings.fortnox_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="fortnox_not_configured",
        )
    state = secrets.token_urlsafe(24)
    _oauth_state[state] = firma.id
    url = fortnox.authorize_url(
        client_id=settings.fortnox_client_id,
        redirect_uri=settings.fortnox_redirect_uri,
        state=state,
    )
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/fortnox/callback")
def fortnox_callback(
    db: Annotated[Session, Depends(get_db)],
    code: str = Query(...),
    state: str = Query(...),
) -> RedirectResponse:
    firma_id = _oauth_state.pop(state, None)
    if firma_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_state",
        )
    settings = get_settings()
    tokens = fortnox.exchange_code(
        code,
        client_id=settings.fortnox_client_id,
        client_secret=settings.fortnox_client_secret,
        redirect_uri=settings.fortnox_redirect_uri,
    )
    fortnox.store_tokens(db, firma_id, tokens, settings=settings)
    log.info("fortnox.connected", firma=firma_id)
    return RedirectResponse(
        url="/settings?integration=fortnox&status=ok",
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/fortnox/sync")
def fortnox_sync(
    firma: Annotated[Firma, Depends(get_current_firma)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, int]:
    with fortnox.FortnoxClient(db, firma.id) as client:
        pulled = fortnox.sync_customers_to_local(client)
    return {"customers_pulled": pulled}


@router.get("/status", response_model=list[IntegrationStatus])
def list_status(
    firma: Annotated[Firma, Depends(get_current_firma)],
    db: Annotated[Session, Depends(get_db)],
) -> list[IntegrationStatus]:
    rows = db.query(Integration).filter(Integration.firma_id == firma.id).all()
    by_type: dict[str, bool] = {r.type.value: r.connected for r in rows}
    return [
        IntegrationStatus(type=t.value, connected=by_type.get(t.value, False))
        for t in IntegrationType
    ]

"""Integration OAuth callbacks + status endpoints."""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlmodel import Session

from switchboard.api.deps import get_current_firma, get_db
from switchboard.core.config import get_settings
from switchboard.core.logging import get_logger
from switchboard.integrations import fortnox, google_calendar, visma_eekonomi
from switchboard.models import Firma, Integration, IntegrationType

router = APIRouter(prefix="/api/integrations", tags=["integrations"])
log = get_logger("switchboard.integrations.api")

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


@router.get("/visma/connect")
def visma_connect(
    firma: Annotated[Firma, Depends(get_current_firma)],
) -> RedirectResponse:
    settings = get_settings()
    if not settings.visma_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="visma_not_configured",
        )
    state = secrets.token_urlsafe(24)
    _oauth_state[state] = firma.id
    url = visma_eekonomi.authorize_url(
        client_id=settings.visma_client_id,
        redirect_uri=settings.visma_redirect_uri,
        state=state,
    )
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/visma/callback")
def visma_callback(
    db: Annotated[Session, Depends(get_db)],
    code: str = Query(...),
    state: str = Query(...),
) -> RedirectResponse:
    firma_id = _oauth_state.pop(state, None)
    if firma_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_state")
    settings = get_settings()
    tokens = visma_eekonomi.exchange_code(
        code,
        client_id=settings.visma_client_id,
        client_secret=settings.visma_client_secret,
        redirect_uri=settings.visma_redirect_uri,
    )
    visma_eekonomi.store_tokens(db, firma_id, tokens, settings=settings)
    return RedirectResponse(
        url="/settings?integration=visma&status=ok",
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/google-calendar/connect")
def gcal_connect(
    firma: Annotated[Firma, Depends(get_current_firma)],
) -> RedirectResponse:
    settings = get_settings()
    if not settings.google_oauth_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="google_oauth_not_configured",
        )
    state = secrets.token_urlsafe(24)
    _oauth_state[state] = firma.id
    url = google_calendar.authorize_url(
        client_id=settings.google_oauth_client_id,
        redirect_uri=settings.google_calendar_redirect_uri,
        state=state,
    )
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/google-calendar/callback")
def gcal_callback(
    db: Annotated[Session, Depends(get_db)],
    code: str = Query(...),
    state: str = Query(...),
) -> RedirectResponse:
    firma_id = _oauth_state.pop(state, None)
    if firma_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_state")
    settings = get_settings()
    tokens = google_calendar.exchange_code(
        code,
        client_id=settings.google_oauth_client_id,
        client_secret=settings.google_oauth_client_secret,
        redirect_uri=settings.google_calendar_redirect_uri,
    )
    google_calendar.store_tokens(db, firma_id, tokens, settings=settings)
    return RedirectResponse(
        url="/settings?integration=google_calendar&status=ok",
        status_code=status.HTTP_302_FOUND,
    )


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

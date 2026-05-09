"""Tool dispatch endpoint — called by the Realtime Bridge in prod (separate service).

Authentication is by `X-Internal-Token` (shared with the Bridge's deploy)
PLUS the standard `X-Firma-Id` header bound by `TenantMiddleware`. The
internal token is rotated independently from customer credentials.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from switchboard.api.deps import get_current_firma, get_db
from switchboard.core.config import get_settings
from switchboard.models import Firma
from switchboard.tools.handlers import ToolContext, dispatch

router = APIRouter(prefix="/api/tools", tags=["tools"])


class DispatchRequest(BaseModel):
    call_id: str | None = None
    name: str
    args: dict[str, Any] = {}


class DispatchResponse(BaseModel):
    result: dict[str, Any]


def _verify_internal_token(
    x_internal_token: Annotated[str | None, Header(alias="X-Internal-Token")] = None,
) -> None:
    expected = get_settings().bridge_internal_token
    if not expected:
        return  # dev: token not configured, allow
    if x_internal_token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_internal_token"
        )


@router.post("/dispatch", response_model=DispatchResponse)
def dispatch_tool(
    payload: DispatchRequest,
    firma: Annotated[Firma, Depends(get_current_firma)],
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(_verify_internal_token)] = None,
) -> DispatchResponse:
    ctx = ToolContext(session=db, firma_id=firma.id, call_id=payload.call_id)
    result = dispatch(ctx, payload.name, payload.args)
    return DispatchResponse(result=result)

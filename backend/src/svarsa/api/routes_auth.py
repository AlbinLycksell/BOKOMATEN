"""Auth bootstrap endpoint — called by NextAuth on first sign-in.

The web layer's NextAuth `jwt` callback receives the Google `sub` and
`email`. It POSTs them here, we resolve (or create) the matching User +
Firma, and return the `firma_id` + `role` that NextAuth then stamps into
the JWT. Subsequent backend requests verify that JWT via
`core.auth.verify_jwt`.

Authentication: `X-Internal-Token` shared with the web app. The endpoint
is firewalled to the VPC connector in production.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlmodel import Session

from svarsa.api.deps import get_db
from svarsa.core.config import get_settings
from svarsa.services.onboarding_service import (
    SignupNotAllowed,
    bootstrap_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class BootstrapRequest(BaseModel):
    google_sub: str
    email: EmailStr
    name: str | None = None


class BootstrapResponse(BaseModel):
    user_id: str
    firma_id: str
    role: str
    created_firma: bool


def _verify_internal_token(
    x_internal_token: Annotated[str | None, Header(alias="X-Internal-Token")] = None,
) -> None:
    expected = get_settings().bootstrap_internal_token
    if not expected:
        return  # dev: token not configured, allow
    if x_internal_token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_internal_token",
        )


@router.post("/bootstrap", response_model=BootstrapResponse)
def bootstrap(
    payload: BootstrapRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(_verify_internal_token)] = None,
) -> BootstrapResponse:
    try:
        result = bootstrap_user(
            db,
            google_sub=payload.google_sub,
            email=str(payload.email),
            name=payload.name,
        )
    except SignupNotAllowed as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return BootstrapResponse(
        user_id=result.user_id,
        firma_id=result.firma_id,
        role=result.role,
        created_firma=result.created_firma,
    )

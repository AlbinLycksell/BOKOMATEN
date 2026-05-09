from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from switchboard.core.config import Settings, get_settings

router = APIRouter(tags=["meta"])


class HealthResponse(BaseModel):
    status: str
    env: str
    version: str


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings: Settings = get_settings()
    return HealthResponse(status="ok", env=settings.env, version=settings.version)

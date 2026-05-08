"""Realtime Bridge — separate FastAPI factory for independent deploy (PRD §8.10).

Production: this runs as its own Cloud Run service with min-instances ≥ 2,
60 min request timeout, weekly Sunday-04:00-CET deploys with traffic-split
canary. Tool calls go to the Application Backend over the VPC connector,
not over public internet — Settings.tool_dispatch_mode = "http".

Dev: a single `uvicorn svarsa.app:create_app --factory` already exposes
the bridge at the same /ws/bridge/... endpoint via the umbrella factory.
This module is for the prod-shape topology and to keep the deploy
boundary unambiguous in code.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from svarsa import __version__
from svarsa.api import routes_health
from svarsa.bridge import ws as bridge_ws
from svarsa.core.config import get_settings
from svarsa.core.logging import configure_logging, get_logger
from svarsa.core.middleware import TenantMiddleware
from svarsa.db.session import init_db

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@asynccontextmanager
async def _lifespan(app: FastAPI) -> "AsyncIterator[None]":
    settings = get_settings()
    configure_logging(settings)
    log = get_logger("svarsa.bridge_app")
    log.info(
        "bridge.startup",
        env=settings.env,
        version=__version__,
        dispatch_mode=settings.tool_dispatch_mode,
        backend=settings.application_backend_url,
    )
    init_db()
    yield
    log.info("bridge.shutdown")


def create_bridge_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Svarsa Realtime Bridge",
        version=__version__,
        lifespan=_lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TenantMiddleware)
    app.include_router(routes_health.router)
    app.include_router(bridge_ws.router)
    return app

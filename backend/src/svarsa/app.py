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
from svarsa.db.session import init_db

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@asynccontextmanager
async def _lifespan(app: FastAPI) -> "AsyncIterator[None]":
    settings = get_settings()
    configure_logging(settings)
    log = get_logger("svarsa.app")
    log.info("startup", env=settings.env, version=__version__)
    init_db()
    if settings.seed_dev_data and settings.env == "dev":
        from svarsa.db.seed import seed_dev_data

        seed_dev_data()
    yield
    log.info("shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Svarsa API",
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
    app.include_router(routes_health.router)
    app.include_router(bridge_ws.router)
    return app

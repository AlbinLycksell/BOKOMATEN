from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from switchboard import __version__
from switchboard.api import (
    routes_admin,
    routes_auth,
    routes_billing,
    routes_calls,
    routes_customers,
    routes_firma,
    routes_health,
    routes_integrations,
    routes_metrics,
    routes_tools,
    routes_training,
    ws_inbox,
)
from switchboard.bridge import ws as bridge_ws
from switchboard.core.config import get_settings
from switchboard.core.logging import configure_logging, get_logger
from switchboard.core.middleware import TenantMiddleware
from switchboard.db.seed import DEMO_FIRMA_ID
from switchboard.db.session import init_db
from switchboard.integrations import elks_voice

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@asynccontextmanager
async def _lifespan(app: FastAPI) -> "AsyncIterator[None]":
    settings = get_settings()
    configure_logging(settings)
    log = get_logger("switchboard.app")
    log.info("startup", env=settings.env, version=__version__)
    if settings.sentry_dsn:
        try:
            import sentry_sdk

            sentry_sdk.init(
                dsn=settings.sentry_dsn,
                environment=settings.sentry_environment or settings.env,
                traces_sample_rate=0.1,
                send_default_pii=False,
            )
        except Exception:  # noqa: BLE001
            log.exception("sentry.init_failed")
    init_db()
    if settings.seed_dev_data and settings.env == "dev":
        from switchboard.db.seed import seed_dev_data

        seed_dev_data()
    yield
    log.info("shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Switchboard API",
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
    app.add_middleware(
        TenantMiddleware,
        default_firma_id=DEMO_FIRMA_ID if settings.env == "dev" else None,
    )
    app.include_router(routes_health.router)
    app.include_router(routes_auth.router)
    app.include_router(routes_calls.router)
    app.include_router(routes_customers.router)
    app.include_router(routes_firma.router)
    app.include_router(routes_tools.router)
    app.include_router(routes_integrations.router)
    app.include_router(routes_billing.router)
    app.include_router(routes_training.router)
    app.include_router(routes_metrics.router)
    app.include_router(routes_admin.router)
    app.include_router(elks_voice.router)
    app.include_router(ws_inbox.router)
    app.include_router(bridge_ws.router)
    return app

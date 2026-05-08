from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, event, text
from sqlmodel import Session, SQLModel, create_engine

from svarsa.core.config import Settings, get_settings
from svarsa.core.tenant import get_firma_id

_engine: Engine | None = None


def _build_engine(settings: Settings) -> Engine:
    if settings.database_url.startswith("sqlite"):
        engine = create_engine(
            settings.database_url,
            echo=False,
            connect_args={"check_same_thread": False},
        )
    else:
        engine = create_engine(
            settings.database_url,
            echo=False,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_pool_max_overflow,
            pool_pre_ping=True,
        )
        _attach_tenant_session_var(engine)
    return engine


def _attach_tenant_session_var(engine: Engine) -> None:
    """Set the Postgres `app.firma_id` session variable on each connection checkout.

    The RLS policies installed by the initial Alembic migration use
    `current_setting('app.firma_id', true)` to scope every tenant table.
    """

    @event.listens_for(engine, "checkout")
    def _on_checkout(dbapi_connection, connection_record, connection_proxy):  # type: ignore[no-untyped-def]
        firma_id = get_firma_id()
        if firma_id is None:
            return
        with dbapi_connection.cursor() as cur:
            cur.execute("SELECT set_config('app.firma_id', %s, false)", (firma_id,))


def get_engine(settings: Settings | None = None) -> Engine:
    global _engine
    if _engine is None:
        s = settings or get_settings()
        _engine = _build_engine(s)
    return _engine


def reset_engine() -> None:
    """For tests that change DATABASE_URL between fixtures."""
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None


def init_db() -> None:
    """Dev-only schema bootstrap. Production uses Alembic migrations."""
    from svarsa import models  # noqa: F401

    settings = get_settings()
    if settings.is_postgres:
        # In production we run migrations via `alembic upgrade head` in CI,
        # not from the running app. Skip create_all to avoid drift.
        return
    SQLModel.metadata.create_all(get_engine())


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session


def healthcheck_db() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001
        return False

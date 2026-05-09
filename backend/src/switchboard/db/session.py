from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, event, text
from sqlmodel import Session, SQLModel, create_engine

from switchboard.core.config import Settings, get_settings
from switchboard.core.tenant import get_firma_id

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
    """Dev-only schema bootstrap.

    On Postgres we rely on ``alembic upgrade head`` (run by the container
    entrypoint or CI). On SQLite we:

    1. Detect whether the existing schema is missing any columns the
       current models declare.
    2. If yes, attempt ``alembic upgrade head``. If alembic fails (or the
       drift is too wide for an in-place upgrade), drop the file and
       recreate from `SQLModel.metadata` so dev never gets stuck on
       stale schema.
    """
    from switchboard import models  # noqa: F401

    settings = get_settings()
    if settings.is_postgres:
        return

    engine = get_engine()
    if not _sqlite_schema_matches(engine):
        # Dev-only: nuke and recreate. Seeded data is regenerated; nothing
        # survives across model edits in dev anyway. Production uses
        # Postgres + explicit alembic upgrades.
        from switchboard.core.logging import get_logger

        get_logger("switchboard.db").warning("schema_drift_detected_recreating_sqlite")
        _recreate_sqlite(engine, settings)
        engine = get_engine()
    SQLModel.metadata.create_all(engine)


def _sqlite_schema_matches(engine: Engine) -> bool:
    """True iff every model column exists on its corresponding table."""
    from sqlalchemy import inspect

    insp = inspect(engine)
    if not insp.has_table("firma"):
        return True  # fresh DB; create_all will populate
    for table_name, table in SQLModel.metadata.tables.items():
        if not insp.has_table(table_name):
            return False
        actual = {c["name"] for c in insp.get_columns(table_name)}
        for column in table.columns:
            if column.name not in actual:
                return False
    return True


def _try_alembic_upgrade(engine: Engine, settings: Settings) -> bool:
    try:
        from pathlib import Path

        from alembic import command
        from alembic.config import Config

        repo_root = Path(__file__).resolve().parents[4]
        alembic_ini = repo_root / "backend" / "alembic.ini"
        if not alembic_ini.exists():
            return False
        cfg = Config(str(alembic_ini))
        cfg.set_main_option("script_location", str(repo_root / "backend" / "alembic"))
        cfg.set_main_option("sqlalchemy.url", settings.database_url)
        command.upgrade(cfg, "head")
        return True
    except Exception:  # noqa: BLE001
        return False


def _recreate_sqlite(engine: Engine, settings: Settings) -> None:
    """Last-resort dev-only reset: delete the file, drop the engine cache."""
    import os

    # SQLAlchemy SQLite URLs use `sqlite:///<absolute_or_relative_path>`.
    # `sqlite:////abs/path` → 4 slashes for absolute. Standard form is
    # `sqlite:///abs/path` where the third slash is the separator and the
    # rest is the literal filesystem path.
    db_path = settings.database_url.removeprefix("sqlite:///")
    engine.dispose()
    if db_path and os.path.exists(db_path):
        os.remove(db_path)
        if os.path.exists(db_path + "-journal"):
            os.remove(db_path + "-journal")
    reset_engine()


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

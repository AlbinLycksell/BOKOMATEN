from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

from svarsa.core.config import Settings, get_settings

_engine: Engine | None = None


def get_engine(settings: Settings | None = None) -> Engine:
    global _engine
    if _engine is None:
        s = settings or get_settings()
        connect_args = {"check_same_thread": False} if s.database_url.startswith("sqlite") else {}
        _engine = create_engine(s.database_url, echo=False, connect_args=connect_args)
    return _engine


def init_db() -> None:
    from svarsa import models  # noqa: F401  (register tables on import)

    SQLModel.metadata.create_all(get_engine())


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session

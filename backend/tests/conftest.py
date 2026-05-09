from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _isolate_db() -> Iterator[None]:
    tmpdir = tempfile.mkdtemp(prefix="svarsa-test-")
    db_path = Path(tmpdir) / "test.db"
    os.environ["SVARSA_DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["SVARSA_ENV"] = "dev"
    os.environ["SVARSA_SEED_DEV_DATA"] = "true"
    os.environ["SVARSA_LOG_LEVEL"] = "WARNING"
    from svarsa.core.config import get_settings

    get_settings.cache_clear()
    from svarsa.db import session as db_session

    db_session.reset_engine()
    db_session.init_db()
    yield

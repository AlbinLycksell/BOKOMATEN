"""Tenant context propagation per PRD §8.9.

Every authenticated request resolves to one `firma_id`. We bind it as a
`contextvars.ContextVar` so:

- structlog auto-merges it into every log line (via `merge_contextvars`)
- Background tasks inherit it across `asyncio.create_task` boundaries
- Helpers can `require_firma_id()` to refuse unscoped operations

For Postgres-backed deploys we additionally `SET app.firma_id = ...` per
connection in `db/session.set_postgres_tenant()` so row-level security
policies kick in.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

import structlog

_firma_id_var: ContextVar[str | None] = ContextVar("switchboard_firma_id", default=None)


def get_firma_id() -> str | None:
    return _firma_id_var.get()


def require_firma_id() -> str:
    value = _firma_id_var.get()
    if value is None:
        msg = "tenant context not set — cannot perform tenant-scoped operation"
        raise RuntimeError(msg)
    return value


@contextmanager
def firma_context(firma_id: str) -> Iterator[None]:
    """Bind a tenant scope for the duration of the with-block."""
    log_token = structlog.contextvars.bind_contextvars(firma_id=firma_id)
    var_token = _firma_id_var.set(firma_id)
    try:
        yield
    finally:
        _firma_id_var.reset(var_token)
        # bind_contextvars returned a token-style mapping; clear specifically.
        structlog.contextvars.unbind_contextvars("firma_id")
        del log_token

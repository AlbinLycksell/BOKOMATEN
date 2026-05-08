"""FastAPI middleware that resolves and binds the tenant scope per request."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from svarsa.core.tenant import firma_context

DEV_FIRMA_HEADER = "X-Firma-Id"


class TenantMiddleware(BaseHTTPMiddleware):
    """Dev-mode auth shim: read X-Firma-Id and bind it. Replace with OAuth in Phase 1."""

    def __init__(self, app, default_firma_id: str | None = None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.default_firma_id = default_firma_id

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        firma_id = request.headers.get(DEV_FIRMA_HEADER) or self.default_firma_id
        if firma_id is None:
            return await call_next(request)
        with firma_context(firma_id):
            return await call_next(request)

"""FastAPI middleware that resolves and binds the tenant scope per request.

Two paths:

- ``Settings.auth_mode == "dev_header"`` — reads ``X-Firma-Id``. Used for
  local dev and the bridge ↔ backend internal call (with the
  ``X-Internal-Token`` denyability gate elsewhere).
- ``Settings.auth_mode == "jwks"`` — reads a Bearer JWT, verifies via
  NextAuth JWKS, extracts ``firma_id`` from the verified claim. The
  ``X-Firma-Id`` header is ignored on JWKS paths to prevent spoofing.

Routes that don't require a firma scope (``/health``, ``/api/auth/*``,
the ``/ws/*`` paths which authenticate inline) are skipped.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from switchboard.core.auth import AuthError, verify_jwt
from switchboard.core.config import Settings, get_settings
from switchboard.core.constants import BEARER_PREFIX, HttpHeader
from switchboard.core.logging import get_logger
from switchboard.core.tenant import firma_context
from switchboard.models import AuthMode

log = get_logger("switchboard.middleware")

SKIP_PATH_PREFIXES = ("/health", "/api/auth", "/ws/")


class TenantMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,  # type: ignore[no-untyped-def]
        *,
        default_firma_id: str | None = None,
        settings: Settings | None = None,
    ) -> None:
        super().__init__(app)
        self.default_firma_id = default_firma_id
        self.settings = settings or get_settings()

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        path = request.url.path
        if any(path.startswith(p) for p in SKIP_PATH_PREFIXES):
            return await call_next(request)

        firma_id = self._resolve_firma_id(request)
        if firma_id is None:
            return await call_next(request)
        with firma_context(firma_id):
            return await call_next(request)

    def _resolve_firma_id(self, request: Request) -> str | None:
        if self.settings.auth_mode is AuthMode.JWKS:
            auth = request.headers.get(HttpHeader.AUTHORIZATION, "")
            if not auth.startswith(BEARER_PREFIX):
                return None
            token = auth.removeprefix(BEARER_PREFIX).strip()
            try:
                ctx = verify_jwt(token, self.settings)
                return ctx.firma_id
            except AuthError as exc:
                log.warning("auth.rejected", reason=str(exc))
                return None
        return request.headers.get(HttpHeader.FIRMA_ID) or self.default_firma_id

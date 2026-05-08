"""JWT verification for production auth.

Production path: NextAuth (web) issues a JWT signed with RS256, exposes
JWKS at ``${NEXTAUTH_URL}/api/auth/jwks``. Backend verifies the token,
extracts the ``firma_id`` claim (stamped by the NextAuth ``jwt`` callback),
binds it via ``firma_context``.

Dev path: ``Settings.auth_mode == "dev_header"`` reads the ``X-Firma-Id``
header — useful for local testing without spinning up the full auth flow.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import jwt
from jwt import PyJWKClient

from svarsa.core.config import Settings, get_settings


class AuthError(Exception):
    pass


@dataclass(frozen=True)
class AuthContext:
    user_id: str
    firma_id: str
    email: str | None
    role: str | None


@lru_cache(maxsize=1)
def _jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url, cache_keys=True, lifespan=600)


def verify_jwt(token: str, settings: Settings | None = None) -> AuthContext:
    s = settings or get_settings()
    if not s.auth_jwks_url:
        msg = "auth.jwks_url not configured"
        raise AuthError(msg)
    try:
        signing_key = _jwks_client(s.auth_jwks_url).get_signing_key_from_jwt(token).key
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256", "ES256"],
            audience=s.auth_audience,
            issuer=s.auth_issuer,
        )
    except jwt.InvalidTokenError as exc:  # noqa: F821
        raise AuthError(f"invalid_token:{exc.__class__.__name__}") from exc
    firma_id = payload.get("firma_id")
    if not firma_id:
        raise AuthError("missing_firma_id_claim")
    return AuthContext(
        user_id=str(payload.get("sub", "")),
        firma_id=str(firma_id),
        email=payload.get("email"),
        role=payload.get("role"),
    )

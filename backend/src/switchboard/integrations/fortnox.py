"""Fortnox API client (https://apps.fortnox.se/apidocs).

OAuth 2.0 Authorization Code flow:
- ``GET https://apps.fortnox.se/oauth-v1/auth`` — user-facing consent page.
- ``POST https://apps.fortnox.se/oauth-v1/token`` — code → tokens.
- Tokens: access expires in 1h, refresh valid 45 days. Each refresh
  rotates both — store the new pair atomically.

API:
- Base: ``https://api.fortnox.se/3/``
- Bearer auth via ``Authorization: Bearer <access>``.
- Customer endpoint: ``GET/POST /3/customers/?CustomerNumber=…``
- Booking calendar: ``GET/POST /3/bookings/`` (Hantverksdata-style projektkalender; available
  on Pro plan).
- Invoices (read-only here): ``GET /3/invoices/``

Storage: encrypted refresh tokens in `Integration.sync_state`. Per
PRD §8.9 we use a per-tenant DEK for credentials at rest — wrapped here
behind `_encrypt`/`_decrypt`. In dev, those are no-ops; production uses
Cloud KMS via the application service account.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx
from sqlmodel import Session, select

from switchboard.core.config import Settings, get_settings
from switchboard.core.logging import get_logger
from switchboard.core.tenant import require_firma_id
from switchboard.core.time import utcnow
from switchboard.models import Customer, CustomerType, Integration, IntegrationType

log = get_logger("switchboard.fortnox")

AUTH_URL = "https://apps.fortnox.se/oauth-v1/auth"
TOKEN_URL = "https://apps.fortnox.se/oauth-v1/token"
API_BASE = "https://api.fortnox.se/3"
DEFAULT_SCOPES = ("companyinformation", "customer", "invoice", "bookkeeping", "settings")


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_at: int  # unix epoch seconds


def authorize_url(*, client_id: str, redirect_uri: str, state: str, scopes: tuple[str, ...] = DEFAULT_SCOPES) -> str:
    from urllib.parse import urlencode

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(scopes),
        "state": state,
        "access_type": "offline",
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code(
    code: str,
    *,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> TokenPair:
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(
            TOKEN_URL,
            auth=(client_id, client_secret),
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        body = resp.json()
        return TokenPair(
            access_token=body["access_token"],
            refresh_token=body["refresh_token"],
            expires_at=int(time.time()) + int(body.get("expires_in", 3600)) - 30,
        )


def refresh_token(
    refresh: str,
    *,
    client_id: str,
    client_secret: str,
) -> TokenPair:
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(
            TOKEN_URL,
            auth=(client_id, client_secret),
            data={"grant_type": "refresh_token", "refresh_token": refresh},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        body = resp.json()
        return TokenPair(
            access_token=body["access_token"],
            refresh_token=body["refresh_token"],
            expires_at=int(time.time()) + int(body.get("expires_in", 3600)) - 30,
        )


# --- Token storage ---


def _encrypt(plain: str, settings: Settings) -> str:
    """Wrap a refresh token. Production: Cloud KMS encrypt+base64. Dev: no-op."""
    if settings.storage_mode == "gcs" and settings.gcp_project:
        try:
            return _kms_encrypt(plain, settings)
        except Exception:  # noqa: BLE001
            log.exception("fortnox.token.kms_encrypt_failed")
    return f"plaintext:{plain}"


def _decrypt(blob: str, settings: Settings) -> str:
    if blob.startswith("plaintext:"):
        return blob.removeprefix("plaintext:")
    try:
        return _kms_decrypt(blob, settings)
    except Exception:  # noqa: BLE001
        log.exception("fortnox.token.kms_decrypt_failed")
        msg = "fortnox_token_decrypt_failed"
        raise RuntimeError(msg) from None


def _kms_encrypt(plain: str, settings: Settings) -> str:
    import base64

    from google.cloud import kms  # type: ignore[attr-defined]

    client = kms.KeyManagementServiceClient()
    firma_id = require_firma_id().lower()
    key_name = (
        f"projects/{settings.gcp_project}/locations/{settings.kms_location}"
        f"/keyRings/{settings.kms_keyring}/cryptoKeys/firma-{firma_id}"
    )
    encoded = client.encrypt(
        request={"name": key_name, "plaintext": plain.encode()}
    ).ciphertext
    return "kms:" + base64.b64encode(encoded).decode()


def _kms_decrypt(blob: str, settings: Settings) -> str:
    import base64

    from google.cloud import kms  # type: ignore[attr-defined]

    client = kms.KeyManagementServiceClient()
    firma_id = require_firma_id().lower()
    key_name = (
        f"projects/{settings.gcp_project}/locations/{settings.kms_location}"
        f"/keyRings/{settings.kms_keyring}/cryptoKeys/firma-{firma_id}"
    )
    raw = base64.b64decode(blob.removeprefix("kms:"))
    out = client.decrypt(request={"name": key_name, "ciphertext": raw})
    return out.plaintext.decode()


def store_tokens(
    session: Session,
    firma_id: str,
    tokens: TokenPair,
    *,
    settings: Settings | None = None,
) -> Integration:
    s = settings or get_settings()
    integ = session.exec(
        select(Integration).where(
            Integration.firma_id == firma_id,
            Integration.type == IntegrationType.FORTNOX,
        )
    ).first()
    state = {
        "access_token": tokens.access_token,
        "refresh_token_encrypted": _encrypt(tokens.refresh_token, s),
        "expires_at": tokens.expires_at,
        "updated_at": utcnow().isoformat(),
    }
    if integ is None:
        integ = Integration(
            firma_id=firma_id,
            type=IntegrationType.FORTNOX,
            connected=True,
            sync_state=state,
        )
    else:
        integ.connected = True
        integ.sync_state = state
    session.add(integ)
    session.commit()
    session.refresh(integ)
    return integ


def load_tokens(session: Session, firma_id: str, settings: Settings | None = None) -> TokenPair | None:
    s = settings or get_settings()
    integ = session.exec(
        select(Integration).where(
            Integration.firma_id == firma_id,
            Integration.type == IntegrationType.FORTNOX,
        )
    ).first()
    if integ is None or not integ.connected:
        return None
    state = integ.sync_state or {}
    access = state.get("access_token") or ""
    encrypted = state.get("refresh_token_encrypted") or ""
    if not access or not encrypted:
        return None
    return TokenPair(
        access_token=access,
        refresh_token=_decrypt(encrypted, s),
        expires_at=int(state.get("expires_at", 0)),
    )


# --- API client ---


class FortnoxClient:
    """Thin typed wrapper. Handles transparent token refresh on 401."""

    def __init__(
        self,
        session: Session,
        firma_id: str,
        *,
        settings: Settings | None = None,
        http: httpx.Client | None = None,
    ) -> None:
        self.session = session
        self.firma_id = firma_id
        self.settings = settings or get_settings()
        self._http = http or httpx.Client(timeout=10.0, base_url=API_BASE)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "FortnoxClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _tokens(self) -> TokenPair:
        tokens = load_tokens(self.session, self.firma_id, self.settings)
        if tokens is None:
            msg = "fortnox_not_connected"
            raise RuntimeError(msg)
        if tokens.expires_at - 30 < int(time.time()):
            tokens = self._refresh(tokens)
        return tokens

    def _refresh(self, current: TokenPair) -> TokenPair:
        new = refresh_token(
            current.refresh_token,
            client_id=self.settings.fortnox_client_id,
            client_secret=self.settings.fortnox_client_secret,
        )
        store_tokens(self.session, self.firma_id, new, settings=self.settings)
        log.info("fortnox.token.refreshed", firma=self.firma_id)
        return new

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        tokens = self._tokens()
        headers = kwargs.pop("headers", {}) or {}
        headers["Authorization"] = f"Bearer {tokens.access_token}"
        headers["Accept"] = "application/json"
        resp = self._http.request(method, path, headers=headers, **kwargs)
        if resp.status_code == 401:
            tokens = self._refresh(tokens)
            headers["Authorization"] = f"Bearer {tokens.access_token}"
            resp = self._http.request(method, path, headers=headers, **kwargs)
        resp.raise_for_status()
        return resp

    def list_customers(self, *, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        resp = self._request(
            "GET", "/customers", params={"limit": limit, "offset": offset}
        )
        body = resp.json()
        return body.get("Customers", [])

    def get_customer(self, customer_number: str) -> dict[str, Any] | None:
        resp = self._request("GET", f"/customers/{customer_number}")
        return resp.json().get("Customer")

    def upsert_customer(self, customer: dict[str, Any]) -> dict[str, Any]:
        resp = self._request("POST", "/customers", json={"Customer": customer})
        return resp.json().get("Customer", {})

    def list_invoices(self, *, limit: int = 50) -> list[dict[str, Any]]:
        resp = self._request("GET", "/invoices", params={"limit": limit})
        return resp.json().get("Invoices", [])


# --- Sync operations ---


def sync_customers_to_local(
    fortnox: FortnoxClient,
    *,
    limit: int = 100,
) -> int:
    """Pull recent Fortnox customers into the firma's `customer` table."""
    pulled = 0
    for fc in fortnox.list_customers(limit=limit):
        phone = (fc.get("Phone1") or fc.get("Phone2") or "").strip()
        if not phone:
            continue
        # Normalize Swedish phone to E.164 if it starts with 0
        if phone.startswith("0"):
            phone = "+46" + phone[1:].replace(" ", "").replace("-", "")
        existing = fortnox.session.exec(
            select(Customer).where(
                Customer.firma_id == fortnox.firma_id, Customer.phone == phone
            )
        ).first()
        if existing is not None:
            continue
        fortnox.session.add(
            Customer(
                firma_id=fortnox.firma_id,
                type=CustomerType.COMPANY if fc.get("OrganisationNumber") else CustomerType.PRIVATE,
                name=fc.get("Name") or "",
                phone=phone,
                email=fc.get("Email"),
                org_number=fc.get("OrganisationNumber"),
                address=({"street": fc.get("Address1"), "city": fc.get("City"), "postal_code": fc.get("ZipCode")} if fc.get("Address1") else None),
                source="fortnox",
                notes_summary=f"Importerad från Fortnox ({fc.get('CustomerNumber')})",
            )
        )
        pulled += 1
    fortnox.session.commit()
    log.info("fortnox.customers.synced", firma=fortnox.firma_id, pulled=pulled)
    return pulled

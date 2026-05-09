"""Visma eEkonomi API client (https://developer.visma.com/api/eaccountingapi/).

OAuth 2.0 Authorization Code flow:
- Authorization: ``https://identity.vismaonline.com/connect/authorize``
- Token: ``https://identity.vismaonline.com/connect/token``
- API base: ``https://eaccountingapi.vismaonline.com/v2/``
- Scopes: ``ea:api`` (broad) + ``offline_access`` for refresh tokens.

Same token-storage pattern as Fortnox (KMS-encrypted refresh tokens in
`Integration.sync_state`). Same FortnoxClient-style transparent refresh
on 401.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx
from sqlmodel import Session, select

from svarsa.core.config import Settings, get_settings
from svarsa.core.logging import get_logger
from svarsa.core.time import utcnow
from svarsa.integrations.fortnox import _decrypt, _encrypt
from svarsa.models import Customer, CustomerType, Integration, IntegrationType

log = get_logger("svarsa.visma")

AUTH_URL = "https://identity.vismaonline.com/connect/authorize"
TOKEN_URL = "https://identity.vismaonline.com/connect/token"
API_BASE = "https://eaccountingapi.vismaonline.com/v2"
DEFAULT_SCOPES = ("ea:api", "offline_access")


@dataclass(frozen=True)
class VismaTokenPair:
    access_token: str
    refresh_token: str
    expires_at: int


def authorize_url(*, client_id: str, redirect_uri: str, state: str, scopes: tuple[str, ...] = DEFAULT_SCOPES) -> str:
    from urllib.parse import urlencode

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(scopes),
        "state": state,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code(
    code: str,
    *,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> VismaTokenPair:
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        resp.raise_for_status()
        body = resp.json()
        return VismaTokenPair(
            access_token=body["access_token"],
            refresh_token=body["refresh_token"],
            expires_at=int(time.time()) + int(body.get("expires_in", 3600)) - 30,
        )


def refresh_token(
    refresh: str, *, client_id: str, client_secret: str
) -> VismaTokenPair:
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh,
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        resp.raise_for_status()
        body = resp.json()
        return VismaTokenPair(
            access_token=body["access_token"],
            refresh_token=body["refresh_token"],
            expires_at=int(time.time()) + int(body.get("expires_in", 3600)) - 30,
        )


def store_tokens(
    session: Session,
    firma_id: str,
    tokens: VismaTokenPair,
    *,
    settings: Settings | None = None,
) -> Integration:
    s = settings or get_settings()
    integ = session.exec(
        select(Integration).where(
            Integration.firma_id == firma_id,
            Integration.type == IntegrationType.VISMA,
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
            type=IntegrationType.VISMA,
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


def load_tokens(session: Session, firma_id: str, settings: Settings | None = None) -> VismaTokenPair | None:
    s = settings or get_settings()
    integ = session.exec(
        select(Integration).where(
            Integration.firma_id == firma_id,
            Integration.type == IntegrationType.VISMA,
        )
    ).first()
    if integ is None or not integ.connected:
        return None
    state = integ.sync_state or {}
    access = state.get("access_token") or ""
    encrypted = state.get("refresh_token_encrypted") or ""
    if not access or not encrypted:
        return None
    return VismaTokenPair(
        access_token=access,
        refresh_token=_decrypt(encrypted, s),
        expires_at=int(state.get("expires_at", 0)),
    )


class VismaClient:
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

    def __enter__(self) -> "VismaClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self._http.close()

    def _tokens(self) -> VismaTokenPair:
        tokens = load_tokens(self.session, self.firma_id, self.settings)
        if tokens is None:
            msg = "visma_not_connected"
            raise RuntimeError(msg)
        if tokens.expires_at - 30 < int(time.time()):
            tokens = refresh_token(
                tokens.refresh_token,
                client_id=self.settings.visma_client_id,
                client_secret=self.settings.visma_client_secret,
            )
            store_tokens(self.session, self.firma_id, tokens, settings=self.settings)
        return tokens

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        tokens = self._tokens()
        headers = kwargs.pop("headers", {}) or {}
        headers["Authorization"] = f"Bearer {tokens.access_token}"
        headers["Accept"] = "application/json"
        resp = self._http.request(method, path, headers=headers, **kwargs)
        resp.raise_for_status()
        return resp

    def list_customers(self, *, limit: int = 100) -> list[dict[str, Any]]:
        resp = self._request("GET", "/customers", params={"$top": limit})
        return resp.json().get("data", [])


def sync_customers_to_local(client: VismaClient, *, limit: int = 100) -> int:
    pulled = 0
    for vc in client.list_customers(limit=limit):
        phone = (vc.get("Phone") or "").strip()
        if not phone:
            continue
        if phone.startswith("0"):
            phone = "+46" + phone[1:].replace(" ", "").replace("-", "")
        existing = client.session.exec(
            select(Customer).where(
                Customer.firma_id == client.firma_id, Customer.phone == phone
            )
        ).first()
        if existing is not None:
            continue
        client.session.add(
            Customer(
                firma_id=client.firma_id,
                type=CustomerType.COMPANY if vc.get("CorporateIdentityNumber") else CustomerType.PRIVATE,
                name=vc.get("Name") or "",
                phone=phone,
                email=vc.get("EmailAddress"),
                org_number=vc.get("CorporateIdentityNumber"),
                source="visma",
                notes_summary=f"Importerad från Visma ({vc.get('Id')})",
            )
        )
        pulled += 1
    client.session.commit()
    log.info("visma.customers.synced", firma=client.firma_id, pulled=pulled)
    return pulled

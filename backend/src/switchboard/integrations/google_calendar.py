"""Google Calendar bidirectional sync.

Uses the same Google OAuth client as NextAuth (with the additional scope
``https://www.googleapis.com/auth/calendar``). Tokens stored encrypted
per firma in `Integration.sync_state`.

API base: ``https://www.googleapis.com/calendar/v3/``
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx
from sqlmodel import Session, select

from switchboard.core.config import Settings, get_settings
from switchboard.core.logging import get_logger
from switchboard.core.time import utcnow
from switchboard.integrations.fortnox import _decrypt, _encrypt
from switchboard.models import Integration, IntegrationType

log = get_logger("switchboard.gcal")

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API_BASE = "https://www.googleapis.com/calendar/v3"
DEFAULT_SCOPES = (
    "https://www.googleapis.com/auth/calendar.events",
    "openid",
    "email",
)


@dataclass(frozen=True)
class GoogleTokenPair:
    access_token: str
    refresh_token: str
    expires_at: int


def authorize_url(*, client_id: str, redirect_uri: str, state: str) -> str:
    from urllib.parse import urlencode

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(DEFAULT_SCOPES),
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code(
    code: str,
    *,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> GoogleTokenPair:
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
        return GoogleTokenPair(
            access_token=body["access_token"],
            refresh_token=body.get("refresh_token", ""),
            expires_at=int(time.time()) + int(body.get("expires_in", 3600)) - 30,
        )


def refresh_token(
    refresh: str, *, client_id: str, client_secret: str
) -> GoogleTokenPair:
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
        return GoogleTokenPair(
            access_token=body["access_token"],
            refresh_token=refresh,  # Google sometimes omits; keep the existing
            expires_at=int(time.time()) + int(body.get("expires_in", 3600)) - 30,
        )


def store_tokens(
    session: Session,
    firma_id: str,
    tokens: GoogleTokenPair,
    *,
    settings: Settings | None = None,
) -> Integration:
    s = settings or get_settings()
    integ = session.exec(
        select(Integration).where(
            Integration.firma_id == firma_id,
            Integration.type == IntegrationType.GOOGLE_CALENDAR,
        )
    ).first()
    state = {
        "access_token": tokens.access_token,
        "refresh_token_encrypted": _encrypt(tokens.refresh_token, s) if tokens.refresh_token else "",
        "expires_at": tokens.expires_at,
        "updated_at": utcnow().isoformat(),
    }
    if integ is None:
        integ = Integration(
            firma_id=firma_id,
            type=IntegrationType.GOOGLE_CALENDAR,
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


def load_tokens(session: Session, firma_id: str, settings: Settings | None = None) -> GoogleTokenPair | None:
    s = settings or get_settings()
    integ = session.exec(
        select(Integration).where(
            Integration.firma_id == firma_id,
            Integration.type == IntegrationType.GOOGLE_CALENDAR,
        )
    ).first()
    if integ is None or not integ.connected:
        return None
    state = integ.sync_state or {}
    access = state.get("access_token") or ""
    encrypted = state.get("refresh_token_encrypted") or ""
    if not access:
        return None
    return GoogleTokenPair(
        access_token=access,
        refresh_token=_decrypt(encrypted, s) if encrypted else "",
        expires_at=int(state.get("expires_at", 0)),
    )


class GoogleCalendarClient:
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

    def __enter__(self) -> "GoogleCalendarClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self._http.close()

    def _tokens(self) -> GoogleTokenPair:
        tokens = load_tokens(self.session, self.firma_id, self.settings)
        if tokens is None:
            msg = "google_calendar_not_connected"
            raise RuntimeError(msg)
        if tokens.expires_at - 30 < int(time.time()) and tokens.refresh_token:
            tokens = refresh_token(
                tokens.refresh_token,
                client_id=self.settings.google_oauth_client_id,
                client_secret=self.settings.google_oauth_client_secret,
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

    def create_event(
        self,
        *,
        calendar_id: str = "primary",
        summary: str,
        description: str = "",
        start_iso: str,
        end_iso: str,
        location: str | None = None,
        attendees_email: list[str] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_iso, "timeZone": "Europe/Stockholm"},
            "end": {"dateTime": end_iso, "timeZone": "Europe/Stockholm"},
        }
        if location:
            body["location"] = location
        if attendees_email:
            body["attendees"] = [{"email": e} for e in attendees_email]
        resp = self._request(
            "POST", f"/calendars/{calendar_id}/events", json=body
        )
        return resp.json()

    def list_events(
        self,
        *,
        calendar_id: str = "primary",
        time_min_iso: str,
        time_max_iso: str,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        resp = self._request(
            "GET",
            f"/calendars/{calendar_id}/events",
            params={
                "timeMin": time_min_iso,
                "timeMax": time_max_iso,
                "maxResults": max_results,
                "singleEvents": "true",
                "orderBy": "startTime",
            },
        )
        return resp.json().get("items", [])

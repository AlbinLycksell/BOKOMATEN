"""Tool dispatch client.

The Realtime Bridge calls this to execute a tool. In `local` mode it routes
to `tools.handlers.dispatch` directly (single-deployable dev). In `http`
mode it POSTs to the Application Backend at `/api/tools/dispatch` over the
internal VPC connector — that's the production split per PRD §8.2/§8.10.

Either way, the Bridge gets the same `dict[str, Any]` result shape.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import httpx
from sqlmodel import Session

from switchboard.core.config import Settings, get_settings
from switchboard.core.constants import ContentType, HttpHeader
from switchboard.core.logging import get_logger
from switchboard.models import ToolDispatchMode
from switchboard.tools.handlers import ToolContext
from switchboard.tools.handlers import dispatch as local_dispatch

log = get_logger("switchboard.tools.client")


@runtime_checkable
class ToolClient(Protocol):
    async def dispatch(
        self,
        firma_id: str,
        call_id: str | None,
        name: str,
        args: dict[str, Any],
    ) -> dict[str, Any]: ...


class LocalToolClient:
    """In-process dispatch — used in dev / single-deployable mode."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.consent_disabled = False

    async def dispatch(
        self,
        firma_id: str,
        call_id: str | None,
        name: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        ctx = ToolContext(
            session=self.session,
            firma_id=firma_id,
            call_id=call_id,
        )
        result = local_dispatch(ctx, name, args)
        if ctx.consent_disabled:
            self.consent_disabled = True
        return result


class HTTPToolClient:
    """POST to Application Backend — used when Bridge and Backend deploy separately."""

    def __init__(self, base_url: str, internal_token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.internal_token = internal_token
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=1.0))

    async def aclose(self) -> None:
        await self._client.aclose()

    async def dispatch(
        self,
        firma_id: str,
        call_id: str | None,
        name: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        url = f"{self.base_url}/api/tools/dispatch"
        headers = {
            HttpHeader.FIRMA_ID: firma_id,
            HttpHeader.INTERNAL_TOKEN: self.internal_token,
            HttpHeader.CONTENT_TYPE: ContentType.JSON,
        }
        body = {"call_id": call_id, "name": name, "args": args}
        try:
            resp = await self._client.post(url, headers=headers, json=body)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            log.exception("tool.dispatch.http_error", name=name, error=str(exc))
            return {"error": f"dispatch_failed:{exc.__class__.__name__}"}
        return resp.json()


def make_tool_client(session: Session, settings: Settings | None = None) -> ToolClient:
    s = settings or get_settings()
    if s.tool_dispatch_mode is ToolDispatchMode.HTTP:
        return HTTPToolClient(s.application_backend_url, s.bridge_internal_token)
    return LocalToolClient(session)

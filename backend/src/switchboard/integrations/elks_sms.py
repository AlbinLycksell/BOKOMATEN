"""46elks SMS API client."""

from __future__ import annotations

from typing import Any

import httpx

from switchboard.core.config import Settings, get_settings
from switchboard.core.logging import get_logger

log = get_logger("switchboard.elks.sms")

ELKS_SMS_URL = "https://api.46elks.com/a1/SMS"


class ElksSMSClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = httpx.Client(
            auth=(self.settings.elks_api_username, self.settings.elks_api_password),
            timeout=httpx.Timeout(5.0, connect=2.0),
        )

    def send(
        self,
        *,
        to: str,
        message: str,
        sender_id: str | None = None,
    ) -> dict[str, Any]:
        if not self.settings.elks_api_username:
            log.warning("elks.sms.unconfigured", to=to)
            return {"id": "stub", "delivered": False, "reason": "not_configured"}
        from_id = sender_id or self.settings.elks_default_sender_id
        resp = self._client.post(
            ELKS_SMS_URL,
            data={"from": from_id, "to": to, "message": message},
        )
        resp.raise_for_status()
        body = resp.json()
        log.info("elks.sms.sent", id=body.get("id"), to=to, sender=from_id)
        return body

    def close(self) -> None:
        self._client.close()

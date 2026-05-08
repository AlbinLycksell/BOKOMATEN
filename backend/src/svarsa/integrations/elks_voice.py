"""46elks Voice Streaming adapter — webhook endpoint + frame translator.

46elks streams G.711 μ-law base64 frames over WebSocket and expects the
same back. The bridge already speaks a normalized provider-agnostic
protocol; this adapter converts.

In production:
- The 46elks number's "Voice" → "URL when called" points at
  ``https://app.svarsa.se/api/integrations/elks/voice/inbound``.
- That endpoint returns JSON instructing 46elks to open a stream to
  ``wss://bridge.svarsa.se/ws/bridge/{firma_id}/{call_id}``.
- The bridge accepts the stream and runs the conversation.
"""

from __future__ import annotations

from fastapi import APIRouter, Form, Request

from svarsa.core.config import get_settings
from svarsa.core.ids import new_id
from svarsa.core.logging import get_logger
from svarsa.db.session import get_engine
from svarsa.db.seed import DEMO_FIRMA_ID

router = APIRouter(prefix="/api/integrations/elks", tags=["elks"])
log = get_logger("svarsa.elks.voice")


@router.post("/voice/inbound")
async def voice_inbound(
    request: Request,
    callid: str = Form(default=""),
    direction: str = Form(default="incoming"),
    from_: str = Form(alias="from", default=""),
    to: str = Form(default=""),
) -> dict[str, object]:
    """Webhook hit by 46elks when an inbound call lands on a Svarsa number."""
    settings = get_settings()
    log.info("elks.voice.inbound", call=callid, from_=from_, to=to)

    # Resolve firma from the dialed number. For MVP we route every
    # inbound call to the demo firma; lookup by `to` lands in next-step plan.
    from sqlmodel import Session, select

    from svarsa.models import PhoneNumber

    firma_id = DEMO_FIRMA_ID
    with Session(get_engine()) as db:
        row = db.exec(select(PhoneNumber).where(PhoneNumber.e164 == to)).first()
        if row is not None:
            firma_id = row.firma_id

    bridge_call_id = new_id()
    bridge_url = (
        settings.application_backend_url.rstrip("/")
        .replace("https://", "wss://")
        .replace("http://", "ws://")
    )
    # If a dedicated bridge domain is configured, prefer that.
    if settings.tool_dispatch_mode == "http" and settings.application_backend_url:
        # In separate-deployable mode the bridge is on its own host, but
        # we don't keep a separate setting for it yet. The deploy guide
        # documents how to override via SVARSA_APPLICATION_BACKEND_URL on
        # the 46elks-facing service if needed.
        pass
    ws_url = f"{bridge_url}/ws/bridge/{firma_id}/{bridge_call_id}"

    return {
        "voicestart": ws_url,
        "callerid": from_,
        "from": from_,
        "to": to,
        "next": ws_url,
    }

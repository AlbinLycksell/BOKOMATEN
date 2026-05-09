"""46elks Voice Streaming integration — webhook + WS protocol.

The owner sets the inbound number's "Voice URL" in the 46elks dashboard to
``https://app.switchboard.se/api/integrations/elks/voice/inbound``. 46elks POSTs
form-encoded call metadata; we respond with a JSON body that tells 46elks
to open a WebSocket to our bridge:

    {"connect": "wss://bridge.switchboard.se/ws/bridge/{firma_id}/{call_id}"}

46elks then opens the WebSocket and streams PCM 24kHz audio. The wire
protocol used over that WS lives in `bridge/ws.py`.

Reference: https://46elks.fi/tutorials/real-time-two-way-voice-calls-with-websocket
"""

from __future__ import annotations

from fastapi import APIRouter, Form

from switchboard.core.config import get_settings
from switchboard.core.ids import new_id
from switchboard.core.logging import get_logger
from switchboard.db.seed import DEMO_FIRMA_ID
from switchboard.db.session import get_engine

router = APIRouter(prefix="/api/integrations/elks", tags=["elks"])
log = get_logger("switchboard.elks.voice")


def _bridge_ws_base(public_url: str) -> str:
    """Convert https:// → wss:// (or http:// → ws://) for the bridge endpoint."""
    if public_url.startswith("https://"):
        return "wss://" + public_url.removeprefix("https://").rstrip("/")
    if public_url.startswith("http://"):
        return "ws://" + public_url.removeprefix("http://").rstrip("/")
    return public_url.rstrip("/")


@router.post("/voice/inbound")
async def voice_inbound(
    callid: str = Form(default=""),
    direction: str = Form(default="incoming"),
    from_: str = Form(alias="from", default=""),
    to: str = Form(default=""),
) -> dict[str, str]:
    """Webhook hit by 46elks when an inbound call lands on a Switchboard number.

    Returns a JSON body 46elks understands as "open a WebSocket here".
    """
    settings = get_settings()
    log.info("elks.voice.inbound", callid=callid, from_=from_, to=to)

    from sqlmodel import Session, select

    from switchboard.models import PhoneNumber

    firma_id = DEMO_FIRMA_ID
    with Session(get_engine()) as db:
        row = db.exec(select(PhoneNumber).where(PhoneNumber.e164 == to)).first()
        if row is not None:
            firma_id = row.firma_id

    # Plan-aware busy-tone gate — refuse the call if the firma is over-quota
    # or has a delinquent subscription.
    from switchboard.integrations.stripe_billing import check_call_allowed
    from switchboard.models import Firma

    with Session(get_engine()) as db:
        firma = db.get(Firma, firma_id)
        if firma is not None:
            allowed, reason = check_call_allowed(firma)
            if not allowed:
                log.warning("elks.voice.rejected", firma=firma_id, reason=reason)
                # 46elks recognizes "hangup" to drop the call immediately.
                return {"hangup": "true"}

    bridge_call_id = callid or new_id()
    base = _bridge_ws_base(settings.application_backend_url)
    ws_url = f"{base}/ws/bridge/{firma_id}/{bridge_call_id}"

    return {"connect": ws_url}

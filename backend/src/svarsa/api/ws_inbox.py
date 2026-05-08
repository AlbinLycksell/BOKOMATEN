"""Live inbox WebSocket — broadcasts call lifecycle events to the dashboard.

MVP uses an in-process pub-sub. Replace with Redis Pub/Sub in production
to support multi-process Cloud Run deployments.
"""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from svarsa.core.logging import get_logger

router = APIRouter()
log = get_logger("svarsa.inbox")

_channels: dict[str, set[WebSocket]] = defaultdict(set)
_lock = asyncio.Lock()


async def publish(firma_id: str, event: str, payload: dict[str, Any]) -> None:
    async with _lock:
        listeners = list(_channels.get(firma_id, set()))
    if not listeners:
        return
    msg = json.dumps({"event": event, "payload": payload})
    for ws in listeners:
        try:
            await ws.send_text(msg)
        except Exception:  # noqa: BLE001
            log.warning("inbox.publish.dropped", firma=firma_id)


@router.websocket("/ws/inbox/{firma_id}")
async def inbox(websocket: WebSocket, firma_id: str) -> None:
    await websocket.accept()
    async with _lock:
        _channels[firma_id].add(websocket)
    log.info("inbox.connected", firma=firma_id)
    try:
        while True:
            await websocket.receive_text()  # ignore client pings
    except WebSocketDisconnect:
        pass
    finally:
        async with _lock:
            _channels[firma_id].discard(websocket)
        log.info("inbox.disconnected", firma=firma_id)

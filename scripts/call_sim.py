"""
Simulate a phone call through the Switchboard bridge.

Connects your mic + speakers to the bridge WebSocket at
ws://localhost:8000/ws/bridge/<firma_id>/<call_id>, routing audio through
Gemini with the full system prompt and booking tools. Everything is logged
to the dashboard at http://localhost:3000.

Usage:
    cd scripts
    uv run call_sim.py

Press Ctrl+C to hang up.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import queue
import sys
import traceback
from pathlib import Path

import sounddevice as sd
import websockets
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK

# ---------------------------------------------------------------------------
# Load .env / .env.local from repo root
# ---------------------------------------------------------------------------

def _load_env() -> None:
    root = Path(__file__).resolve().parent.parent
    for name in (".env", ".env.local"):
        path = root / name
        if not path.exists():
            continue
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)

_load_env()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BRIDGE_BASE  = os.environ.get("BRIDGE_URL", "ws://127.0.0.1:8000/ws/bridge/01J0000FIRM0ANDERSSONSVVS00")
CALLER_PHONE = os.environ.get("CALLER_PHONE", "+46700000001")

SAMPLE_RATE = 24000
CHANNELS    = 1
CHUNK       = 2048

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def _run() -> None:
    from ulid import ULID
    call_id = str(ULID())
    url = f"{BRIDGE_BASE}/{call_id}"

    print(f"Connecting to bridge…")
    print(f"  URL:    {url}")
    print(f"  Caller: {CALLER_PHONE}")
    print(f"  Watch:  http://localhost:3000/inbox")
    print("Speak after connection. Ctrl+C to hang up.\n")

    mic_q: queue.Queue[bytes] = queue.Queue(maxsize=40)
    play_q: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=100)
    send_stop = asyncio.Event()   # stop sending mic audio
    play_done = asyncio.Event()   # play_audio finished draining

    def mic_callback(indata, frames, time_info, status) -> None:
        if not send_stop.is_set():
            try:
                mic_q.put_nowait(bytes(indata))
            except queue.Full:
                pass

    async def send_audio(ws) -> None:
        try:
            while not send_stop.is_set():
                try:
                    pcm = await asyncio.to_thread(mic_q.get, True, 0.1)
                except Exception:
                    continue
                b64 = base64.b64encode(pcm).decode()
                await ws.send(json.dumps({"t": "audio", "data": b64}))
        except Exception:
            pass

    async def recv_loop(ws) -> None:
        try:
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                except ConnectionClosedOK:
                    # Normal end of session — drain whatever audio is queued then stop
                    play_q.put_nowait(None)
                    return
                except ConnectionClosed as e:
                    print(f"\n[bridge] disconnected: {e}")
                    play_q.put_nowait(None)
                    return
                msg = json.loads(raw)
                t = msg.get("t")
                if t == "audio":
                    play_q.put_nowait(base64.b64decode(msg["data"]))
                elif t == "interrupt":
                    while not play_q.empty():
                        play_q.get_nowait()
                elif t == "bye":
                    print("\n[bridge] Server ended the call.")
                    play_q.put_nowait(None)
                    return
                elif t == "sync":
                    try:
                        await ws.send(json.dumps({"t": "sync"}))
                    except Exception:
                        pass
        except Exception as e:
            print(f"[recv error] {e}", file=sys.stderr)
            play_q.put_nowait(None)

    async def play_audio() -> None:
        try:
            stream = sd.RawOutputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16")
            stream.start()
            while True:
                try:
                    chunk = await asyncio.wait_for(play_q.get(), timeout=0.3)
                except asyncio.TimeoutError:
                    continue
                if chunk is None:
                    break
                await asyncio.to_thread(stream.write, chunk)
            stream.stop()
            stream.close()
        except Exception as e:
            print(f"[play error] {e}", file=sys.stderr)
        finally:
            play_done.set()

    async def send_sync(ws) -> None:
        try:
            while not send_stop.is_set():
                await asyncio.sleep(5)
                if not send_stop.is_set():
                    await ws.send(json.dumps({"t": "sync"}))
        except Exception:
            pass

    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({
            "t": "hello",
            "callid": call_id,
            "from": CALLER_PHONE,
            "to": "+46000000000",
        }))

        for _ in range(2):
            print(f"[bridge] {json.loads(await ws.recv())}")

        print("\n--- Connected. Speak now. ---\n")

        with sd.RawInputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16",
                               blocksize=CHUNK, callback=mic_callback):

            tasks = [
                asyncio.create_task(send_audio(ws)),
                asyncio.create_task(recv_loop(ws)),
                asyncio.create_task(play_audio()),
                asyncio.create_task(send_sync(ws)),
            ]

            try:
                # Wait for Ctrl+C — recv_loop handles the play drain via None sentinel
                await asyncio.gather(*tasks)
            except (KeyboardInterrupt, asyncio.CancelledError):
                pass

        send_stop.set()

        # Let play_audio finish draining any queued audio
        if not play_done.is_set():
            play_q.put_nowait(None)
            try:
                await asyncio.wait_for(play_done.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                pass

        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

        try:
            await ws.send(json.dumps({"t": "bye", "reason": "hangup"}))
        except Exception:
            pass

    print("\nCall ended. Check http://localhost:3000/inbox for the result.")


if __name__ == "__main__":
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        print("\nHanging up…")
    except Exception:
        traceback.print_exc()
        sys.exit(1)

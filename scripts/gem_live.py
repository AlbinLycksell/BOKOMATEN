"""
Real-time voice chat with Gemini Live, with optional vision.

## What it does
Opens a WebSocket session to the Gemini Live API and runs four concurrent streams:

- **Mic in**: captures 16 kHz PCM audio from the default input device and streams
  it to Gemini as it's recorded.
- **Vision in** (optional): depending on `--mode`, also streams ~1 fps frames as
  JPEGs — `camera` (default) uses the webcam via OpenCV, `screen` grabs the
  primary display via mss, `none` disables visual input.
- **Text in**: a `message > ` prompt on stdin lets you type a message at any
  time (sent as a turn-completing user message). Type `q` to quit.
- **Audio out**: streams Gemini's spoken reply (24 kHz PCM, `Zephyr` voice) and
  plays it through the default output device. Interrupting the model clears the
  playback queue so it stops talking immediately.

Nothing is rendered on screen — the only visible UI is the `message > ` prompt
and any text the model emits inline. Everything else is audio.

## Documentation
Quickstart: https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_LiveAPI.py

## Setup

To install the dependencies for this script, run:

```
pip install google-genai opencv-python pyaudio pillow mss
```
"""

import os
import asyncio
import io
import sys
import traceback
from pathlib import Path

import cv2
import pyaudio
import PIL.Image

import argparse

from google import genai
from google.genai import types
from google.genai.types import Type


def _load_env_files() -> None:
    """Load .env then .env.local from the project root.

    Precedence (highest first): real environment > .env.local > .env.
    """
    project_root = Path(__file__).resolve().parent.parent
    file_values: dict[str, str] = {}
    for name in (".env", ".env.local"):
        path = project_root / name
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
                file_values[key] = value
    for key, value in file_values.items():
        os.environ.setdefault(key, value)


_load_env_files()

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

MODEL = "models/gemini-3.1-flash-live-preview"

DEFAULT_MODE = "camera"

client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=os.environ.get("GEMINI_API_KEY"),
)


CONFIG = types.LiveConnectConfig(
    response_modalities=[
        "AUDIO",
    ],
    media_resolution="MEDIA_RESOLUTION_MEDIUM",
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Zephyr")
        )
    ),
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=104857,
        sliding_window=types.SlidingWindow(target_tokens=52428),
    ),
)

pya = pyaudio.PyAudio()


class AudioLoop:
    def __init__(self, video_mode=DEFAULT_MODE):
        self.video_mode = video_mode

        self.audio_in_queue = None
        self.out_queue = None

        self.session = None

        self.send_text_task = None
        self.receive_audio_task = None
        self.play_audio_task = None

        self.audio_stream = None

        # Cumulative token usage across the session.
        # prompt_* is naturally session-cumulative on the wire (server reports
        # the running input total each frame). response/thoughts/tool reset per
        # turn, so we track a per-turn rolling max and absorb it on turn end.
        self._cum_prompt = 0
        self._cum_response = 0
        self._cum_thoughts = 0
        self._cum_tool_use = 0
        self._cum_prompt_modalities: dict[str, int] = {}
        self._cum_response_modalities: dict[str, int] = {}
        self._turn_response = 0
        self._turn_thoughts = 0
        self._turn_tool_use = 0
        self._turn_response_modalities: dict[str, int] = {}

    async def send_text(self):
        while True:
            text = await asyncio.to_thread(
                input,
                "message > ",
            )
            if text.lower() == "q":
                break
            if self.session is not None:
                await self.session.send_client_content(
                    turns=types.Content(
                        role="user",
                        parts=[types.Part(text=text or ".")],
                    ),
                    turn_complete=True,
                )

    def _get_frame(self, cap):
        # Read the frameq
        ret, frame = cap.read()
        # Check if the frame was read successfully
        if not ret:
            return None
        # Fix: Convert BGR to RGB color space
        # OpenCV captures in BGR but PIL expects RGB format
        # This prevents the blue tint in the video feed
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = PIL.Image.fromarray(frame_rgb)  # Now using RGB frame
        img.thumbnail([1024, 1024])

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)

        mime_type = "image/jpeg"
        image_bytes = image_io.read()
        return {"mime_type": mime_type, "data": image_bytes}

    async def get_frames(self):
        # This takes about a second, and will block the whole program
        # causing the audio pipeline to overflow if you don't to_thread it.
        cap = await asyncio.to_thread(
            cv2.VideoCapture, 0
        )  # 0 represents the default camera

        while True:
            frame = await asyncio.to_thread(self._get_frame, cap)
            if frame is None:
                break

            await asyncio.sleep(1.0)

            if self.out_queue is not None:
                await self.out_queue.put(frame)

        # Release the VideoCapture object
        cap.release()

    def _get_screen(self):
        try:
            import mss  # pytype: disable=import-error # pylint: disable=g-import-not-at-top
        except ImportError as e:
            raise ImportError("Please install mss package using 'pip install mss'") from e
        sct = mss.mss()
        monitor = sct.monitors[0]

        i = sct.grab(monitor)

        mime_type = "image/jpeg"
        image_bytes = mss.tools.to_png(i.rgb, i.size)
        img = PIL.Image.open(io.BytesIO(image_bytes))

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)

        image_bytes = image_io.read()
        return {"mime_type": mime_type, "data": image_bytes}

    async def get_screen(self):

        while True:
            frame = await asyncio.to_thread(self._get_screen)
            if frame is None:
                break

            await asyncio.sleep(1.0)

            if self.out_queue is not None:
                await self.out_queue.put(frame)

    async def send_realtime(self):
        while True:
            if self.out_queue is not None:
                msg = await self.out_queue.get()
                if self.session is None:
                    continue
                blob = types.Blob(data=msg["data"], mime_type=msg["mime_type"])
                if msg["mime_type"].startswith("audio/"):
                    await self.session.send_realtime_input(audio=blob)
                else:
                    await self.session.send_realtime_input(video=blob)

    async def listen_audio(self):
        mic_info = pya.get_default_input_device_info()
        self.audio_stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=CHUNK_SIZE,
        )
        if __debug__:
            kwargs = {"exception_on_overflow": False}
        else:
            kwargs = {}
        while True:
            data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
            if self.out_queue is not None:
                await self.out_queue.put(
                    {"data": data, "mime_type": f"audio/pcm;rate={SEND_SAMPLE_RATE}"}
                )

    @staticmethod
    def _modality_dict(details) -> dict[str, int]:
        """Convert list[ModalityTokenCount] → {modality_name: token_count}, dropping zeros."""
        out: dict[str, int] = {}
        if not details:
            return out
        for d in details:
            if d is None or not d.token_count:
                continue
            name = getattr(d.modality, "name", str(d.modality)).lower()
            out[name] = d.token_count
        return out

    @staticmethod
    def _fmt_modalities(d: dict[str, int]) -> str:
        if not d:
            return ""
        return " (" + " ".join(f"{k}={v}" for k, v in sorted(d.items())) + ")"

    def _update_usage(self, usage) -> None:
        # Prompt is cumulative across the session — server keeps the running total.
        if usage.prompt_token_count is not None:
            self._cum_prompt = usage.prompt_token_count
        prompt_mods = self._modality_dict(usage.prompt_tokens_details)
        if prompt_mods:
            self._cum_prompt_modalities = prompt_mods
        # Response/thoughts/tool reset each turn — track per-turn rolling max.
        if usage.response_token_count is not None:
            self._turn_response = max(self._turn_response, usage.response_token_count)
        if usage.thoughts_token_count is not None:
            self._turn_thoughts = max(self._turn_thoughts, usage.thoughts_token_count)
        if usage.tool_use_prompt_token_count is not None:
            self._turn_tool_use = max(self._turn_tool_use, usage.tool_use_prompt_token_count)
        for k, v in self._modality_dict(usage.response_tokens_details).items():
            self._turn_response_modalities[k] = max(
                self._turn_response_modalities.get(k, 0), v
            )
        self._render_usage()

    def _finish_turn(self) -> None:
        """Lock the current turn's response/thoughts/tool counters into the session totals."""
        self._cum_response += self._turn_response
        self._cum_thoughts += self._turn_thoughts
        self._cum_tool_use += self._turn_tool_use
        for k, v in self._turn_response_modalities.items():
            self._cum_response_modalities[k] = self._cum_response_modalities.get(k, 0) + v
        self._turn_response = 0
        self._turn_thoughts = 0
        self._turn_tool_use = 0
        self._turn_response_modalities = {}
        self._render_usage()

    def _render_usage(self) -> None:
        resp_now = self._cum_response + self._turn_response
        thoughts_now = self._cum_thoughts + self._turn_thoughts
        tool_now = self._cum_tool_use + self._turn_tool_use
        grand_total = self._cum_prompt + resp_now + thoughts_now + tool_now
        merged_resp = dict(self._cum_response_modalities)
        for k, v in self._turn_response_modalities.items():
            merged_resp[k] = merged_resp.get(k, 0) + v
        line = (
            f"[tokens] prompt={self._cum_prompt}"
            f"{self._fmt_modalities(self._cum_prompt_modalities)}  "
            f"resp={resp_now}{self._fmt_modalities(merged_resp)}  "
            f"total={grand_total}  thoughts={thoughts_now}"
        )
        sys.stderr.write(f"\r\x1b[2K{line}")
        sys.stderr.flush()

    async def receive_audio(self):
        "Background task to reads from the websocket and write pcm chunks to the output queue"
        while True:
            if self.session is not None:
                turn = self.session.receive()
                async for response in turn:
                    if usage := response.usage_metadata:
                        self._update_usage(usage)
                    if data := response.data:
                        self.audio_in_queue.put_nowait(data)
                        continue
                    if text := response.text:
                        print(text, end="")
                self._finish_turn()

                # If you interrupt the model, it sends a turn_complete.
                # For interruptions to work, we need to stop playback.
                # So empty out the audio queue because it may have loaded
                # much more audio than has played yet.
                while not self.audio_in_queue.empty():
                    self.audio_in_queue.get_nowait()

    async def play_audio(self):
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        try:
            while True:
                if self.audio_in_queue is not None:
                    bytestream = await self.audio_in_queue.get()
                    await asyncio.to_thread(stream.write, bytestream)
        finally:
            try:
                stream.close()
            except Exception:
                pass

    async def run(self):
        try:
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session

                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)

                send_text_task = tg.create_task(self.send_text())
                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())
                if self.video_mode == "camera":
                    tg.create_task(self.get_frames())
                elif self.video_mode == "screen":
                    tg.create_task(self.get_screen())

                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())

                await send_text_task
                raise asyncio.CancelledError("User requested exit")

        except asyncio.CancelledError:
            pass
        except ExceptionGroup as EG:
            traceback.print_exception(EG)
        finally:
            # Close the mic stream so its blocking read() in a worker thread returns,
            # otherwise loop.shutdown_default_executor() hangs joining it.
            try:
                if self.audio_stream is not None:
                    self.audio_stream.close()
                    self.audio_stream = None
            except Exception:
                pass
            sys.stderr.write("\n")
            sys.stderr.flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        type=str,
        default=DEFAULT_MODE,
        help="pixels to stream from",
        choices=["camera", "screen", "none"],
    )
    args = parser.parse_args()
    main = AudioLoop(video_mode=args.mode)
    exit_code = 0
    try:
        asyncio.run(main.run())
    except KeyboardInterrupt:
        sys.stderr.write("\n")
        sys.stderr.flush()
    except Exception:
        traceback.print_exc()
        exit_code = 1
    finally:
        try:
            pya.terminate()
        except Exception:
            pass
        # Worker threads spawned by asyncio.to_thread (input(), pyaudio reads,
        # cv2 capture) may still be blocked in syscalls; the interpreter's
        # atexit hook would otherwise hang joining them. Hard-exit instead.
        os._exit(exit_code)
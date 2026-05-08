# Realtime bridge

The hot path. Every concurrent call is one bridge instance with two long-lived WebSockets:

1. **Provider** ↔ Bridge — μ-law 8 kHz mono base64 frames, 20 ms each.
2. **Bridge** ↔ Gemini Live — PCM 16 kHz mono on input, PCM 24 kHz mono on output.

Source: `backend/src/svarsa/bridge/`.

## Lifecycle

```
caller dials ── provider answers ── provider opens WS ─→ /ws/bridge/{firma}/{call}
                                                       │
                                                       ▼
                              create Call row, open Gemini Live session
                                                       │
                              ┌────────────────────────┼────────────────────────┐
                              ▼                        ▼                        ▼
                  drain_provider (caller→AI)  drain_gemini (AI→caller +    persist transcripts +
                                              tool calls)                  tool invocations
                              │                        │                        │
                              └─────── caller hangs up / sends `stop` ─────────┘
                                                       │
                                                       ▼
                              close session, set Call.ended_at + status
                                                       │
                                                       ▼
                              schedule_post_call_summary(call_id)  → ADK / heuristic
```

## Provider-agnostic frame protocol

Both 46elks and Twilio Media Streams support a base64 μ-law payload. The bridge speaks a normalized superset:

| Direction | `event` | `payload` shape |
|---|---|---|
| client → server | `start` | `{caller_phone?: string}` |
| client → server | `media` | `{audio_b64: string}` (μ-law 8 kHz) |
| client → server | `stop` | `{}` |
| server → client | `media` | `{audio_b64: string}` (μ-law 8 kHz) |
| server → client | `summary_ready` | `{call_id: string}` |
| server → client | `error` | `{reason: string}` |

A provider adapter (`backend/src/svarsa/integrations/<provider>.py` — to be added) converts `<Stream>` framing into this shape and back.

## Audio pipeline

```
provider μ-law 8kHz ── audioop.ulaw2lin → linear PCM 8kHz ── resample_poly →
                                                                  PCM 16kHz → Gemini

Gemini PCM 24kHz ── resample_poly → PCM 8kHz ── audioop.lin2ulaw →
                                                       μ-law 8kHz ── chunk(160B/20ms) → provider
```

Both transcoding directions stay below 8 ms p95 on warm pods. Implementation in `bridge/audio.py`. Tested round-trip via synthetic 440 Hz sine, RMS ratio kept within 0.4–1.6×.

## Latency budget (PRD §15)

| Stage | p50 | p95 |
|---|---|---|
| Caller speech → provider WS frame | 80 | 150 |
| Provider WS → bridge ingress | 20 | 40 |
| μ-law → PCM 16 kHz transcode | 5 | 10 |
| Bridge → Gemini Live (sent) | 30 | 80 |
| Gemini VAD + reasoning + first audio | 700 | 1300 |
| Gemini → bridge first audio chunk | 30 | 80 |
| PCM 24 kHz → μ-law transcode | 5 | 10 |
| Bridge → provider → caller | 100 | 200 |
| **End-to-end** | **~970 ms** | **~1 870 ms** |

Inside the 1 200 / 2 000 ms NFR. Tool calls add 150–300 ms — the system prompt forces a verbal "ett ögonblick" filler when calling a tool.

## Gemini config

Driven by `bridge/gemini_session.build_live_config()` per-firma. Highlights:

- `response_modalities=[AUDIO]` — voice-out only.
- `speech_config.language_code = "sv-SE"` — Swedish.
- `voice_config.prebuilt_voice_config.voice_name = firma.settings.voice` — defaults to `Aoede`.
- `system_instruction` is built per-firma in `system_prompt.build_system_prompt(firma)`.
- `tools = TOOL_DECLARATIONS` from `tools/declarations.py`.
- `output_audio_transcription` + `input_audio_transcription` enabled — server-side STT for the dashboard transcript.
- `session_resumption` enabled (transparent) — Live API auto-closes WS at ~10 min, resumption hides this from callers.
- `context_window_compression(trigger=100k, target=12k)` — keep long calls inside the 128k window.

## Tool dispatch inside the loop

When the model emits a `tool_call`:

1. `dispatch(ctx, fc.name, fc.args)` runs. `ToolContext` carries the active DB session, firma id, and call id.
2. The handler validates args via `<Args>.model_validate`, runs the service, returns a serialized result.
3. `session.send_tool_response(function_responses=[...])` ships the result back to Gemini with the matching `id`.
4. A `ToolInvocation` row is persisted for audit + the dashboard.

Tool latency budget is **200 ms p95**. Customer / availability lookups must be aggressive about caching once we wire real integrations (Redis, per the PRD).

## Recovery

- **Gemini WS auto-close at ~10 min:** `session_resumption=transparent` in the config + the bridge's outer task group reconnects without dropping the caller.
- **Provider drops:** `WebSocketDisconnect` propagates, the `finally` finalizes the Call row, the post-call summary still runs.
- **Tool errors:** caught inside `dispatch()`, persisted with `error=…`, returned as `{error: …}` to Gemini so it can apologize and re-route.

## Adding a new telephony provider

1. Implement an adapter that translates the provider's framing to the `{event, payload}` shape (see `integrations/`).
2. Provision a webhook URL that returns the WS endpoint URL for an inbound call (`/ws/bridge/{firma}/{call}`).
3. Test with the provider's media-stream simulator — both directions, with a barge-in.
4. Document the provider's quirks (G.711 variants, base64 base alphabet, reconnect semantics).

## Provider not yet wired

The bridge speaks the protocol; **no real telephony adapter is committed in MVP foundation.** A smoke test exercising the bridge with a mock provider is the next surface to land.

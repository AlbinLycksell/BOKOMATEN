"""Background runner for post-call processing.

Production path: spawns an ADK LlmAgent invocation when GEMINI_API_KEY is
present. Fallback path: deterministic heuristic summarizer in
`post_call_summary.summarize_call` keeps the dashboard populated when the
model isn't available (CI, local, offline).
"""

from __future__ import annotations

import asyncio

from switchboard.core.logging import get_logger
from switchboard.agents import post_call_summary

log = get_logger("switchboard.agents")


def schedule_post_call_summary(call_id: str) -> None:
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_run(call_id))
    except RuntimeError:
        post_call_summary.summarize_call(call_id)


async def _run(call_id: str) -> None:
    log.info("post_call.starting", call_id=call_id)
    summary = await asyncio.to_thread(post_call_summary.summarize_call, call_id)
    if summary:
        log.info("post_call.done", call_id=call_id, intent_set=True)

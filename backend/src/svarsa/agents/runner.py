"""Stub dispatcher for post-call summarization (real ADK wiring in Phase 5)."""

from __future__ import annotations

from svarsa.core.logging import get_logger

log = get_logger("svarsa.agents")


def schedule_post_call_summary(call_id: str) -> None:
    """Phase 5 will run the ADK LlmAgent in the background."""
    log.info("post_call.scheduled", call_id=call_id)

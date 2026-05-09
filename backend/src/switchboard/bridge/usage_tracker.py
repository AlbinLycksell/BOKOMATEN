"""Cumulative session-token tracker (port from scripts/gem_live.py).

This version emits structured events so the Owner API can surface live
counters per call instead of writing to stderr.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from switchboard.core.logging import get_logger

log = get_logger("switchboard.usage")


@dataclass
class UsageSnapshot:
    prompt_total: int = 0
    response_total: int = 0
    thoughts_total: int = 0
    tool_use_total: int = 0
    grand_total: int = 0
    prompt_modalities: dict[str, int] = field(default_factory=dict)
    response_modalities: dict[str, int] = field(default_factory=dict)


class UsageTracker:
    def __init__(self, call_id: str | None = None) -> None:
        self.call_id = call_id
        self._cum_prompt = 0
        self._cum_response = 0
        self._cum_thoughts = 0
        self._cum_tool_use = 0
        self._cum_prompt_mods: dict[str, int] = {}
        self._cum_response_mods: dict[str, int] = {}
        self._turn_response = 0
        self._turn_thoughts = 0
        self._turn_tool_use = 0
        self._turn_response_mods: dict[str, int] = {}

    @staticmethod
    def _modality_dict(details) -> dict[str, int]:  # type: ignore[no-untyped-def]
        out: dict[str, int] = {}
        if not details:
            return out
        for d in details:
            if d is None or not d.token_count:
                continue
            name = getattr(d.modality, "name", str(d.modality)).lower()
            out[name] = d.token_count
        return out

    def update(self, usage) -> None:  # type: ignore[no-untyped-def]
        if usage is None:
            return
        if usage.prompt_token_count is not None:
            self._cum_prompt = usage.prompt_token_count
        prompt_mods = self._modality_dict(usage.prompt_tokens_details)
        if prompt_mods:
            self._cum_prompt_mods = prompt_mods
        if usage.response_token_count is not None:
            self._turn_response = max(self._turn_response, usage.response_token_count)
        if usage.thoughts_token_count is not None:
            self._turn_thoughts = max(self._turn_thoughts, usage.thoughts_token_count)
        if usage.tool_use_prompt_token_count is not None:
            self._turn_tool_use = max(self._turn_tool_use, usage.tool_use_prompt_token_count)
        for k, v in self._modality_dict(usage.response_tokens_details).items():
            self._turn_response_mods[k] = max(self._turn_response_mods.get(k, 0), v)

    def end_turn(self) -> None:
        self._cum_response += self._turn_response
        self._cum_thoughts += self._turn_thoughts
        self._cum_tool_use += self._turn_tool_use
        for k, v in self._turn_response_mods.items():
            self._cum_response_mods[k] = self._cum_response_mods.get(k, 0) + v
        self._turn_response = 0
        self._turn_thoughts = 0
        self._turn_tool_use = 0
        self._turn_response_mods = {}
        log.info(
            "usage.turn_end",
            call_id=self.call_id,
            **self.snapshot().__dict__,
        )

    def snapshot(self) -> UsageSnapshot:
        resp_now = self._cum_response + self._turn_response
        thoughts_now = self._cum_thoughts + self._turn_thoughts
        tool_now = self._cum_tool_use + self._turn_tool_use
        merged_resp = dict(self._cum_response_mods)
        for k, v in self._turn_response_mods.items():
            merged_resp[k] = merged_resp.get(k, 0) + v
        return UsageSnapshot(
            prompt_total=self._cum_prompt,
            response_total=resp_now,
            thoughts_total=thoughts_now,
            tool_use_total=tool_now,
            grand_total=self._cum_prompt + resp_now + thoughts_now + tool_now,
            prompt_modalities=dict(self._cum_prompt_mods),
            response_modalities=merged_resp,
        )

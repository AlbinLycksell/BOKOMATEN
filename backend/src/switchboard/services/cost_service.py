"""Per-call cost computation.

Cost components (all in SEK):

- Vertex Live API: tokens × per-token rate (PRD §10.1 estimate, ~0,9 SEK/min
  audio at typical mix). We compute from the UsageTracker snapshot.
- 46elks inbound minute: ~0,40 SEK/min.
- 46elks SMS: ~0,30 SEK each.
- Compute/infra: amortized; we apply a flat ~0,30 SEK overhead per call.

Rates are tunable in `Settings.cost_rates_*` so we can refresh as
Google's GA pricing lands without redeploying.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from switchboard.bridge.usage_tracker import UsageSnapshot
from switchboard.core.config import Settings, get_settings


@dataclass(frozen=True)
class CostBreakdown:
    gemini_sek: float
    telephony_sek: float
    sms_sek: float
    overhead_sek: float
    total_sek: float
    duration_seconds: int
    sms_count: int
    prompt_tokens: int
    response_tokens: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute(
    *,
    usage: UsageSnapshot,
    duration_seconds: int,
    sms_count: int,
    settings: Settings | None = None,
) -> CostBreakdown:
    s = settings or get_settings()
    minutes = max(0.0, duration_seconds / 60.0)
    # Vertex Live API tokens — split prompt vs response
    gemini = (
        usage.prompt_total * s.cost_rate_prompt_token_sek
        + usage.response_total * s.cost_rate_response_token_sek
        + usage.thoughts_total * s.cost_rate_response_token_sek
    )
    telephony = minutes * s.cost_rate_telephony_minute_sek
    sms = sms_count * s.cost_rate_sms_sek
    overhead = s.cost_overhead_sek
    total = gemini + telephony + sms + overhead
    return CostBreakdown(
        gemini_sek=round(gemini, 4),
        telephony_sek=round(telephony, 4),
        sms_sek=round(sms, 4),
        overhead_sek=round(overhead, 4),
        total_sek=round(total, 4),
        duration_seconds=duration_seconds,
        sms_count=sms_count,
        prompt_tokens=usage.prompt_total,
        response_tokens=usage.response_total,
    )

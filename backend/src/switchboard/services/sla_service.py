"""Per-tool latency SLO surface.

PRD §8.4 sets the budget at 200 ms p95 per tool. We compute rolling
percentiles from `tool_invocation` and expose them via the dashboard
metrics endpoint. A breach raises a Sentry issue (when configured) so
oncall sees it without a separate alert pipeline.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable

from sqlmodel import Session, select

from switchboard.core.logging import get_logger
from switchboard.core.time import utcnow
from switchboard.models import ToolInvocation

log = get_logger("switchboard.sla")

P95_BUDGET_MS = 200


@dataclass(frozen=True)
class ToolLatencyStats:
    name: str
    n: int
    p50_ms: int
    p95_ms: int
    p99_ms: int
    error_rate: float

    def breaches_p95(self) -> bool:
        return self.n >= 20 and self.p95_ms > P95_BUDGET_MS


def _percentile(values: list[int], pct: float) -> int:
    if not values:
        return 0
    s = sorted(values)
    idx = max(0, min(len(s) - 1, int(pct / 100.0 * len(s)) - 1))
    return s[idx]


def compute_stats(
    session: Session,
    *,
    firma_id: str | None = None,
    window_hours: int = 24,
) -> list[ToolLatencyStats]:
    cutoff = utcnow() - timedelta(hours=window_hours)
    stmt = select(ToolInvocation).where(ToolInvocation.invoked_at >= cutoff)
    if firma_id is not None:
        stmt = stmt.where(ToolInvocation.firma_id == firma_id)
    rows = session.exec(stmt).all()

    by_name: dict[str, list[ToolInvocation]] = defaultdict(list)
    for r in rows:
        by_name[r.name].append(r)

    stats: list[ToolLatencyStats] = []
    for name, items in by_name.items():
        latencies = [i.latency_ms for i in items if i.latency_ms is not None]
        errors = sum(1 for i in items if i.error)
        stats.append(
            ToolLatencyStats(
                name=name,
                n=len(items),
                p50_ms=_percentile(latencies, 50),
                p95_ms=_percentile(latencies, 95),
                p99_ms=_percentile(latencies, 99),
                error_rate=errors / max(len(items), 1),
            )
        )
    return sorted(stats, key=lambda s: -s.p95_ms)


def detect_breaches(stats: Iterable[ToolLatencyStats]) -> list[ToolLatencyStats]:
    return [s for s in stats if s.breaches_p95()]

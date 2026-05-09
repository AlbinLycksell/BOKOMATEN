"""Metrics endpoints — per-tool latency stats + per-firma cost rollup."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from svarsa.api.deps import get_current_firma, get_db
from svarsa.models import Call, Firma
from svarsa.services import sla_service

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


class ToolLatencyStat(BaseModel):
    name: str
    n: int
    p50_ms: int
    p95_ms: int
    p99_ms: int
    error_rate: float
    breaches_p95: bool


class CostRollup(BaseModel):
    n: int
    total_sek: float
    avg_sek: float
    p95_sek: float


@router.get("/tools/latency", response_model=list[ToolLatencyStat])
def tool_latency(
    firma: Annotated[Firma, Depends(get_current_firma)],
    db: Annotated[Session, Depends(get_db)],
    hours: int = Query(default=24, ge=1, le=720),
) -> list[ToolLatencyStat]:
    stats = sla_service.compute_stats(db, firma_id=firma.id, window_hours=hours)
    return [
        ToolLatencyStat(
            name=s.name,
            n=s.n,
            p50_ms=s.p50_ms,
            p95_ms=s.p95_ms,
            p99_ms=s.p99_ms,
            error_rate=s.error_rate,
            breaches_p95=s.breaches_p95(),
        )
        for s in stats
    ]


@router.get("/cost", response_model=CostRollup)
def cost_rollup(
    firma: Annotated[Firma, Depends(get_current_firma)],
    db: Annotated[Session, Depends(get_db)],
) -> CostRollup:
    rows = db.exec(select(Call.cost_total_sek).where(Call.firma_id == firma.id)).all()
    values = [float(v or 0.0) for v in rows]
    if not values:
        return CostRollup(n=0, total_sek=0.0, avg_sek=0.0, p95_sek=0.0)
    sorted_v = sorted(values)
    p95_idx = max(0, int(0.95 * len(sorted_v)) - 1)
    return CostRollup(
        n=len(values),
        total_sek=round(sum(values), 2),
        avg_sek=round(sum(values) / len(values), 2),
        p95_sek=round(sorted_v[p95_idx], 2),
    )

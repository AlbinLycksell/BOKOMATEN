"""Admin / operator endpoints — emulate calls, run tools, send test SMS,
preview the system prompt, query the audit log, run eval on demand.

Mounted under `/api/admin`. All routes are tenant-scoped via the
standard middleware. Production tightens this further with a role
check on the JWT (only owners hit `/api/admin`).
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from switchboard.api.deps import get_current_firma, get_db
from switchboard.bridge.system_prompt import build_system_prompt
from switchboard.core.config import get_settings
from switchboard.core.logging import get_logger
from switchboard.core.tenant import firma_context
from switchboard.core.time import utcnow
from switchboard.models import (
    AuditLog,
    AuditLogRead,
    Firma,
    Severity,
)
from switchboard.services import (
    audit_service,
    escalation_service,
    notification_service,
    scenario_service,
    sla_service,
)
from switchboard.tools.handlers import HANDLERS, ToolContext, dispatch as tool_dispatch
from switchboard.tools.schemas import TOOL_NAMES

router = APIRouter(prefix="/api/admin", tags=["admin"])
log = get_logger("switchboard.admin")


# ---- system prompt preview ----


class SystemPromptResponse(BaseModel):
    text: str
    length_chars: int
    estimated_tokens: int


@router.get("/system-prompt", response_model=SystemPromptResponse)
def system_prompt(
    firma: Annotated[Firma, Depends(get_current_firma)],
) -> SystemPromptResponse:
    text = build_system_prompt(firma)
    return SystemPromptResponse(
        text=text,
        length_chars=len(text),
        estimated_tokens=len(text) // 4,
    )


# ---- voice test readiness (pre-flight before opening the bridge WS) ----


class VoiceTestReadyResponse(BaseModel):
    ready: bool
    provider: str
    model: str
    reason: str | None = None


@router.get("/voice-test/ready", response_model=VoiceTestReadyResponse)
def voice_test_ready() -> VoiceTestReadyResponse:
    s = get_settings()
    if s.gemini_provider == "vertex":
        if not s.vertex_project:
            return VoiceTestReadyResponse(
                ready=False,
                provider="vertex",
                model=s.gemini_model,
                reason="SWITCHBOARD_VERTEX_PROJECT är inte satt på backenden.",
            )
        return VoiceTestReadyResponse(
            ready=True,
            provider=f"vertex:{s.vertex_location}",
            model=s.gemini_model,
        )
    if not s.gemini_api_key:
        return VoiceTestReadyResponse(
            ready=False,
            provider="api_key",
            model=s.gemini_model,
            reason=(
                "GEMINI_API_KEY är inte satt. Lägg till den i .env.local "
                "i repo-roten (eller exportera i din shell) och starta om "
                "backenden."
            ),
        )
    return VoiceTestReadyResponse(
        ready=True,
        provider="api_key",
        model=s.gemini_model,
    )


# ---- scenario runner ----


class ScenarioPresetResponse(BaseModel):
    id: str
    name_sv: str
    description_sv: str
    trade: str
    expected_intent: str
    expected_severity: str | None
    caller_phone: str
    turn_count: int


class ScenarioRunResponse(BaseModel):
    call_id: str
    intent: str | None
    severity: str | None
    tool_invocations: list[str]
    summary_short: str | None


@router.get("/scenarios", response_model=list[ScenarioPresetResponse])
def list_scenarios() -> list[ScenarioPresetResponse]:
    return [
        ScenarioPresetResponse(
            id=p.id,
            name_sv=p.name_sv,
            description_sv=p.description_sv,
            trade=p.trade.value,
            expected_intent=p.expected_intent.value,
            expected_severity=p.expected_severity.value if p.expected_severity else None,
            caller_phone=p.caller_phone,
            turn_count=len(p.caller_turns),
        )
        for p in scenario_service.list_presets()
    ]


@router.post("/scenarios/{preset_id}/run", response_model=ScenarioRunResponse)
async def run_scenario(
    preset_id: str,
    firma: Annotated[Firma, Depends(get_current_firma)],
    db: Annotated[Session, Depends(get_db)],
) -> ScenarioRunResponse:
    try:
        result = await scenario_service.run_preset_async(db, firma.id, preset_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ScenarioRunResponse(
        call_id=result.call_id,
        intent=result.intent.value if result.intent else None,
        severity=result.severity.value if result.severity else None,
        tool_invocations=result.tool_invocations,
        summary_short=result.summary_short,
    )


# ---- tool playground ----


class ToolListEntry(BaseModel):
    name: str
    args_schema: dict[str, Any]


class ToolRunRequest(BaseModel):
    name: str
    args: dict[str, Any] = Field(default_factory=dict)


class ToolRunResponse(BaseModel):
    name: str
    result: dict[str, Any]


@router.get("/tools", response_model=list[ToolListEntry])
def list_tools() -> list[ToolListEntry]:
    from switchboard.tools.declarations import TOOL_DESCRIPTIONS

    out: list[ToolListEntry] = []
    for name in TOOL_NAMES:
        args_model, _desc = TOOL_DESCRIPTIONS[name]
        schema = args_model.model_json_schema()
        out.append(ToolListEntry(name=name, args_schema=schema))
    return out


@router.post("/tools/run", response_model=ToolRunResponse)
def run_tool(
    payload: ToolRunRequest,
    firma: Annotated[Firma, Depends(get_current_firma)],
    db: Annotated[Session, Depends(get_db)],
) -> ToolRunResponse:
    if payload.name not in HANDLERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"unknown_tool:{payload.name}",
        )
    with firma_context(firma.id):
        ctx = ToolContext(session=db, firma_id=firma.id, call_id=None)
        result = tool_dispatch(ctx, payload.name, payload.args)
        audit_service.record(
            db,
            actor="admin",
            action="admin.tool.tested",
            target_type="tool",
            target_id=payload.name,
            payload={"args": payload.args, "ok": "error" not in result},
        )
    return ToolRunResponse(name=payload.name, result=result)


# ---- test SMS / test escalation ----


class TestSmsRequest(BaseModel):
    to_phone: str = Field(pattern=r"^\+46\d{6,10}$")
    template: str = "callback_promise"
    context_data: dict[str, str | int | bool] = Field(default_factory=dict)


class TestSmsResponse(BaseModel):
    sent: bool
    sms_id: str
    via: str  # "live" or "simulated"


@router.post("/test/sms", response_model=TestSmsResponse)
def test_sms(
    payload: TestSmsRequest,
    firma: Annotated[Firma, Depends(get_current_firma)],
    db: Annotated[Session, Depends(get_db)],
) -> TestSmsResponse:
    settings = get_settings()
    from switchboard.models import FirmaSettings

    fs = FirmaSettings.model_validate(firma.settings or {})
    res = notification_service.send_sms(
        to_phone=payload.to_phone,
        template=payload.template,  # type: ignore[arg-type]
        context_data=payload.context_data,
        firma_sender_id=fs.sms_sender_id,
        firma_sender_id_verified=fs.sms_sender_id_verified,
    )
    via = "live" if settings.elks_api_username else "simulated"
    with firma_context(firma.id):
        audit_service.record(
            db,
            actor="admin",
            action="admin.sms.tested",
            target_type="phone",
            target_id=payload.to_phone,
            payload={"template": payload.template, "via": via},
        )
    return TestSmsResponse(sent=res.sent, sms_id=res.sms_id, via=via)


class TestEscalationRequest(BaseModel):
    severity: Severity = Severity.HIGH
    reason_sv: str = "Testäskalering från adminpanelen"


class TestEscalationResponse(BaseModel):
    escalation_id: str
    contacted: list[str]
    next_in_chain_minutes: int


@router.post("/test/escalation", response_model=TestEscalationResponse)
def test_escalation(
    payload: TestEscalationRequest,
    firma: Annotated[Firma, Depends(get_current_firma)],
    db: Annotated[Session, Depends(get_db)],
) -> TestEscalationResponse:
    # Use a synthetic but real-looking call id so the Escalation row is
    # auditable but doesn't pollute the inbox.
    from switchboard.core.ids import new_id
    from switchboard.models import Call, CallStatus

    with firma_context(firma.id):
        synthetic_call = Call(
            id=new_id(),
            firma_id=firma.id,
            status=CallStatus.HANDLED,
            intent=None,
            severity=payload.severity,
            gemini_session_id="admin:test_escalation",
            ended_at=utcnow(),
            billing_seconds=1,
        )
        db.add(synthetic_call)
        db.commit()
        result = escalation_service.escalate(
            db,
            firma.id,
            synthetic_call.id,
            severity=payload.severity,
            reason_sv=payload.reason_sv,
        )
        audit_service.record(
            db,
            actor="admin",
            action="admin.escalation.tested",
            target_type="call",
            target_id=synthetic_call.id,
            payload={"severity": payload.severity.value, "reason_sv": payload.reason_sv},
        )
    return TestEscalationResponse(
        escalation_id=result.escalation_id,
        contacted=result.contacted,
        next_in_chain_minutes=result.next_in_chain_minutes,
    )


# ---- audit log viewer ----


@router.get("/audit-log", response_model=list[AuditLogRead])
def audit_log(
    firma: Annotated[Firma, Depends(get_current_firma)],
    db: Annotated[Session, Depends(get_db)],
    action_prefix: str | None = None,
    actor: str | None = None,
    hours: int = Query(default=24, ge=1, le=720),
    limit: int = Query(default=200, ge=1, le=1000),
) -> list[AuditLogRead]:
    cutoff = utcnow() - timedelta(hours=hours)
    stmt = (
        select(AuditLog)
        .where(AuditLog.firma_id == firma.id)
        .where(AuditLog.created_at >= cutoff)
    )
    if action_prefix:
        stmt = stmt.where(AuditLog.action.like(f"{action_prefix}%"))  # type: ignore[attr-defined]
    if actor:
        stmt = stmt.where(AuditLog.actor == actor)
    stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit)  # type: ignore[arg-type]
    rows = db.exec(stmt).all()
    return [
        AuditLogRead(
            id=r.id,
            actor=r.actor,
            action=r.action,
            target_type=r.target_type,
            target_id=r.target_id,
            payload=r.payload,
            created_at=r.created_at,
        )
        for r in rows
    ]


# ---- on-demand eval run ----


class EvalRunRequest(BaseModel):
    dataset_path: str | None = None  # defaults to backend/eval/sample.jsonl


class EvalRunResponse(BaseModel):
    total: int
    intent_accuracy: float
    severity_accuracy: float
    emergency_false_negatives: int
    by_intent: dict[str, int]
    failures: list[dict[str, Any]]


@router.post("/eval/run", response_model=EvalRunResponse)
def run_eval(payload: EvalRunRequest) -> EvalRunResponse:
    from switchboard.eval import dataset as eval_dataset
    from switchboard.eval import runner as eval_runner

    repo_root = Path(__file__).resolve().parents[4]
    path = Path(payload.dataset_path) if payload.dataset_path else (
        repo_root / "backend" / "eval" / "sample.jsonl"
    )
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"dataset_not_found:{path}",
        )
    dataset = eval_dataset.load_dataset(path)
    report = eval_runner.run(dataset)
    return EvalRunResponse(
        total=report.total,
        intent_accuracy=report.intent_accuracy,
        severity_accuracy=report.severity_accuracy,
        emergency_false_negatives=report.emergency_false_negatives,
        by_intent=dict(report.by_intent),
        failures=[
            {
                "call_id": f.call_id,
                "actual_intent": f.actual_intent.value if f.actual_intent else None,
                "actual_severity": f.actual_severity,
            }
            for f in report.failures[:25]
        ],
    )


# ---- per-tool latency snapshot ----


class ToolLatencySnapshot(BaseModel):
    name: str
    n: int
    p50_ms: int
    p95_ms: int
    p99_ms: int
    error_rate: float
    breaches_p95: bool


@router.get("/metrics/tools/latency", response_model=list[ToolLatencySnapshot])
def tools_latency(
    firma: Annotated[Firma, Depends(get_current_firma)],
    db: Annotated[Session, Depends(get_db)],
    hours: int = Query(default=24, ge=1, le=720),
) -> list[ToolLatencySnapshot]:
    stats = sla_service.compute_stats(db, firma_id=firma.id, window_hours=hours)
    return [
        ToolLatencySnapshot(
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

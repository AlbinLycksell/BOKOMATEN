"""Synthetic call scenarios — emulate a real call end-to-end without
hitting Gemini Live.

Used by the admin page so an operator can run a Swedish caller scenario
through triage + the standard tool playbook, see the resulting Call row
+ transcript + tool invocations + summary, and verify wiring before
flipping the real telephony provider on. Also used in eval to gate
deploys on triage accuracy.

The runner is fully tenant-scoped (refuses to operate without
``require_firma_id`` set) and writes through the same persistence layer
as a real call, so the result shows up in the inbox immediately.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from sqlmodel import Session

from switchboard.core.ids import new_id
from switchboard.core.logging import get_logger
from switchboard.core.tenant import firma_context
from switchboard.core.time import utcnow
from switchboard.models import (
    AuditAction,
    AuditActor,
    AuditTargetType,
    Call,
    CallSource,
    CallStatus,
    CustomerType,
    Firma,
    Intent,
    Severity,
    SmsTemplate,
    ToolName,
    Trade,
    TranscriptRole,
    TranscriptSegment,
    Urgency,
)
from switchboard.models.enums import EmergencyIndicator
from switchboard.services import audit_service, triage_service
from switchboard.tools.handlers import ToolContext
from switchboard.tools.handlers import dispatch as tool_dispatch

log = get_logger("switchboard.scenarios")


@dataclass
class ScenarioPreset:
    id: str
    name_sv: str
    description_sv: str
    trade: Trade
    expected_intent: Intent
    expected_severity: Severity | None
    caller_phone: str
    caller_turns: list[str]
    ai_turns: list[str] = field(default_factory=list)
    is_winter: bool = True


@dataclass
class ScenarioResult:
    call_id: str
    intent: Intent | None
    severity: Severity | None
    tool_invocations: list[ToolName]
    summary_short: str | None


# Swedish-text presets — each exercises a different code path. Keep these
# realistic (they're shown to operators) and faithful to PRD §6 examples.
PRESETS: dict[str, ScenarioPreset] = {
    "vattenlacka_akut": ScenarioPreset(
        id="vattenlacka_akut",
        name_sv="Vattenläcka — akut",
        description_sv="Inger Svensson ringer om vattenläcka under diskbänken. Bör triggas som AKUT/HIGH och eskaleras direkt till jourtekniker.",
        trade=Trade.VVS,
        expected_intent=Intent.AKUT,
        expected_severity=Severity.HIGH,
        caller_phone="+46708557777",
        caller_turns=[
            "Hej, jag har en vattenläcka under diskbänken, det rinner ner på golvet.",
            "Ja jag har stängt av huvudkranen men det är ändå vått.",
            "Storgatan 14, lägenhet 3, Bromma.",
        ],
        ai_turns=[
            "Hej, du har kommit till Anderssons VVS, jag är deras digitala assistent. Hur kan jag hjälpa dig?",
            "Det låter akut. Är det mycket vatten — har du behövt stänga av vattnet?",
            "Bra att du stängt av. Vad är din adress?",
            "Tack Inger. Magnus är på ett jobb just nu men jag skickar honom ditt ärende direkt. Han ringer upp inom 15 minuter.",
        ],
    ),
    "gas_lukt_kritisk": ScenarioPreset(
        id="gas_lukt_kritisk",
        name_sv="Gas-lukt — kritisk",
        description_sv="Kunden rapporterar gas-lukt. Bör triggas som CRITICAL och hänvisa till räddningstjänsten 112.",
        trade=Trade.VVS,
        expected_intent=Intent.AKUT,
        expected_severity=Severity.CRITICAL,
        caller_phone="+46708111000",
        caller_turns=[
            "Hej, det luktar gas i hela köket! Vad ska jag göra?",
            "Bryggargatan 8 i Solna.",
        ],
        ai_turns=[
            "Hej. Det här är akut — ring genast 112. Stäng av gasen om du kan, ventilera, gå ut. Vad är din adress?",
            "Tack. Jag eskalerar direkt till Magnus och han ringer dig inom 5 minuter. Stanna utanför tills räddningstjänsten kommer.",
        ],
    ),
    "stromost_el": ScenarioPreset(
        id="stromost_el",
        name_sv="Strömlöst hela bostaden — akut (el)",
        description_sv="Kunden ringer en el-firma; strömlöst hela huset. Bör triggas som AKUT/HIGH för el-trade.",
        trade=Trade.EL,
        expected_intent=Intent.AKUT,
        expected_severity=Severity.HIGH,
        caller_phone="+46708554444",
        caller_turns=[
            "Det är strömlöst i hela huset, ingenting fungerar. Jag har tre små barn här.",
            "Eriksgatan 22, Sundbyberg.",
        ],
    ),
    "ovk_b2b_bokning": ScenarioPreset(
        id="ovk_b2b_bokning",
        name_sv="OVK-bokning B2B (Brf-förvaltare)",
        description_sv="Karim på Brf Vasaliljan vill boka in OVK-besiktningar i fyra fastigheter. Bör triggas som BOKNING.",
        trade=Trade.VVS,
        expected_intent=Intent.BOKNING,
        expected_severity=None,
        caller_phone="+46708558888",
        caller_turns=[
            "Hej det är Karim på Brf Vasaliljan. Jag behöver boka in OVK i fyra fastigheter.",
            "Vasagatan 8, 10 och 12 plus Karlbergsvägen 22.",
            "Den 22:a fungerar.",
        ],
    ),
    "badrumsrenovering_offert": ScenarioPreset(
        id="badrumsrenovering_offert",
        name_sv="Badrumsrenovering — offertförfrågan",
        description_sv="Privatperson vill ha offert på badrumsrenovering. Bör triggas som OFFERT, lead skapad, foto-länk skickad.",
        trade=Trade.VVS,
        expected_intent=Intent.OFFERT,
        expected_severity=None,
        caller_phone="+46708559999",
        caller_turns=[
            "Hej, vi vill ha offert på badrumsrenovering. Det är ett gammalt 70-tals badrum.",
            "Hökarängsplan 4 i Stockholm. Cirka 5 kvadrat.",
            "Pelle Lundgren, ja.",
        ],
    ),
    "befintlig_kund_status": ScenarioPreset(
        id="befintlig_kund_status",
        name_sv="Befintlig kund — fråga om pågående jobb",
        description_sv="Returnerande kund frågar om sitt pågående arbete. Bör triggas som BEFINTLIG_KUND, eskaleras med meddelande.",
        trade=Trade.VVS,
        expected_intent=Intent.BEFINTLIG_KUND,
        expected_severity=None,
        caller_phone="+46708557777",
        caller_turns=[
            "Hej det är Inger igen. Hur går det med badrumsjobbet?",
        ],
    ),
    "telemarketing_avslag": ScenarioPreset(
        id="telemarketing_avslag",
        name_sv="Telemarketing — fellringd",
        description_sv="Telefonförsäljning. AI ska identifiera som ÖVRIGT och avsluta artigt med meddelande.",
        trade=Trade.OVRIGT,
        expected_intent=Intent.OVRIGT,
        expected_severity=None,
        caller_phone="+46101234567",
        caller_turns=[
            "Hej! Vi har ett fantastiskt erbjudande på telefoniabonnemang för företagare.",
            "Är ni intresserade av att höra mer?",
        ],
    ),
}


_INDICATOR_KEYWORDS: list[tuple[str, EmergencyIndicator]] = [
    ("läcka", EmergencyIndicator.LACKA),
    ("rinner", EmergencyIndicator.RINNER),
    ("strömlös", EmergencyIndicator.STROMLOST),
    ("ström", EmergencyIndicator.STROMLOST),
    ("ingen värme", EmergencyIndicator.INGEN_VARME),
    ("gas", EmergencyIndicator.GAS_LUKT),
    ("brand", EmergencyIndicator.BRAND),
    ("rök", EmergencyIndicator.BRAND),
    ("avlopp", EmergencyIndicator.AVLOPP_STOPP),
    ("stopp", EmergencyIndicator.AVLOPP_STOPP),
]


def _detect_indicators(text: str) -> list[EmergencyIndicator]:
    lower = text.lower()
    seen: set[EmergencyIndicator] = set()
    for needle, ind in _INDICATOR_KEYWORDS:
        if needle in lower:
            seen.add(ind)
    return sorted(seen, key=lambda i: i.value)


def _classify(turns: list[str], trade: Trade, *, is_winter: bool) -> tuple[Intent, Severity | None]:
    text = " ".join(turns).lower()
    indicators: list[EmergencyIndicator] = []
    for turn in turns:
        for ind in _detect_indicators(turn):
            if ind not in indicators:
                indicators.append(ind)
    triage = triage_service.assess(text, trade, indicators, is_winter=is_winter)
    if triage.is_emergency:
        return Intent.AKUT, triage.severity
    if "boka" in text or "ovk" in text:
        return Intent.BOKNING, None
    if "offert" in text or "renovering" in text:
        return Intent.OFFERT, None
    if "hur går det" in text or "fakturan" in text or "min tid" in text:
        return Intent.BEFINTLIG_KUND, None
    return Intent.OVRIGT, None


# Per-intent canonical playbook of tool calls. Each entry: tool name +
# fn(turns, scenario) -> args. Real production calls follow these
# playbooks; the scenario runner just runs them deterministically.
def _build_args_for_tool(
    tool: ToolName, preset: ScenarioPreset, intent: Intent, severity: Severity | None
) -> dict[str, object]:
    last_caller = preset.caller_turns[-1] if preset.caller_turns else ""
    full_text = " ".join(preset.caller_turns)
    if tool is ToolName.LOOKUP_CUSTOMER:
        return {"phone_number": preset.caller_phone}
    if tool is ToolName.TRIAGE_EMERGENCY:
        return {
            "problem_description": full_text,
            "trade": preset.trade.value,
            "indicators_present": [i.value for i in _detect_indicators(full_text)],
        }
    if tool is ToolName.ESCALATE_TO_OWNER:
        return {
            "severity": (severity or Severity.HIGH).value,
            "reason_sv": full_text[:120],
            "customer_phone": preset.caller_phone,
        }
    if tool is ToolName.SEND_SMS_FOLLOWUP:
        if intent is Intent.AKUT:
            return {
                "to_phone": preset.caller_phone,
                "template": SmsTemplate.EMERGENCY_ACK.value,
                "context_data": {"name": "kund", "owner_name": "Magnus", "window": "15 min"},
            }
        return {
            "to_phone": preset.caller_phone,
            "template": SmsTemplate.BOOKING_CONFIRMATION.value,
            "context_data": {"name": "kund", "time": "den 22:a maj 08:00", "address": last_caller},
        }
    if tool is ToolName.CREATE_LEAD:
        return {
            "name": "Ny lead",
            "phone": preset.caller_phone,
            "type": CustomerType.PRIVATE.value,
            "problem_summary_sv": full_text[:200],
        }
    if tool is ToolName.REQUEST_PHOTO_UPLOAD:
        return {
            "to_phone": preset.caller_phone,
            "lead_or_customer_id": "pending",
            "expires_hours": 168,
        }
    if tool is ToolName.CHECK_AVAILABILITY:
        return {
            "duration_minutes": 60,
            "earliest_date": utcnow().date().isoformat(),
            "latest_date": (utcnow().date()).isoformat(),
            "required_skills": [],
            "address": last_caller,
        }
    if tool is ToolName.BOOK_APPOINTMENT:
        return {
            "customer_id": "pending",
            "start_iso": utcnow().isoformat(),
            "duration_minutes": 60,
            "address": last_caller,
            "problem_summary_sv": full_text[:200],
            "rot_eligible": False,
        }
    if tool is ToolName.LOOKUP_JOB_STATUS:
        return {"customer_id": "pending", "job_query_sv": last_caller}
    if tool is ToolName.TAKE_MESSAGE:
        return {
            "caller_phone": preset.caller_phone,
            "topic_sv": full_text[:200],
            "urgency": Urgency.LOW.value,
        }
    return {}


_PLAYBOOK: dict[Intent, list[ToolName]] = {
    Intent.AKUT: [
        ToolName.LOOKUP_CUSTOMER,
        ToolName.TRIAGE_EMERGENCY,
        ToolName.ESCALATE_TO_OWNER,
        ToolName.SEND_SMS_FOLLOWUP,
    ],
    Intent.BOKNING: [
        ToolName.LOOKUP_CUSTOMER,
        ToolName.CHECK_AVAILABILITY,
        ToolName.BOOK_APPOINTMENT,
        ToolName.SEND_SMS_FOLLOWUP,
    ],
    Intent.OFFERT: [
        ToolName.LOOKUP_CUSTOMER,
        ToolName.CREATE_LEAD,
        ToolName.REQUEST_PHOTO_UPLOAD,
    ],
    Intent.BEFINTLIG_KUND: [
        ToolName.LOOKUP_CUSTOMER,
        ToolName.LOOKUP_JOB_STATUS,
        ToolName.TAKE_MESSAGE,
    ],
    Intent.OVRIGT: [ToolName.TAKE_MESSAGE],
}


def list_presets() -> list[ScenarioPreset]:
    return list(PRESETS.values())


def get_preset(preset_id: str) -> ScenarioPreset | None:
    return PRESETS.get(preset_id)


def run_preset(session: Session, firma_id: str, preset_id: str) -> ScenarioResult:
    preset = get_preset(preset_id)
    if preset is None:
        msg = f"unknown_preset:{preset_id}"
        raise ValueError(msg)
    return run_scenario(session, firma_id, preset)


def run_scenario(
    session: Session,
    firma_id: str,
    preset: ScenarioPreset,
) -> ScenarioResult:
    """Execute the scenario end-to-end. Persists a real Call row."""
    firma = session.get(Firma, firma_id)
    if firma is None:
        msg = f"firma_not_found:{firma_id}"
        raise ValueError(msg)

    with firma_context(firma_id):
        intent, severity = _classify(
            preset.caller_turns, preset.trade, is_winter=preset.is_winter
        )

        call = Call(
            id=new_id(),
            firma_id=firma_id,
            caller_phone=preset.caller_phone,
            status=CallStatus.IN_PROGRESS,
            source=CallSource.SCENARIO,
            intent=intent,
            severity=severity,
            gemini_session_id=f"{CallSource.SCENARIO.value}:{preset.id}",
        )
        session.add(call)
        session.commit()
        session.refresh(call)

        ctx = ToolContext(session=session, firma_id=firma_id, call_id=call.id)
        tool_names: list[ToolName] = []

        ai_turns_iter = iter(preset.ai_turns)
        for i, caller_text in enumerate(preset.caller_turns):
            ts = i * 5_000
            session.add(
                TranscriptSegment(
                    call_id=call.id,
                    role=TranscriptRole.CALLER,
                    text=caller_text,
                    ts_ms_offset=ts,
                )
            )
            ai_text = next(ai_turns_iter, _synthesize_ai_response(intent, severity))
            session.add(
                TranscriptSegment(
                    call_id=call.id,
                    role=TranscriptRole.AI,
                    text=ai_text,
                    ts_ms_offset=ts + 2_000,
                )
            )
        session.commit()

        for tool in _PLAYBOOK[intent]:
            args = _build_args_for_tool(tool, preset, intent, severity)
            try:
                tool_dispatch(ctx, tool.value, args)
                tool_names.append(tool)
            except Exception:  # noqa: BLE001
                log.exception("scenario.tool_failed", tool=tool.value, preset=preset.id)

        call.ended_at = utcnow()
        call.status = CallStatus.HANDLED
        call.billing_seconds = max(30, len(preset.caller_turns) * 8)
        session.add(call)
        session.commit()

        # Run the heuristic post-call summarizer so the dashboard sees a complete row.
        from switchboard.agents import post_call_summary

        summary = post_call_summary.summarize_call(call.id)

        audit_service.record(
            session,
            actor=AuditActor.ADMIN,
            action=AuditAction.SCENARIO_RUN,
            target_type=AuditTargetType.CALL,
            target_id=call.id,
            payload={
                "preset_id": preset.id,
                "intent": intent.value,
                "severity": severity.value if severity else None,
                "tools": [t.value for t in tool_names],
            },
        )

        return ScenarioResult(
            call_id=call.id,
            intent=intent,
            severity=severity,
            tool_invocations=tool_names,
            summary_short=summary.short_sv if summary else None,
        )


def _synthesize_ai_response(intent: Intent, severity: Severity | None) -> str:
    if intent == Intent.AKUT:
        if severity == Severity.CRITICAL:
            return "Det här är akut. Ring 112 omedelbart. Jag eskalerar samtidigt till Magnus."
        return "Det låter akut. Magnus ringer dig inom 15 minuter."
    if intent == Intent.BOKNING:
        return "Jag bokar in det. Du får bekräftelse via SMS."
    if intent == Intent.OFFERT:
        return "Tack. Magnus återkommer med offert. Jag skickar dig en länk för att ladda upp foton."
    if intent == Intent.BEFINTLIG_KUND:
        return "Jag tar ett meddelande till Magnus så återkommer han."
    return "Tack för samtalet. Vi hör av oss om det skulle behövas."


# Async-friendly wrapper for the FastAPI route.
async def run_preset_async(session: Session, firma_id: str, preset_id: str) -> ScenarioResult:
    return await asyncio.to_thread(run_preset, session, firma_id, preset_id)

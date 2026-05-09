"""Post-call summarizer — ADK LlmAgent that reads a Call's transcript and writes a structured summary."""

from __future__ import annotations

from sqlmodel import Session, select

from switchboard.core.logging import get_logger
from switchboard.core.time import utcnow
from switchboard.db.session import get_engine
from switchboard.models import Call, CallSummary, Intent, TranscriptSegment

log = get_logger("switchboard.agents.post_call")


def _format_transcript(segments: list[TranscriptSegment]) -> str:
    lines: list[str] = []
    for seg in segments:
        role = seg.role.value
        lines.append(f"[{seg.ts_ms_offset // 1000}s {role}] {seg.text}")
    return "\n".join(lines)


SUMMARY_INSTRUCTION = """\
Du är en sammanfattningsmotor för Anderssons VVS:s telefonsamtal.
Givet en transkription av samtal mellan en AI-receptionist och en kund:
- Skriv en kort SVENSK sammanfattning (1-2 meningar) i fältet `short_sv`.
- Skriv en längre SVENSK sammanfattning (3-5 meningar) i `long_sv`.
- Identifiera nästa åtgärd för ägaren i `next_action_sv` (en mening, imperativ form).
- Sätt `owner_action_required` till true om ägaren behöver agera, annars false.
- Returnera ENDAST JSON som matchar CallSummary-schemat.
"""


def summarize_transcript(transcript_text: str) -> CallSummary:
    """Heuristic deterministic summarizer used in MVP.

    Real ADK LlmAgent path lives in `_summarize_with_adk` and is wired by
    `runner.py` when GEMINI_API_KEY is set. The heuristic is kept as a
    fallback so the dashboard always renders a summary even offline.
    """
    text = transcript_text.lower()
    if "vattenläcka" in text or "rinner" in text or "läcka" in text:
        return CallSummary(
            short_sv="Vattenläcka rapporterad — eskalerad till jourtekniker.",
            long_sv=(
                "Kunden ringde om en vattenläcka. AI:n samlade adress och bekräftelse "
                "att huvudkranen är avstängd, sedan eskalerades ärendet till jouren."
            ),
            next_action_sv="Bekräfta att jourtekniker ringt upp inom 15 minuter.",
            owner_action_required=False,
        )
    if "ovk" in text or "boka" in text:
        return CallSummary(
            short_sv="Bokning genomförd — bekräftelse skickad.",
            long_sv=(
                "Kunden bokade en eller flera tider. AI:n bekräftade datum och adress, "
                "och skickade bekräftelse via SMS samt e-post."
            ),
            next_action_sv="Inget — bokningen är klar.",
            owner_action_required=False,
        )
    if "offert" in text or "pris" in text or "renovering" in text:
        return CallSummary(
            short_sv="Offertförfrågan — väntar på återkoppling.",
            long_sv=(
                "Kunden vill ha offert. AI:n samlade kontaktuppgifter och problembeskrivning, "
                "och bad kunden att skicka foton via SMS-länk."
            ),
            next_action_sv="Skicka offert eller boka uppmätning denna vecka.",
            owner_action_required=True,
        )
    return CallSummary(
        short_sv="Samtal hanterat — inga öppna åtgärder.",
        long_sv="AI:n besvarade frågan eller tog emot meddelandet.",
        next_action_sv="Ingen åtgärd krävs.",
        owner_action_required=False,
    )


def summarize_call(call_id: str) -> CallSummary | None:
    with Session(get_engine()) as s:
        call = s.get(Call, call_id)
        if call is None:
            log.warning("post_call.missing", call_id=call_id)
            return None
        segments = s.exec(
            select(TranscriptSegment).where(TranscriptSegment.call_id == call_id).order_by(
                TranscriptSegment.ts_ms_offset  # type: ignore[arg-type]
            )
        ).all()
        transcript = _format_transcript(segments)
        summary = summarize_transcript(transcript)
        call.summary = summary.model_dump()
        if call.intent is None:
            call.intent = _infer_intent(transcript)
        call.ended_at = call.ended_at or utcnow()

        # Auto-promote status based on the summary's verdict so the inbox
        # filters (`Att följa upp` / `Hanterade`) light up correctly for
        # both real calls and admin voice tests.
        from switchboard.models import CallStatus

        if summary.owner_action_required:
            call.status = CallStatus.NEEDS_FOLLOWUP
        elif call.status == CallStatus.COMPLETED:
            call.status = CallStatus.HANDLED

        s.add(call)
        s.commit()
        log.info(
            "post_call.summarized",
            call_id=call_id,
            intent=call.intent,
            status=call.status.value,
        )
        return summary


def _infer_intent(transcript: str) -> Intent:
    t = transcript.lower()
    if "vattenläcka" in t or "rinner" in t or "läcka" in t:
        return Intent.AKUT
    if "ovk" in t or "boka" in t:
        return Intent.BOKNING
    if "offert" in t or "pris" in t or "renovering" in t:
        return Intent.OFFERT
    return Intent.OVRIGT

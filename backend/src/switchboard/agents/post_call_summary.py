"""Post-call summarizer — reads the transcript with Gemini and writes a structured summary."""

from __future__ import annotations

import json

from sqlmodel import Session, select

from switchboard.core.config import get_settings
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


SUMMARY_PROMPT = """\
Du är en sammanfattningsmotor för ett VVS-företags telefonsamtal.
Nedan är en transkription av ett samtal mellan en AI-receptionist och en kund.

Extrahera och returnera ENDAST ett JSON-objekt med dessa fält:
- short_sv: 1-2 meningar. Inkludera kundens namn och adress om de samlades in.
- long_sv: 3-5 meningar. Beskriv vad kunden ville, vad som samlades in (namn, adress, ärendetyp), och vad som hände.
- next_action_sv: En mening i imperativform om vad ägaren behöver göra härnäst.
- owner_action_required: true om ägaren behöver agera, annars false.

Returnera ENDAST JSON, inget annat.

Transkription:
{transcript}
"""


def summarize_transcript(transcript_text: str) -> CallSummary:
    settings = get_settings()
    if settings.gemini_api_key:
        try:
            return _summarize_with_gemini(transcript_text, settings.gemini_api_key)
        except Exception:
            log.exception("post_call.gemini_failed — falling back to heuristic")
    return _heuristic_summary(transcript_text)


def _summarize_with_gemini(transcript_text: str, api_key: str) -> CallSummary:
    from google import genai

    client = genai.Client(
        http_options={"api_version": "v1beta"},
        api_key=api_key,
    )
    prompt = SUMMARY_PROMPT.format(transcript=transcript_text)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    raw = response.text or ""
    # Strip markdown code fences if present
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    data = json.loads(raw)
    return CallSummary(**data)


def _heuristic_summary(text: str) -> CallSummary:
    t = text.lower()
    if "vattenläcka" in t or "rinner" in t or "läcka" in t:
        return CallSummary(
            short_sv="Vattenläcka rapporterad — eskalerad till jourtekniker.",
            long_sv="Kunden ringde om en vattenläcka. Ärendet eskalerades till jouren.",
            next_action_sv="Bekräfta att jourtekniker ringt upp inom 15 minuter.",
            owner_action_required=False,
        )
    if "offert" in t or "pris" in t or "renovering" in t:
        return CallSummary(
            short_sv="Offertförfrågan mottagen.",
            long_sv="Kunden vill ha offert. Kontaktuppgifter och problembeskrivning samlades in.",
            next_action_sv="Skicka offert eller boka uppmätning denna vecka.",
            owner_action_required=True,
        )
    if "boka" in t or "ovk" in t:
        return CallSummary(
            short_sv="Bokning genomförd.",
            long_sv="Kunden bokade en tid. Bekräftelse skickad.",
            next_action_sv="Inget — bokningen är klar.",
            owner_action_required=False,
        )
    return CallSummary(
        short_sv="Samtal hanterat.",
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
        s.add(call)
        s.commit()
        log.info("post_call.summarized", call_id=call_id, intent=call.intent)
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

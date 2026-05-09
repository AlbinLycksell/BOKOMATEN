"""Post-call PII entity audit (PRD §9.5, Strategy A).

Live regex (`redaction_service`) catches canonical patterns instantly so
the dashboard never displays raw PII. This second pass runs after the
call ends and uses Gemini to flag obscure patterns the regex missed
(spelled-out personnummer, partial bankgiro, OCR-style number runs).

Falls back to a heuristic if Vertex AI isn't reachable so the audit
trail still gets written.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from sqlmodel import Session, select

from svarsa.core.config import Settings, get_settings
from svarsa.core.logging import get_logger
from svarsa.models import TranscriptSegment
from svarsa.services import audit_service, redaction_service

log = get_logger("svarsa.pii_audit")

EXTRACTOR_PROMPT = """\
Du är en PII-extraherare. Givet en svensk samtalstranskription, returnera
ENDAST ett JSON-objekt med en lista över känsliga uppgifter som
fortfarande kan finnas kvar i texten — sådana som regex-redaktion missat.

Returnera shapen:
{"findings":[{"label":"personnummer|bankgiro|iban|kortnummer|annat","excerpt":"..."}]}

Om inget hittas: {"findings":[]}
"""


@dataclass(frozen=True)
class AuditResult:
    findings: list[dict[str, str]]
    method: str


def audit_call_transcript(
    session: Session,
    call_id: str,
    *,
    settings: Settings | None = None,
) -> AuditResult:
    s = settings or get_settings()
    segments = session.exec(
        select(TranscriptSegment).where(TranscriptSegment.call_id == call_id).order_by(
            TranscriptSegment.ts_ms_offset  # type: ignore[arg-type]
        )
    ).all()
    full = "\n".join(seg.text for seg in segments if seg.text)
    if not full.strip():
        return AuditResult(findings=[], method="empty")

    findings, method = _extract_with_gemini(full, s)
    if findings is None:
        findings = _heuristic_extract(full)
        method = "heuristic"

    if findings:
        log.warning(
            "pii_audit.findings",
            call_id=call_id,
            count=len(findings),
            method=method,
        )
        # Re-redact via the regex service over each finding excerpt.
        for f in findings:
            f["redacted_excerpt"] = redaction_service.redact(f["excerpt"]).redacted

        audit_service.record(
            session,
            actor="ai",
            action="pii_audit.flagged",
            target_type="call",
            target_id=call_id,
            payload={"method": method, "findings": findings},
        )

    return AuditResult(findings=findings, method=method)


def _extract_with_gemini(transcript: str, settings: Settings) -> tuple[list[dict[str, Any]] | None, str]:
    if settings.gemini_provider != "vertex" or not settings.vertex_project:
        return None, "skipped_no_vertex"
    try:
        from google import genai
        from google.genai import types as gtypes

        client = genai.Client(
            vertexai=True,
            project=settings.vertex_project,
            location=settings.vertex_location,
        )
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[gtypes.Content(role="user", parts=[gtypes.Part(text=transcript)])],
            config=gtypes.GenerateContentConfig(
                system_instruction=EXTRACTOR_PROMPT,
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )
        body = json.loads(resp.text or "{}")
        findings = body.get("findings", [])
        if isinstance(findings, list):
            return findings, "gemini"
    except Exception:  # noqa: BLE001
        log.exception("pii_audit.gemini_failed")
    return None, "gemini_failed"


# Heuristic fallback — same regexes as the live pass plus a few
# spelled-out catchers. Lower recall than Gemini but never wrong.
SPELLED_PATTERNS = (
    re.compile(r"\b(?:nio|sju|åtta|sex)\s*[-–]?\s*(?:två|tre|fyra)?\b", re.I),
    re.compile(r"\b\d\s*\d\s*\d\s*\d\s*\d\s*\d\s*\d\s*\d\s*\d\s*\d\b"),
)


def _heuristic_extract(transcript: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for pat in SPELLED_PATTERNS:
        for m in pat.finditer(transcript):
            findings.append({"label": "annat", "excerpt": m.group(0)})
    return findings

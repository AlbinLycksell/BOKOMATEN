"""Live PII masking on transcript text (PRD §9.5).

Catches Swedish personnummer (`YYYYMMDD-NNNN`, `YYMMDD-NNNN`,
`YYMMDDNNNN`), Swedish bankgirot/plusgirot, and IBAN-shaped sequences.
Audits every redaction so a missed pattern can be replayed and the
classifier improved.

Strategy A from the input form: live regex now + post-call entity audit
later (Step 13 of next-steps).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from switchboard.core.logging import get_logger

log = get_logger("switchboard.redaction")


# YYYYMMDD-NNNN, YYMMDD-NNNN, YYMMDDNNNN (modern + classic + glued)
_PERSONNUMMER = re.compile(
    r"\b(?:\d{2})?\d{6}[-+ ]?\d{4}\b",
)
# Bankgiro (3-4 digits dash 4 digits) — SEK 1000-1234
_BANKGIRO = re.compile(r"\b\d{3,4}-\d{4}\b")
# IBAN (Swedish IBAN: SE + 22 alnum)
_IBAN = re.compile(r"\bSE\d{2}[ ]?\d{4}[ ]?\d{4}[ ]?\d{4}[ ]?\d{4}[ ]?\d{4}\b", re.I)
# Card-shaped 16 digits with optional spaces/dashes
_CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")


@dataclass(frozen=True)
class RedactionResult:
    redacted: str
    spans: list[tuple[str, str]]  # list of (label, original_excerpt)


def redact(text: str) -> RedactionResult:
    spans: list[tuple[str, str]] = []
    out = text

    def _replace(pattern: re.Pattern[str], label: str, mask: str) -> None:
        nonlocal out
        for m in pattern.finditer(out):
            spans.append((label, m.group(0)))
        out = pattern.sub(mask, out)

    _replace(_PERSONNUMMER, "personnummer", "[PERSONNUMMER]")
    _replace(_IBAN, "iban", "[IBAN]")
    _replace(_BANKGIRO, "bankgiro", "[BANKGIRO]")
    _replace(_CARD, "card_number", "[CARD]")

    if spans:
        log.warning(
            "redaction.applied",
            count=len(spans),
            labels=[label for label, _ in spans],
        )
    return RedactionResult(redacted=out, spans=spans)

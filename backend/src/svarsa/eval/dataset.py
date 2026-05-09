"""Eval dataset format and loader.

Each labeled call is a JSONL row at ``gs://svarsa-eval-dataset/v1/`` (or a
local path during development):

    {
      "call_id": "stable-id",
      "transcript": [{"role":"caller","text":"..."}, {"role":"ai","text":"..."}],
      "expected_intent": "akut",
      "expected_severity": "high",
      "expected_tools": ["lookup_customer", "triage_emergency", "escalate_to_owner"],
      "expected_recommended_action": "escalate_now",
      "trade": "vvs",
      "notes": "free-text annotator notes"
    }
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from svarsa.models.enums import Intent, Severity


@dataclass(frozen=True)
class LabeledTurn:
    role: str
    text: str


@dataclass(frozen=True)
class LabeledCall:
    call_id: str
    transcript: list[LabeledTurn]
    expected_intent: Intent
    expected_severity: Severity | None
    expected_tools: list[str] = field(default_factory=list)
    expected_recommended_action: str | None = None
    trade: str = "vvs"
    notes: str = ""


def load_dataset(path: str | Path) -> list[LabeledCall]:
    p = Path(path)
    out: list[LabeledCall] = []
    with p.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            out.append(_row_to_call(row))
    return out


def _row_to_call(row: dict) -> LabeledCall:
    return LabeledCall(
        call_id=row["call_id"],
        transcript=[
            LabeledTurn(role=t["role"], text=t["text"]) for t in row["transcript"]
        ],
        expected_intent=Intent(row["expected_intent"]),
        expected_severity=Severity(row["expected_severity"]) if row.get("expected_severity") else None,
        expected_tools=list(row.get("expected_tools", [])),
        expected_recommended_action=row.get("expected_recommended_action"),
        trade=row.get("trade", "vvs"),
        notes=row.get("notes", ""),
    )

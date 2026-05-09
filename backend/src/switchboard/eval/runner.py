"""Eval replay harness.

Two evaluation modes share the same dataset shape:

- **Triage replay** — feed the caller-side transcript into
  `triage_service.assess` directly (no LLM round-trip). This is a fast,
  deterministic gate over our rule-based classifier.
- **Live replay (TODO)** — for prompt-tuning eval, replay the actual
  caller audio against a Live API session and score the resulting tool
  calls. Wired here in the next iteration; ADK eval already has the
  primitives.

Outputs a `EvalReport` consumed by the weekly Slack digest workflow.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from switchboard.eval.dataset import LabeledCall
from switchboard.models.enums import EmergencyIndicator, Intent, Trade
from switchboard.services import triage_service


@dataclass
class CallEvalResult:
    call_id: str
    intent_match: bool
    severity_match: bool
    actual_intent: Intent | None
    actual_severity: str | None


@dataclass
class EvalReport:
    total: int = 0
    intent_correct: int = 0
    severity_correct: int = 0
    emergency_false_negatives: int = 0
    by_intent: Counter[str] = field(default_factory=Counter)
    failures: list[CallEvalResult] = field(default_factory=list)

    @property
    def intent_accuracy(self) -> float:
        return self.intent_correct / max(self.total, 1)

    @property
    def severity_accuracy(self) -> float:
        return self.severity_correct / max(self.total, 1)


def run(dataset: list[LabeledCall]) -> EvalReport:
    report = EvalReport()
    for call in dataset:
        report.total += 1
        report.by_intent[call.expected_intent.value] += 1
        actual = _classify(call)
        intent_match = actual.actual_intent == call.expected_intent
        severity_match = actual.actual_severity == (
            call.expected_severity.value if call.expected_severity else None
        )
        if intent_match:
            report.intent_correct += 1
        if severity_match:
            report.severity_correct += 1
        if call.expected_intent == Intent.AKUT and actual.actual_intent != Intent.AKUT:
            report.emergency_false_negatives += 1
        if not intent_match or not severity_match:
            report.failures.append(actual)
    return report


def _classify(call: LabeledCall) -> CallEvalResult:
    """Heuristic classifier — same rules the production triage service uses."""
    caller_text = " ".join(
        t.text for t in call.transcript if t.role == "caller"
    ).lower()
    indicators: list[EmergencyIndicator] = []
    keywords = {
        "läcka": EmergencyIndicator.LACKA,
        "rinner": EmergencyIndicator.RINNER,
        "strömlöst": EmergencyIndicator.STROMLOST,
        "ingen värme": EmergencyIndicator.INGEN_VARME,
        "gas": EmergencyIndicator.GAS_LUKT,
        "brand": EmergencyIndicator.BRAND,
        "stopp": EmergencyIndicator.AVLOPP_STOPP,
    }
    for needle, ind in keywords.items():
        if needle in caller_text:
            indicators.append(ind)

    triage = triage_service.assess(caller_text, Trade(call.trade), indicators)
    actual_intent: Intent | None
    if triage.is_emergency:
        actual_intent = Intent.AKUT
    elif "boka" in caller_text or "ovk" in caller_text:
        actual_intent = Intent.BOKNING
    elif "offert" in caller_text or "renovering" in caller_text:
        actual_intent = Intent.OFFERT
    else:
        actual_intent = Intent.OVRIGT
    return CallEvalResult(
        call_id=call.call_id,
        intent_match=actual_intent == call.expected_intent,
        severity_match=(
            triage.severity.value
            == (call.expected_severity.value if call.expected_severity else None)
        ),
        actual_intent=actual_intent,
        actual_severity=triage.severity.value,
    )


def format_slack_digest(report: EvalReport) -> str:
    lines = [
        f"*Switchboard eval — n={report.total}*",
        f"  Intent accuracy: {report.intent_accuracy:.1%}",
        f"  Severity accuracy: {report.severity_accuracy:.1%}",
        f"  Emergency false negatives: {report.emergency_false_negatives}/{report.by_intent.get('akut', 0)}",
        "",
        "Distribution:",
    ]
    for intent, count in report.by_intent.most_common():
        lines.append(f"  {intent}: {count}")
    if report.failures:
        lines.append(f"\nFailures ({len(report.failures)}, first 5):")
        for f in report.failures[:5]:
            lines.append(
                f"  • {f.call_id}: intent={f.actual_intent}, severity={f.actual_severity}"
            )
    return "\n".join(lines)

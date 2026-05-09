"""Rule-based emergency classification per PRD §7.3.

Defaults err toward escalation when uncertain — false-negatives are catastrophic.
"""

from __future__ import annotations

from switchboard.models.enums import EmergencyIndicator, Severity, Trade
from switchboard.tools.schemas import TriageEmergencyResult

CRITICAL_VVS_INDICATORS: frozenset[EmergencyIndicator] = frozenset(
    {EmergencyIndicator.GAS_LUKT, EmergencyIndicator.BRAND}
)
HIGH_VVS_INDICATORS: frozenset[EmergencyIndicator] = frozenset(
    {EmergencyIndicator.LACKA, EmergencyIndicator.RINNER, EmergencyIndicator.AVLOPP_STOPP}
)
HIGH_EL_INDICATORS: frozenset[EmergencyIndicator] = frozenset(
    {EmergencyIndicator.STROMLOST, EmergencyIndicator.BRAND}
)
WINTER_VARME_INDICATORS: frozenset[EmergencyIndicator] = frozenset(
    {EmergencyIndicator.INGEN_VARME}
)


def assess(
    problem_description: str,
    trade: Trade,
    indicators: list[EmergencyIndicator],
    *,
    is_winter: bool = True,
) -> TriageEmergencyResult:
    indicator_set = set(indicators)
    text = problem_description.lower()

    if EmergencyIndicator.GAS_LUKT in indicator_set or "gas" in text:
        return TriageEmergencyResult(
            is_emergency=True,
            severity=Severity.CRITICAL,
            recommended_action="escalate_now",
            reasoning_sv="Gas-lukt rapporterad — kritiskt, ring räddningstjänsten 112 och eskalera.",
        )

    if EmergencyIndicator.BRAND in indicator_set or "brand" in text or "rök" in text:
        return TriageEmergencyResult(
            is_emergency=True,
            severity=Severity.CRITICAL,
            recommended_action="escalate_now",
            reasoning_sv="Brand-relaterat — kritiskt. Eskalera och hänvisa till 112.",
        )

    if trade == Trade.VVS:
        if indicator_set & HIGH_VVS_INDICATORS:
            return TriageEmergencyResult(
                is_emergency=True,
                severity=Severity.HIGH,
                recommended_action="escalate_now",
                reasoning_sv="Vatten/avlopp-akut — eskalera till jourtekniker omedelbart.",
            )
        if is_winter and (indicator_set & WINTER_VARME_INDICATORS):
            return TriageEmergencyResult(
                is_emergency=True,
                severity=Severity.HIGH,
                recommended_action="escalate_now",
                reasoning_sv="Ingen värme i vinter — räknas som akut.",
            )

    if trade == Trade.EL:
        if indicator_set & HIGH_EL_INDICATORS:
            return TriageEmergencyResult(
                is_emergency=True,
                severity=Severity.HIGH,
                recommended_action="escalate_now",
                reasoning_sv="Strömlöst hela bostaden eller brand-tecken — eskalera direkt.",
            )

    if any(word in text for word in ("akut", "rinner", "läcka", "stänga av", "vatten överallt")):
        return TriageEmergencyResult(
            is_emergency=True,
            severity=Severity.MEDIUM,
            recommended_action="book_today",
            reasoning_sv="Texten antyder akut situation — boka samma dag eller eskalera.",
        )

    return TriageEmergencyResult(
        is_emergency=False,
        severity=Severity.LOW,
        recommended_action="book_normal",
        reasoning_sv="Inga akut-indikatorer hittade — planerat arbete.",
    )

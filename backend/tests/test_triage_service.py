from __future__ import annotations

from switchboard.models.enums import EmergencyIndicator, Severity, Trade
from switchboard.services import triage_service


def test_water_leak_with_running_water_is_high_severity() -> None:
    res = triage_service.assess(
        "vattenläcka, det rinner ner på golvet",
        Trade.VVS,
        [EmergencyIndicator.LACKA, EmergencyIndicator.RINNER],
    )
    assert res.is_emergency is True
    assert res.severity is Severity.HIGH
    assert res.recommended_action == "escalate_now"


def test_gas_smell_is_critical_regardless_of_trade() -> None:
    res = triage_service.assess(
        "Det luktar gas i hela köket",
        Trade.VVS,
        [EmergencyIndicator.GAS_LUKT],
    )
    assert res.severity is Severity.CRITICAL
    assert "112" in res.reasoning_sv


def test_no_indicators_returns_normal_booking() -> None:
    res = triage_service.assess(
        "Vill ha offert på badrumsrenovering",
        Trade.VVS,
        [],
    )
    assert res.is_emergency is False
    assert res.recommended_action == "book_normal"


def test_winter_no_heat_is_high() -> None:
    res = triage_service.assess(
        "Värmen funkar inte alls",
        Trade.VVS,
        [EmergencyIndicator.INGEN_VARME],
        is_winter=True,
    )
    assert res.severity is Severity.HIGH


def test_summer_no_heat_is_not_high() -> None:
    res = triage_service.assess(
        "Värmen funkar inte alls",
        Trade.VVS,
        [EmergencyIndicator.INGEN_VARME],
        is_winter=False,
    )
    assert res.severity is Severity.LOW

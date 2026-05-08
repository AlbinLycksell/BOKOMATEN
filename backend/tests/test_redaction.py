from __future__ import annotations

from svarsa.services.redaction_service import redact


def test_personnummer_yyyymmdd_dash() -> None:
    res = redact("Mitt personnummer är 19850525-1234, kan ni boka?")
    assert "[PERSONNUMMER]" in res.redacted
    assert "19850525-1234" not in res.redacted
    assert any(label == "personnummer" for label, _ in res.spans)


def test_personnummer_yymmdd_glued() -> None:
    res = redact("8505251234")
    assert res.redacted == "[PERSONNUMMER]"


def test_swedish_iban() -> None:
    res = redact("Skicka till SE45 5000 0000 0583 9825 7466 tack")
    assert "[IBAN]" in res.redacted


def test_bankgiro() -> None:
    res = redact("Bankgiro 1234-5678")
    assert "[BANKGIRO]" in res.redacted


def test_no_false_positive_phone() -> None:
    res = redact("Du kan ringa mig på 070-555 12 34")
    assert "[PERSONNUMMER]" not in res.redacted


def test_clean_text_passes_through() -> None:
    text = "Hej det är vattenläcka under diskbänken"
    assert redact(text).redacted == text
    assert redact(text).spans == []

from __future__ import annotations

from sqlmodel import Session, select

from switchboard.db.seed import DEMO_FIRMA_ID, seed_dev_data
from switchboard.db.session import get_engine, init_db
from switchboard.models import Call, Customer, Firma


def test_seed_inserts_demo_firma_with_calls() -> None:
    init_db()
    seed_dev_data()
    seed_dev_data()  # idempotent

    with Session(get_engine()) as s:
        firma = s.exec(select(Firma).where(Firma.id == DEMO_FIRMA_ID)).first()
        assert firma is not None
        assert firma.name == "Anderssons VVS AB"
        assert firma.trade.value == "vvs"

        customers = s.exec(select(Customer).where(Customer.firma_id == DEMO_FIRMA_ID)).all()
        assert len(customers) >= 3

        calls = s.exec(select(Call).where(Call.firma_id == DEMO_FIRMA_ID)).all()
        # ≥3 — earlier admin / scenario tests in the same session may add more.
        assert len(calls) >= 3
        assert any(c.intent and c.intent.value == "akut" for c in calls)

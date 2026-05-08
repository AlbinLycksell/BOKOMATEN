from __future__ import annotations

from sqlmodel import Session

from svarsa.db.seed import DEMO_FIRMA_ID, seed_dev_data
from svarsa.db.session import get_engine, init_db
from svarsa.tools.handlers import ToolContext, dispatch


def _ctx() -> ToolContext:
    init_db()
    seed_dev_data()
    return ToolContext(session=Session(get_engine()), firma_id=DEMO_FIRMA_ID)


def test_lookup_customer_found_by_phone() -> None:
    ctx = _ctx()
    res = dispatch(ctx, "lookup_customer", {"phone_number": "+46708557777"})
    assert res["found"] is True
    assert res["name"] == "Inger Svensson"


def test_lookup_customer_not_found() -> None:
    ctx = _ctx()
    res = dispatch(ctx, "lookup_customer", {"phone_number": "+46700000000"})
    assert res["found"] is False


def test_triage_emergency_via_dispatch() -> None:
    ctx = _ctx()
    res = dispatch(
        ctx,
        "triage_emergency",
        {
            "problem_description": "vattenläcka, det rinner",
            "trade": "vvs",
            "indicators_present": ["lacka", "rinner"],
        },
    )
    assert res["is_emergency"] is True
    assert res["severity"] == "high"


def test_check_rot_eligibility_truth_table() -> None:
    ctx = _ctx()
    ok = dispatch(
        ctx,
        "check_rot_eligibility",
        {
            "is_private_person": True,
            "owns_property": True,
            "property_age_years": 25,
            "work_type": "badrumsrenovering",
        },
    )
    assert ok["eligible"] is True
    assert ok["max_deduction_sek_estimate"] > 0

    no = dispatch(
        ctx,
        "check_rot_eligibility",
        {
            "is_private_person": False,
            "owns_property": True,
            "property_age_years": 25,
            "work_type": "vvs",
        },
    )
    assert no["eligible"] is False


def test_unknown_tool_returns_error() -> None:
    ctx = _ctx()
    res = dispatch(ctx, "no_such_tool", {})
    assert "error" in res


def test_tool_declarations_build_without_error() -> None:
    from svarsa.tools.declarations import TOOL_DECLARATIONS

    assert len(TOOL_DECLARATIONS) == 1
    decls = TOOL_DECLARATIONS[0].function_declarations or []
    names = {d.name for d in decls}
    assert "lookup_customer" in names
    assert "escalate_to_owner" in names
    assert len(names) == 12

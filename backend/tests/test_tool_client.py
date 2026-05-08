from __future__ import annotations

from sqlmodel import Session

from svarsa.db.seed import DEMO_FIRMA_ID
from svarsa.db.session import get_engine
from svarsa.tools.client import LocalToolClient


async def test_local_tool_client_dispatches_in_process() -> None:
    with Session(get_engine()) as s:
        client = LocalToolClient(s)
        result = await client.dispatch(
            firma_id=DEMO_FIRMA_ID,
            call_id=None,
            name="check_rot_eligibility",
            args={
                "is_private_person": True,
                "owns_property": True,
                "property_age_years": 30,
                "work_type": "vvs",
            },
        )
        assert result["eligible"] is True
        assert result["max_deduction_sek_estimate"] > 0


async def test_local_tool_client_unknown_tool_returns_error() -> None:
    with Session(get_engine()) as s:
        client = LocalToolClient(s)
        result = await client.dispatch(
            firma_id=DEMO_FIRMA_ID,
            call_id=None,
            name="no_such_tool",
            args={},
        )
        assert "error" in result


def test_dispatch_endpoint_is_mounted() -> None:
    from fastapi.testclient import TestClient

    from svarsa.app import create_app

    with TestClient(create_app()) as client:
        r = client.post(
            "/api/tools/dispatch",
            headers={"X-Firma-Id": DEMO_FIRMA_ID},
            json={
                "name": "check_rot_eligibility",
                "args": {
                    "is_private_person": True,
                    "owns_property": True,
                    "property_age_years": 30,
                    "work_type": "vvs",
                },
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["result"]["eligible"] is True

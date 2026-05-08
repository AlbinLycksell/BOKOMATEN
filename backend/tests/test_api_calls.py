from __future__ import annotations

from fastapi.testclient import TestClient

from svarsa.app import create_app
from svarsa.db.seed import DEMO_FIRMA_ID


def _client() -> TestClient:
    return TestClient(create_app())


def test_list_calls_returns_seeded_data() -> None:
    with _client() as client:
        r = client.get("/api/calls", headers={"X-Firma-Id": DEMO_FIRMA_ID})
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)
        assert len(body) >= 3
        statuses = {c["status"] for c in body}
        assert "handled" in statuses or "needs_followup" in statuses


def test_list_calls_filtered_by_intent() -> None:
    with _client() as client:
        r = client.get(
            "/api/calls?intent=akut",
            headers={"X-Firma-Id": DEMO_FIRMA_ID},
        )
        assert r.status_code == 200
        body = r.json()
        assert all(c["intent"] == "akut" for c in body)


def test_get_call_detail_includes_transcript_and_tools() -> None:
    with _client() as client:
        list_r = client.get(
            "/api/calls?intent=akut",
            headers={"X-Firma-Id": DEMO_FIRMA_ID},
        )
        call_id = list_r.json()[0]["id"]
        r = client.get(
            f"/api/calls/{call_id}",
            headers={"X-Firma-Id": DEMO_FIRMA_ID},
        )
        assert r.status_code == 200
        body = r.json()
        assert "transcript" in body
        assert "tool_invocations" in body
        assert len(body["transcript"]) > 0
        assert any(seg["role"] == "ai" for seg in body["transcript"])


def test_firma_me_returns_settings() -> None:
    with _client() as client:
        r = client.get("/api/firma/me", headers={"X-Firma-Id": DEMO_FIRMA_ID})
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "Anderssons VVS AB"
        assert "settings" in body


def test_firma_settings_update_round_trip() -> None:
    with _client() as client:
        r = client.put(
            "/api/firma/me/settings",
            json={"voice": "Charon"},
            headers={"X-Firma-Id": DEMO_FIRMA_ID},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["settings"]["voice"] == "Charon"


def test_customers_list_includes_seeded() -> None:
    with _client() as client:
        r = client.get("/api/customers", headers={"X-Firma-Id": DEMO_FIRMA_ID})
        assert r.status_code == 200
        body = r.json()
        names = [c["name"] for c in body]
        assert any("Inger" in n for n in names)

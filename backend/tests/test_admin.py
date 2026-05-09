from __future__ import annotations

from fastapi.testclient import TestClient

from switchboard.app import create_app
from switchboard.db.seed import DEMO_FIRMA_ID


def _client() -> TestClient:
    return TestClient(create_app())


def test_system_prompt_returns_per_firma_text() -> None:
    with _client() as client:
        r = client.get("/api/admin/system-prompt", headers={"X-Firma-Id": DEMO_FIRMA_ID})
        assert r.status_code == 200
        body = r.json()
        assert "Anderssons VVS AB" in body["text"]
        assert body["length_chars"] > 100


def test_list_scenarios_returns_presets() -> None:
    with _client() as client:
        r = client.get("/api/admin/scenarios", headers={"X-Firma-Id": DEMO_FIRMA_ID})
        assert r.status_code == 200
        body = r.json()
        ids = {s["id"] for s in body}
        assert "vattenlacka_akut" in ids
        assert "gas_lukt_kritisk" in ids
        assert "ovk_b2b_bokning" in ids


def test_run_emergency_scenario_persists_call_with_high_severity() -> None:
    with _client() as client:
        r = client.post(
            "/api/admin/scenarios/vattenlacka_akut/run",
            headers={"X-Firma-Id": DEMO_FIRMA_ID},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["intent"] == "akut"
        assert body["severity"] == "high"
        assert "escalate_to_owner" in body["tool_invocations"]
        assert body["call_id"]


def test_run_gas_scenario_is_critical() -> None:
    with _client() as client:
        r = client.post(
            "/api/admin/scenarios/gas_lukt_kritisk/run",
            headers={"X-Firma-Id": DEMO_FIRMA_ID},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["severity"] == "critical"


def test_run_unknown_scenario_returns_404() -> None:
    with _client() as client:
        r = client.post(
            "/api/admin/scenarios/no-such/run",
            headers={"X-Firma-Id": DEMO_FIRMA_ID},
        )
        assert r.status_code == 404


def test_tool_playground_lists_tools() -> None:
    with _client() as client:
        r = client.get("/api/admin/tools", headers={"X-Firma-Id": DEMO_FIRMA_ID})
        assert r.status_code == 200
        names = {t["name"] for t in r.json()}
        assert "lookup_customer" in names
        assert "disable_recording_for_call" in names


def test_tool_playground_runs_pure_function() -> None:
    with _client() as client:
        r = client.post(
            "/api/admin/tools/run",
            headers={"X-Firma-Id": DEMO_FIRMA_ID},
            json={
                "name": "check_rot_eligibility",
                "args": {
                    "is_private_person": True,
                    "owns_property": True,
                    "property_age_years": 25,
                    "work_type": "vvs",
                },
            },
        )
        assert r.status_code == 200
        assert r.json()["result"]["eligible"] is True


def test_test_sms_simulates_when_unconfigured() -> None:
    with _client() as client:
        r = client.post(
            "/api/admin/test/sms",
            headers={"X-Firma-Id": DEMO_FIRMA_ID},
            json={
                "to_phone": "+46708555000",
                "template": "callback_promise",
                "context_data": {"name": "Magnus"},
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["sent"] is True
        assert body["via"] in ("simulated", "live")


def test_test_escalation_creates_audit_row() -> None:
    with _client() as client:
        r = client.post(
            "/api/admin/test/escalation",
            headers={"X-Firma-Id": DEMO_FIRMA_ID},
            json={"severity": "high", "reason_sv": "Manuell test"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["escalation_id"]


def test_audit_log_returns_recent_entries() -> None:
    with _client() as client:
        # Touch one auditable action first.
        client.post(
            "/api/admin/scenarios/telemarketing_avslag/run",
            headers={"X-Firma-Id": DEMO_FIRMA_ID},
        )
        r = client.get(
            "/api/admin/audit-log?action_prefix=scenario.&limit=5",
            headers={"X-Firma-Id": DEMO_FIRMA_ID},
        )
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) >= 1
        assert all(row["action"].startswith("scenario.") for row in rows)


def test_run_eval_on_bundled_dataset() -> None:
    with _client() as client:
        r = client.post(
            "/api/admin/eval/run",
            headers={"X-Firma-Id": DEMO_FIRMA_ID},
            json={},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["total"] >= 5
        assert "intent_accuracy" in body

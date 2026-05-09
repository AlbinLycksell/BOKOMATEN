from __future__ import annotations

from fastapi.testclient import TestClient

from switchboard.app import create_app


def test_health_returns_ok() -> None:
    app = create_app()
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["env"] == "dev"
        assert "version" in body

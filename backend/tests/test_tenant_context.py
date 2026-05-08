from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from svarsa.app import create_app
from svarsa.core.tenant import firma_context, get_firma_id, require_firma_id
from svarsa.db.seed import DEMO_FIRMA_ID
from svarsa.db.session import get_engine
from svarsa.models import AuditLog
from svarsa.services import audit_service


def test_get_firma_id_unset_by_default() -> None:
    assert get_firma_id() is None


def test_firma_context_binds_and_releases() -> None:
    assert get_firma_id() is None
    with firma_context("01J0000FIRMTEST"):
        assert get_firma_id() == "01J0000FIRMTEST"
        assert require_firma_id() == "01J0000FIRMTEST"
    assert get_firma_id() is None


def test_require_firma_id_raises_when_unset() -> None:
    with pytest.raises(RuntimeError):
        require_firma_id()


def test_audit_service_refuses_unscoped_write() -> None:
    with Session(get_engine()) as s, pytest.raises(RuntimeError):
        audit_service.record(s, actor="ai", action="test.action")


def test_audit_service_writes_when_scoped() -> None:
    with Session(get_engine()) as s, firma_context(DEMO_FIRMA_ID):
        before = len(s.exec(select(AuditLog)).all())
        audit_service.record(
            s,
            actor="ai",
            action="tool.invoked",
            target_type="call",
            target_id="01J-test",
            payload={"name": "lookup_customer"},
        )
        after = s.exec(select(AuditLog).where(AuditLog.firma_id == DEMO_FIRMA_ID)).all()
        assert len(after) == before + 1
        assert after[-1].action == "tool.invoked"


def test_middleware_binds_firma_from_header() -> None:
    with TestClient(create_app()) as client:
        r = client.get("/health", headers={"X-Firma-Id": "01J-some"})
        assert r.status_code == 200

from __future__ import annotations

from sqlmodel import Session, select

from switchboard.db.session import get_engine
from switchboard.models import Firma, User
from switchboard.scripts.erase_tenant import erase_tenant
from switchboard.services.onboarding_service import bootstrap_user


def _make_tenant() -> str:
    with Session(get_engine()) as s:
        result = bootstrap_user(
            s, google_sub="erase-test", email="erase@example.com", name="Erase Me"
        )
        return result.firma_id


def test_dry_run_does_not_delete() -> None:
    fid = _make_tenant()
    counts = erase_tenant(fid, operator="test", dry_run=True)
    assert sum(counts.values()) >= 1  # at least the user row
    with Session(get_engine()) as s:
        assert s.get(Firma, fid) is not None


def test_full_erase_removes_firma_and_users() -> None:
    fid = _make_tenant()
    erase_tenant(fid, operator="test", dry_run=False)
    with Session(get_engine()) as s:
        assert s.get(Firma, fid) is None
        users = s.exec(select(User).where(User.firma_id == fid)).all()
        assert users == []

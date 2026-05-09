from __future__ import annotations

import os

import pytest
from sqlmodel import Session, select

from svarsa.db.session import get_engine
from svarsa.models import Firma, User
from svarsa.services.onboarding_service import (
    SignupNotAllowed,
    bootstrap_user,
)


def test_bootstrap_creates_firma_on_first_signin() -> None:
    with Session(get_engine()) as s:
        result = bootstrap_user(
            s,
            google_sub="google-12345",
            email="alice@example.com",
            name="Alice Andersson",
        )
        assert result.created_firma is True
        firma = s.get(Firma, result.firma_id)
        assert firma is not None
        assert firma.name.endswith("AB")
        users = s.exec(select(User).where(User.firma_id == result.firma_id)).all()
        assert len(users) == 1
        assert users[0].email == "alice@example.com"
        assert users[0].google_sub == "google-12345"


def test_bootstrap_returns_existing_user() -> None:
    with Session(get_engine()) as s:
        first = bootstrap_user(
            s, google_sub="google-67890", email="bob@example.com", name="Bob"
        )
        second = bootstrap_user(
            s, google_sub="google-67890", email="bob@example.com", name="Bob"
        )
        assert second.created_firma is False
        assert second.firma_id == first.firma_id


def test_bootstrap_blocks_disallowed_domain(monkeypatch: pytest.MonkeyPatch) -> None:
    os.environ["SVARSA_ALLOWED_SIGNUP_DOMAINS"] = '["siftlab.com"]'
    from svarsa.core.config import get_settings

    get_settings.cache_clear()
    try:
        with Session(get_engine()) as s, pytest.raises(SignupNotAllowed):
            bootstrap_user(
                s, google_sub="g-x", email="random@nowhere.example", name="X"
            )
    finally:
        os.environ.pop("SVARSA_ALLOWED_SIGNUP_DOMAINS", None)
        get_settings.cache_clear()

"""Tenant onboarding — sign-up → User row → Firma row → eager bucket creation.

Three modes:

- ``bootstrap_user``: NextAuth POSTs here on first sign-in. We look up the
  user by ``google_sub`` (or ``email``). If found, return their existing
  ``firma_id``. If not, fall through to ``create_firma_for_user``.
- ``create_firma_for_user``: provisions a placeholder Firma + the calling
  user as its owner. Eager bucket creation so the first call doesn't
  fail mid-stream.
- ``provision_phone_number``: stub — concierge onboarding (F6) calls this
  to wire a real 46elks number to the new firma.

Refuses to operate when ``Settings.allowed_signup_domains`` is set and
the email isn't on the list.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlmodel import Session, select

from svarsa.core.config import Settings, get_settings
from svarsa.core.ids import new_id
from svarsa.core.logging import get_logger
from svarsa.core.tenant import firma_context
from svarsa.core.time import utcnow
from svarsa.models import (
    Firma,
    FirmaSettings,
    Plan,
    Trade,
    User,
)

if TYPE_CHECKING:
    from svarsa.models.firma import Firma as FirmaModel

log = get_logger("svarsa.onboarding")


class SignupNotAllowed(Exception):
    pass


@dataclass(frozen=True)
class BootstrapResult:
    user_id: str
    firma_id: str
    role: str
    created_firma: bool


def bootstrap_user(
    session: Session,
    *,
    google_sub: str,
    email: str,
    name: str | None = None,
    settings: Settings | None = None,
) -> BootstrapResult:
    s = settings or get_settings()
    _check_domain_allowlist(email, s)

    user = session.exec(select(User).where(User.google_sub == google_sub)).first()
    if user is None:
        user = session.exec(select(User).where(User.email == email)).first()

    if user is not None:
        user.google_sub = google_sub
        user.last_login_at = utcnow()
        if name and not user.name:
            user.name = name
        session.add(user)
        session.commit()
        session.refresh(user)
        log.info("onboarding.user.returning", user_id=user.id, firma_id=user.firma_id)
        return BootstrapResult(
            user_id=user.id,
            firma_id=user.firma_id,
            role=user.role,
            created_firma=False,
        )

    firma, owner = create_firma_for_user(
        session,
        email=email,
        google_sub=google_sub,
        name=name or email.split("@")[0],
        settings=s,
    )
    return BootstrapResult(
        user_id=owner.id,
        firma_id=firma.id,
        role=owner.role,
        created_firma=True,
    )


def create_firma_for_user(
    session: Session,
    *,
    email: str,
    google_sub: str,
    name: str,
    settings: Settings | None = None,
) -> tuple["FirmaModel", User]:
    s = settings or get_settings()
    _check_domain_allowlist(email, s)

    placeholder = name.split(" ")[0].title() if name else email.split("@")[0]
    firma = Firma(
        id=new_id(),
        name=f"{placeholder} AB",
        trade=Trade.VVS,
        plan=Plan.STARTER,
        settings=FirmaSettings().model_dump(),
    )
    session.add(firma)
    session.flush()

    owner = User(
        firma_id=firma.id,
        role="owner",
        name=name,
        email=email,
        google_sub=google_sub,
        on_call=True,
        last_login_at=utcnow(),
    )
    session.add(owner)
    session.commit()
    session.refresh(firma)
    session.refresh(owner)

    # Eager per-tenant bucket creation in production storage mode (no-op for local).
    try:
        from svarsa.integrations.storage import make_storage

        with firma_context(firma.id):
            store = make_storage(s)
            store.ensure_bucket(firma.id)
    except Exception:  # noqa: BLE001
        log.exception("onboarding.bucket.failed", firma_id=firma.id)

    log.info(
        "onboarding.firma.created",
        firma_id=firma.id,
        owner_user=owner.id,
        email=email,
    )
    return firma, owner


def _check_domain_allowlist(email: str, settings: Settings) -> None:
    allowed = settings.allowed_signup_domains
    if not allowed:
        return
    domain = email.rsplit("@", 1)[-1].lower()
    if domain not in {d.lower() for d in allowed}:
        log.warning("onboarding.domain.blocked", email=email)
        msg = f"signup_blocked:{domain}"
        raise SignupNotAllowed(msg)

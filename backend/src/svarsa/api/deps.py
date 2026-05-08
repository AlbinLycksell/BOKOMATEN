"""FastAPI dependency injectables.

`get_current_firma` reads `X-Firma-Id` for MVP. Replace with OAuth /
JWT when Phase 1 closed-beta lands.
"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, Header, HTTPException, status
from sqlmodel import Session

from svarsa.db.seed import DEMO_FIRMA_ID
from svarsa.db.session import get_engine
from svarsa.models import Firma


def get_db() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session


def get_current_firma(
    db: Session = Depends(get_db),
    x_firma_id: str | None = Header(default=None, alias="X-Firma-Id"),
) -> Firma:
    firma_id = x_firma_id or DEMO_FIRMA_ID
    firma = db.get(Firma, firma_id)
    if firma is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="firma_not_found")
    return firma

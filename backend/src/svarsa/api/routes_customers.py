from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from svarsa.api.deps import get_current_firma, get_db
from svarsa.models import Address, Customer, CustomerRead, Firma

router = APIRouter(prefix="/api/customers", tags=["customers"])


def _to_read(c: Customer) -> CustomerRead:
    addr = Address.model_validate(c.address) if c.address else None
    return CustomerRead(
        id=c.id,
        type=c.type,
        name=c.name,
        phone=c.phone,
        email=c.email,
        org_number=c.org_number,
        address=addr,
        notes_summary=c.notes_summary,
        created_at=c.created_at,
    )


@router.get("", response_model=list[CustomerRead])
def list_customers(
    firma: Annotated[Firma, Depends(get_current_firma)],
    db: Annotated[Session, Depends(get_db)],
    q: str | None = Query(default=None, description="Free-text search on name/phone"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[CustomerRead]:
    stmt = select(Customer).where(Customer.firma_id == firma.id)
    rows = db.exec(stmt.order_by(Customer.updated_at.desc()).offset(offset).limit(limit)).all()  # type: ignore[attr-defined]
    if q:
        needle = q.casefold()
        rows = [c for c in rows if needle in c.name.casefold() or needle in c.phone]
    return [_to_read(c) for c in rows]


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(
    customer_id: str,
    firma: Annotated[Firma, Depends(get_current_firma)],
    db: Annotated[Session, Depends(get_db)],
) -> CustomerRead:
    c = db.get(Customer, customer_id)
    if c is None or c.firma_id != firma.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="customer_not_found")
    return _to_read(c)

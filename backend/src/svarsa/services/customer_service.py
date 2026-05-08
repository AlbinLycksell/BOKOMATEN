from __future__ import annotations

from sqlmodel import Session, select

from svarsa.core.logging import get_logger
from svarsa.models import Customer

log = get_logger("svarsa.customer")


def lookup_by_phone(session: Session, firma_id: str, phone: str) -> Customer | None:
    return session.exec(
        select(Customer).where(Customer.firma_id == firma_id, Customer.phone == phone)
    ).first()


def lookup_by_org(session: Session, firma_id: str, org_number: str) -> Customer | None:
    return session.exec(
        select(Customer).where(
            Customer.firma_id == firma_id, Customer.org_number == org_number
        )
    ).first()


def lookup_by_name(session: Session, firma_id: str, name_query: str) -> Customer | None:
    rows = session.exec(
        select(Customer).where(Customer.firma_id == firma_id)
    ).all()
    needle = name_query.casefold()
    for c in rows:
        if needle in c.name.casefold():
            return c
    return None


def create_lead(
    session: Session,
    firma_id: str,
    *,
    name: str,
    phone: str,
    type_: str,
    email: str | None,
    address: str | None,
    org_number: str | None,
    problem_summary_sv: str,
) -> Customer:
    customer = Customer(
        firma_id=firma_id,
        name=name,
        phone=phone,
        type=type_,  # type: ignore[arg-type]
        email=email,
        org_number=org_number,
        address={"street": address} if address else None,
        notes_summary=problem_summary_sv,
        source="ai_call",
    )
    session.add(customer)
    session.commit()
    session.refresh(customer)
    log.info("customer.created", id=customer.id, firma=firma_id)
    return customer

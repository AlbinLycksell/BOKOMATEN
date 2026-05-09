from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import JSON, Column
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel

from switchboard.core.ids import new_id
from switchboard.core.time import utcnow
from switchboard.models.enums import CustomerType


class Address(BaseModel):
    street: str
    apartment: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: str = "SE"


class Customer(SQLModel, table=True):
    __tablename__ = "customer"

    id: str = SQLField(default_factory=new_id, primary_key=True)
    firma_id: str = SQLField(foreign_key="firma.id", index=True)
    type: CustomerType = CustomerType.PRIVATE
    name: str = SQLField(index=True)
    phone: str = SQLField(index=True)
    email: str | None = None
    org_number: str | None = SQLField(default=None, index=True)
    address: dict[str, Any] | None = SQLField(default=None, sa_column=Column(JSON))
    source: str = "ai_call"
    notes_summary: str | None = None
    created_at: datetime = SQLField(default_factory=utcnow)
    updated_at: datetime = SQLField(default_factory=utcnow)


class Note(SQLModel, table=True):
    __tablename__ = "customer_note"

    id: str = SQLField(default_factory=new_id, primary_key=True)
    customer_id: str = SQLField(foreign_key="customer.id", index=True)
    body: str
    created_by: str
    created_at: datetime = SQLField(default_factory=utcnow)


class Photo(SQLModel, table=True):
    __tablename__ = "customer_photo"

    id: str = SQLField(default_factory=new_id, primary_key=True)
    customer_id: str = SQLField(foreign_key="customer.id", index=True)
    url: str
    expires_at: datetime | None = None
    uploaded_at: datetime = SQLField(default_factory=utcnow)


class CustomerRead(BaseModel):
    id: str
    type: CustomerType
    name: str
    phone: str
    email: str | None
    org_number: str | None
    address: Address | None
    notes_summary: str | None
    created_at: datetime

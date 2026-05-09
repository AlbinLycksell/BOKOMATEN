from __future__ import annotations

from typing import NewType

from ulid import ULID

FirmaId = NewType("FirmaId", str)
UserId = NewType("UserId", str)
PhoneNumberId = NewType("PhoneNumberId", str)
CustomerId = NewType("CustomerId", str)
CallId = NewType("CallId", str)
JobId = NewType("JobId", str)
EscalationId = NewType("EscalationId", str)
ToolInvocationId = NewType("ToolInvocationId", str)
NoteId = NewType("NoteId", str)
PhotoId = NewType("PhotoId", str)
IntegrationId = NewType("IntegrationId", str)


def new_id() -> str:
    return str(ULID())

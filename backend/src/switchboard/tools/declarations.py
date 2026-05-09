"""Adapt Pydantic schemas → Gemini Live tool declarations.

Gemini's function-calling schema dialect is OpenAPI-ish but rejects
`$defs`, `$ref`, `additionalProperties`, and `null` types in unions.
We deref + flatten before submission.
"""

from __future__ import annotations

from typing import Any

from google.genai import types as gtypes
from pydantic import BaseModel

from switchboard.tools.schemas import (
    BookAppointmentArgs,
    CheckAvailabilityArgs,
    CheckRotEligibilityArgs,
    CreateLeadArgs,
    EscalateToOwnerArgs,
    LookupCustomerArgs,
    LookupJobStatusArgs,
    RequestPhotoUploadArgs,
    SendSmsFollowupArgs,
    TakeMessageArgs,
    TransferToHumanArgs,
    TriageEmergencyArgs,
)

TOOL_DESCRIPTIONS: dict[str, tuple[type[BaseModel], str]] = {
    "lookup_customer": (
        LookupCustomerArgs,
        "Slå upp en kund i firmans system baserat på telefonnummer eller org-nummer. "
        "Anropa direkt vid samtalets start för CLI-baserad igenkänning.",
    ),
    "triage_emergency": (
        TriageEmergencyArgs,
        "Bedöm om problemet är akut enligt firmans regler. Anropa när kunden beskriver ett problem.",
    ),
    "check_availability": (
        CheckAvailabilityArgs,
        "Hämta lediga tider i kalendern för planerat arbete.",
    ),
    "book_appointment": (
        BookAppointmentArgs,
        "Boka in jobbet hos kunden. Anropa endast efter att kunden uttryckligen bekräftat tid och adress.",
    ),
    "create_lead": (
        CreateLeadArgs,
        "Skapa ny kund/lead i firmans CRM när lookup_customer inte hittade träff.",
    ),
    "escalate_to_owner": (
        EscalateToOwnerArgs,
        "Eskalera ärendet till ägare/jourtekniker enligt firmans eskaleringskedja.",
    ),
    "send_sms_followup": (
        SendSmsFollowupArgs,
        "Skicka SMS-bekräftelse, foto-uppladdningslänk eller bokningsbekräftelse till kunden.",
    ),
    "request_photo_upload": (
        RequestPhotoUploadArgs,
        "Generera engångs-länk för foto-uppladdning och skicka via SMS.",
    ),
    "lookup_job_status": (
        LookupJobStatusArgs,
        "Slå upp status på pågående eller nyligen avslutat jobb för befintlig kund.",
    ),
    "check_rot_eligibility": (
        CheckRotEligibilityArgs,
        "Bedöm om kunden sannolikt kvalificerar för ROT-avdrag. Pure-function.",
    ),
    "transfer_to_human": (
        TransferToHumanArgs,
        "Koppla samtalet till en människa via SIP-bridge.",
    ),
    "take_message": (
        TakeMessageArgs,
        "Avsluta med strukturerat meddelande. Sista utvägen.",
    ),
}


def _strip_unsupported(schema: dict[str, Any]) -> dict[str, Any]:
    """Strip JSONSchema features Gemini's function calling rejects."""
    DROP = {
        "$defs",
        "$ref",
        "additionalProperties",
        "title",
        "examples",
        "anyOf",
        "oneOf",
        "allOf",
    }
    if isinstance(schema, dict):
        cleaned: dict[str, Any] = {}
        for k, v in schema.items():
            if k in DROP:
                continue
            cleaned[k] = _strip_unsupported(v)
        return cleaned
    if isinstance(schema, list):
        return [_strip_unsupported(item) for item in schema]  # type: ignore[return-value]
    return schema


def _to_gemini_schema(model: type[BaseModel]) -> dict[str, Any]:
    raw = model.model_json_schema()
    return _strip_unsupported(raw)


def build_tool_declarations() -> list[gtypes.Tool]:
    declarations: list[gtypes.FunctionDeclaration] = []
    for name, (args_model, description) in TOOL_DESCRIPTIONS.items():
        schema = _to_gemini_schema(args_model)
        declarations.append(
            gtypes.FunctionDeclaration(
                name=name,
                description=description,
                parameters_json_schema=schema,
            )
        )
    return [gtypes.Tool(function_declarations=declarations)]


TOOL_DECLARATIONS: list[gtypes.Tool] = build_tool_declarations()

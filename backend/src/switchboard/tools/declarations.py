"""Adapt Pydantic schemas → Gemini Live tool declarations.

Gemini's function-calling schema dialect is OpenAPI-ish but rejects
`$defs`, `$ref`, `additionalProperties`, and `null` types in unions.
We deref + flatten before submission.
"""

from __future__ import annotations

from typing import Any

from google.genai import types as gtypes
from pydantic import BaseModel

from switchboard.models import ToolName
from switchboard.tools.schemas import (
    BookAppointmentArgs,
    CheckAvailabilityArgs,
    CheckRotEligibilityArgs,
    CreateLeadArgs,
    DisableRecordingArgs,
    EscalateToOwnerArgs,
    LookupCustomerArgs,
    LookupJobStatusArgs,
    RequestPhotoUploadArgs,
    SendSmsFollowupArgs,
    TakeMessageArgs,
    TransferToHumanArgs,
    TriageEmergencyArgs,
)

TOOL_DESCRIPTIONS: dict[ToolName, tuple[type[BaseModel], str]] = {
    ToolName.LOOKUP_CUSTOMER: (
        LookupCustomerArgs,
        "Slå upp en kund i firmans system baserat på telefonnummer eller org-nummer. "
        "Anropa direkt vid samtalets start för CLI-baserad igenkänning.",
    ),
    ToolName.TRIAGE_EMERGENCY: (
        TriageEmergencyArgs,
        "Bedöm om problemet är akut enligt firmans regler. Anropa när kunden beskriver ett problem.",
    ),
    ToolName.CHECK_AVAILABILITY: (
        CheckAvailabilityArgs,
        "Hämta lediga tider i kalendern för planerat arbete.",
    ),
    ToolName.BOOK_APPOINTMENT: (
        BookAppointmentArgs,
        "Boka in jobbet hos kunden. Anropa endast efter att kunden uttryckligen bekräftat tid och adress.",
    ),
    ToolName.CREATE_LEAD: (
        CreateLeadArgs,
        "Skapa ny kund/lead i firmans CRM när lookup_customer inte hittade träff.",
    ),
    ToolName.ESCALATE_TO_OWNER: (
        EscalateToOwnerArgs,
        "Eskalera ärendet till ägare/jourtekniker enligt firmans eskaleringskedja.",
    ),
    ToolName.SEND_SMS_FOLLOWUP: (
        SendSmsFollowupArgs,
        "Skicka SMS-bekräftelse, foto-uppladdningslänk eller bokningsbekräftelse till kunden.",
    ),
    ToolName.REQUEST_PHOTO_UPLOAD: (
        RequestPhotoUploadArgs,
        "Generera engångs-länk för foto-uppladdning och skicka via SMS.",
    ),
    ToolName.LOOKUP_JOB_STATUS: (
        LookupJobStatusArgs,
        "Slå upp status på pågående eller nyligen avslutat jobb för befintlig kund.",
    ),
    ToolName.CHECK_ROT_ELIGIBILITY: (
        CheckRotEligibilityArgs,
        "Bedöm om kunden sannolikt kvalificerar för ROT-avdrag. Pure-function.",
    ),
    ToolName.TRANSFER_TO_HUMAN: (
        TransferToHumanArgs,
        "Koppla samtalet till en människa via SIP-bridge.",
    ),
    ToolName.TAKE_MESSAGE: (
        TakeMessageArgs,
        "Avsluta med strukturerat meddelande. Sista utvägen.",
    ),
    ToolName.DISABLE_RECORDING_FOR_CALL: (
        DisableRecordingArgs,
        "Stäng av inspelning av detta samtal direkt. Anropa endast om "
        "kunden uttryckligen invänder mot att samtalet spelas in.",
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

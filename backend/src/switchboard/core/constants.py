"""Shared string constants that aren't enums (HTTP headers, demo IDs, model defaults)."""

from __future__ import annotations

from typing import Final


class HttpHeader:
    FIRMA_ID: Final[str] = "X-Firma-Id"
    INTERNAL_TOKEN: Final[str] = "X-Internal-Token"
    AUTHORIZATION: Final[str] = "Authorization"
    CONTENT_TYPE: Final[str] = "Content-Type"
    STRIPE_SIGNATURE: Final[str] = "Stripe-Signature"


class ContentType:
    JSON: Final[str] = "application/json"
    FORM_URLENCODED: Final[str] = "application/x-www-form-urlencoded"


BEARER_PREFIX: Final[str] = "Bearer "
DEMO_FIRMA_ID: Final[str] = "01J0000FIRM0ANDERSSONSVVS00"

DEFAULT_GEMINI_VOICE: Final[str] = "Aoede"
DEFAULT_GEMINI_LANGUAGE: Final[str] = "sv-SE"
DEFAULT_GEMINI_MODEL: Final[str] = "models/gemini-3.1-flash-live-preview"
GEMINI_MODEL_PREFIX: Final[str] = "models/"

GEMINI_API_VERSION: Final[str] = "v1beta"

DEFAULT_SMS_SENDER_ID: Final[str] = "Switchboard"

SMS_DELIVERY_OK_STATUSES: Final[tuple[str | None, ...]] = (None, "delivered", "queued", "created")

"""SMS / email side-effects.

Production: 46elks SMS API. Dev: logs the would-be message and returns a
deterministic id without hitting the network. Switching is automatic
based on whether `SWITCHBOARD_ELKS_API_USERNAME` is set.
"""

from __future__ import annotations

from switchboard.core.config import get_settings
from switchboard.core.constants import SMS_DELIVERY_OK_STATUSES
from switchboard.core.ids import new_id
from switchboard.core.logging import get_logger
from switchboard.integrations.elks_sms import ElksSMSClient
from switchboard.models import SmsTemplate
from switchboard.tools.schemas import RequestPhotoUploadResult, SendSmsFollowupResult

log = get_logger("switchboard.notify")


_TEMPLATES: dict[SmsTemplate, str] = {
    SmsTemplate.BOOKING_CONFIRMATION: (
        "Hej {name}! Du är bokad {time} på {address}. "
        "Vi hör av oss om något ändras. /Switchboard"
    ),
    SmsTemplate.EMERGENCY_ACK: (
        "Tack {name}, vi har fått ditt ärende och {owner_name} ringer dig "
        "inom {window}. /Switchboard"
    ),
    SmsTemplate.PHOTO_UPLOAD_LINK: (
        "Hej! Skicka gärna bild på problemet via denna länk "
        "(giltig 7 dagar): {url} /Switchboard"
    ),
    SmsTemplate.CALLBACK_PROMISE: (
        "Tack för samtalet, {name}. Vi ringer upp inom {window}. /Switchboard"
    ),
    SmsTemplate.SECURE_FORM_LINK: (
        "För känslig info, fyll i säkert formulär här "
        "(giltigt 1 timme): {url} /Switchboard"
    ),
}


def render_template(template: SmsTemplate, ctx: dict[str, str | int | bool]) -> str:
    body = _TEMPLATES.get(template, "")
    if not body:
        return ""
    safe_ctx = {k: str(v) for k, v in ctx.items()}
    safe_ctx.setdefault("name", "")
    safe_ctx.setdefault("time", "")
    safe_ctx.setdefault("address", "")
    safe_ctx.setdefault("url", "")
    safe_ctx.setdefault("window", "15 min")
    safe_ctx.setdefault("owner_name", "Vi")
    try:
        return body.format(**safe_ctx)
    except KeyError as missing:
        log.warning("sms.template.missing_var", template=template, missing=str(missing))
        return body


def send_sms(
    *,
    to_phone: str,
    template: SmsTemplate,
    context_data: dict[str, str | int | bool],
    sender_id: str | None = None,
    firma_sender_id: str | None = None,
    firma_sender_id_verified: bool = False,
) -> SendSmsFollowupResult:
    """Send an SMS with the firma's verified sender id when available.

    Resolution order:
    - explicit ``sender_id`` arg (rare; debug only)
    - per-firma alias if verified (best UX — recipient sees firma name)
    - platform default (`Settings.elks_default_sender_id` = `"Switchboard"`)
    """
    settings = get_settings()
    body = render_template(template, context_data)
    resolved_sender = sender_id or (
        firma_sender_id if firma_sender_id_verified and firma_sender_id else None
    )
    if not settings.elks_api_username:
        sms_id = new_id()
        log.info(
            "sms.simulated",
            id=sms_id,
            to=to_phone,
            template=template,
            body=body,
        )
        return SendSmsFollowupResult(sent=True, sms_id=sms_id)
    client = ElksSMSClient(settings)
    try:
        result = client.send(to=to_phone, message=body, sender_id=resolved_sender)
        return SendSmsFollowupResult(
            sent=bool(result.get("status") in SMS_DELIVERY_OK_STATUSES),
            sms_id=str(result.get("id", new_id())),
        )
    finally:
        client.close()


def request_photo_upload(
    *,
    to_phone: str,
    lead_or_customer_id: str,
    expires_hours: int,
) -> RequestPhotoUploadResult:
    upload_url = f"https://app.switchboard.se/u/{new_id()}"
    log.info(
        "photo_upload.requested",
        url=upload_url,
        to=to_phone,
        expires_hours=expires_hours,
    )
    return RequestPhotoUploadResult(upload_url=upload_url, sms_sent=True)

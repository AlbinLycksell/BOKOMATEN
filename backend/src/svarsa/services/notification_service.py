"""SMS / email side-effects. MVP: log + return a deterministic id.

Real 46elks integration plugs in here in PRD Phase 1 implementation.
"""

from __future__ import annotations

from svarsa.core.ids import new_id
from svarsa.core.logging import get_logger
from svarsa.tools.schemas import (
    RequestPhotoUploadResult,
    SendSmsFollowupResult,
    SmsTemplate,
)

log = get_logger("svarsa.notify")


def send_sms(
    *,
    to_phone: str,
    template: SmsTemplate,
    context_data: dict[str, str | int | bool],
) -> SendSmsFollowupResult:
    sms_id = new_id()
    log.info("sms.sent", id=sms_id, to=to_phone, template=template, ctx=context_data)
    return SendSmsFollowupResult(sent=True, sms_id=sms_id)


def request_photo_upload(
    *,
    to_phone: str,
    lead_or_customer_id: str,
    expires_hours: int,
) -> RequestPhotoUploadResult:
    upload_url = f"https://app.svarsa.se/u/{new_id()}"
    log.info(
        "photo_upload.requested",
        url=upload_url,
        to=to_phone,
        expires_hours=expires_hours,
    )
    return RequestPhotoUploadResult(upload_url=upload_url, sms_sent=True)

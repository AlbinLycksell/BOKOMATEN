"""Stripe Billing endpoints — checkout, portal, webhook."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlmodel import Session

from switchboard.api.deps import get_current_firma, get_db
from switchboard.core.logging import get_logger
from switchboard.integrations import stripe_billing
from switchboard.models import Firma, Plan

router = APIRouter(prefix="/api/billing", tags=["billing"])
log = get_logger("switchboard.billing")


class CheckoutRequest(BaseModel):
    plan: Plan
    success_url: str
    cancel_url: str
    email: str


class CheckoutResponse(BaseModel):
    id: str
    url: str


class PortalResponse(BaseModel):
    url: str


@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout(
    payload: CheckoutRequest,
    firma: Annotated[Firma, Depends(get_current_firma)],
    db: Annotated[Session, Depends(get_db)],
) -> CheckoutResponse:
    try:
        result = stripe_billing.create_checkout_session(
            db,
            firma,
            plan=payload.plan,
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
            email=payload.email,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return CheckoutResponse(**result)


@router.post("/portal", response_model=PortalResponse)
def create_portal(
    firma: Annotated[Firma, Depends(get_current_firma)],
) -> PortalResponse:
    try:
        result = stripe_billing.create_portal_session(firma)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return PortalResponse(**result)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    stripe_signature: Annotated[str | None, Header(alias="Stripe-Signature")] = None,
) -> dict[str, str]:
    payload = await request.body()
    if not stripe_signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="missing_signature")
    try:
        event = stripe_billing.construct_event(payload, stripe_signature)
    except Exception as exc:  # noqa: BLE001
        log.warning("stripe.webhook.invalid", error=str(exc))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid") from exc

    handled_types = {
        "checkout.session.completed",
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
        "invoice.paid",
        "invoice.payment_failed",
    }
    if event["type"] in handled_types:
        stripe_billing.apply_subscription_event(db, event)
    return {"received": "ok"}

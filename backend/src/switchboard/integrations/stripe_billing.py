"""Stripe Billing — subscription create + portal + webhook handler.

Per https://docs.stripe.com/billing/subscriptions/build-subscriptions:
- Create a Customer per Firma on signup.
- Create a Checkout Session in `mode=subscription` to subscribe to a Price.
- Listen to webhook events: ``customer.subscription.{created,updated,deleted}``,
  ``invoice.{paid,payment_failed}``, ``checkout.session.completed``.
- Customer Portal handles plan changes and cancellations from the user side.

We map Plan enum → Price id from Settings, so the Stripe products/prices
live in the dashboard (one-time setup) but mapping is configurable.
"""

from __future__ import annotations

from typing import Any

import stripe
from sqlmodel import Session

from switchboard.core.config import Settings, get_settings
from switchboard.core.logging import get_logger
from switchboard.core.time import utcnow
from switchboard.models import Firma, Plan, StripeEventType, StripeSubscriptionStatus

log = get_logger("switchboard.stripe")

_DEFAULT_BILLING_COUNTRY = "SE"
_STRIPE_MODE_SUBSCRIPTION = "subscription"
_STRIPE_BILLING_REQUIRED = "required"

_BLOCKED_SUBSCRIPTION_STATUSES: frozenset[StripeSubscriptionStatus] = frozenset(
    {
        StripeSubscriptionStatus.INCOMPLETE,
        StripeSubscriptionStatus.INCOMPLETE_EXPIRED,
        StripeSubscriptionStatus.CANCELED,
    }
)


def _client(settings: Settings | None = None) -> "stripe":  # type: ignore[valid-type]
    s = settings or get_settings()
    if not s.stripe_api_key:
        msg = "stripe_not_configured"
        raise RuntimeError(msg)
    stripe.api_key = s.stripe_api_key
    return stripe


def price_for_plan(plan: Plan, settings: Settings | None = None) -> str:
    s = settings or get_settings()
    return {
        Plan.STARTER: s.stripe_price_starter,
        Plan.PROFESSIONAL: s.stripe_price_professional,
        Plan.PREMIUM: s.stripe_price_premium,
    }[plan]


def plan_from_price(price_id: str, settings: Settings | None = None) -> Plan | None:
    s = settings or get_settings()
    if price_id == s.stripe_price_premium:
        return Plan.PREMIUM
    if price_id == s.stripe_price_professional:
        return Plan.PROFESSIONAL
    if price_id == s.stripe_price_starter:
        return Plan.STARTER
    return None


def ensure_customer(
    session: Session,
    firma: Firma,
    *,
    email: str,
    settings: Settings | None = None,
) -> str:
    if firma.stripe_customer_id:
        return firma.stripe_customer_id
    sc = _client(settings)
    customer = sc.Customer.create(
        email=email,
        name=firma.name,
        metadata={"firma_id": firma.id},
        address={"country": _DEFAULT_BILLING_COUNTRY},
    )
    firma.stripe_customer_id = customer.id
    session.add(firma)
    session.commit()
    log.info("stripe.customer.created", firma=firma.id, customer=customer.id)
    return customer.id


def create_checkout_session(
    session: Session,
    firma: Firma,
    *,
    plan: Plan,
    success_url: str,
    cancel_url: str,
    email: str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    sc = _client(settings)
    customer_id = ensure_customer(session, firma, email=email, settings=settings)
    price = price_for_plan(plan, settings)
    if not price:
        msg = f"no_price_configured_for_plan:{plan.value}"
        raise RuntimeError(msg)
    cs = sc.checkout.Session.create(
        customer=customer_id,
        mode=_STRIPE_MODE_SUBSCRIPTION,
        line_items=[{"price": price, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=firma.id,
        billing_address_collection=_STRIPE_BILLING_REQUIRED,
    )
    return {"id": cs.id, "url": cs.url}


def create_portal_session(
    firma: Firma,
    *,
    return_url: str | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    s = settings or get_settings()
    sc = _client(s)
    if not firma.stripe_customer_id:
        msg = "stripe_customer_missing"
        raise RuntimeError(msg)
    portal = sc.billing_portal.Session.create(
        customer=firma.stripe_customer_id,
        return_url=return_url or s.stripe_portal_return_url,
    )
    return {"url": portal.url}


def construct_event(payload: bytes, sig_header: str, settings: Settings | None = None):  # type: ignore[no-untyped-def]
    s = settings or get_settings()
    if not s.stripe_webhook_secret:
        msg = "stripe_webhook_not_configured"
        raise RuntimeError(msg)
    return stripe.Webhook.construct_event(
        payload, sig_header, s.stripe_webhook_secret
    )


def apply_subscription_event(
    session: Session,
    event: dict[str, Any],
    settings: Settings | None = None,
) -> Firma | None:
    """Update the Firma's subscription state from a Stripe event."""
    s = settings or get_settings()
    obj = event["data"]["object"]
    customer_id = obj.get("customer") or (obj.get("subscription") and obj.get("customer"))
    if not customer_id:
        return None

    firma = session.query(Firma).filter(Firma.stripe_customer_id == customer_id).first()
    if firma is None:
        log.warning("stripe.event.no_matching_firma", customer=customer_id, event_type=event["type"])
        return None

    etype = event["type"]
    if etype.startswith(StripeEventType.SUBSCRIPTION_PREFIX.value):
        firma.stripe_subscription_id = obj.get("id")
        firma.subscription_status = obj.get("status", StripeSubscriptionStatus.INCOMPLETE.value)
        items = (obj.get("items") or {}).get("data") or []
        if items:
            price_id = items[0].get("price", {}).get("id")
            if price_id:
                plan = plan_from_price(price_id, s)
                if plan is not None:
                    firma.plan = plan
        period_end = obj.get("current_period_end")
        if period_end:
            from datetime import datetime, timezone

            firma.plan_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)
            firma.plan_calls_used_period = 0
    elif etype == StripeEventType.INVOICE_PAID.value:
        firma.subscription_status = StripeSubscriptionStatus.ACTIVE.value
    elif etype == StripeEventType.INVOICE_PAYMENT_FAILED.value:
        firma.subscription_status = StripeSubscriptionStatus.PAST_DUE.value
    elif etype == StripeEventType.CHECKOUT_COMPLETED.value:
        firma.subscription_status = StripeSubscriptionStatus.ACTIVE.value

    firma.updated_at = utcnow()
    session.add(firma)
    session.commit()
    log.info("stripe.event.applied", firma=firma.id, event_type=etype, status=firma.subscription_status)
    return firma


# --- Plan enforcement ---


PLAN_LIMITS: dict[Plan, dict[str, int]] = {
    Plan.STARTER: {"calls_per_month": 200, "concurrent_calls": 5, "phone_numbers": 1},
    Plan.PROFESSIONAL: {"calls_per_month": 600, "concurrent_calls": 25, "phone_numbers": 3},
    Plan.PREMIUM: {"calls_per_month": 1_000_000, "concurrent_calls": 1_000, "phone_numbers": 100},
}


def check_call_allowed(firma: Firma) -> tuple[bool, str | None]:
    """Return (allowed, reason). Used by the bridge / webhook to gate ingress."""
    if firma.subscription_status in {s.value for s in _BLOCKED_SUBSCRIPTION_STATUSES}:
        return False, f"subscription_{firma.subscription_status}"
    limits = PLAN_LIMITS.get(firma.plan, PLAN_LIMITS[Plan.STARTER])
    if firma.plan_calls_used_period >= limits["calls_per_month"]:
        return False, "plan_calls_exhausted"
    return True, None


def increment_call_counter(session: Session, firma: Firma) -> None:
    firma.plan_calls_used_period += 1
    session.add(firma)
    session.commit()

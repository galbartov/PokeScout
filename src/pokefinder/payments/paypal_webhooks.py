"""
PayPal webhook handler.
Updates user subscription status based on PayPal Subscriptions API events.
"""
from __future__ import annotations

import hashlib
import hmac
import logging

import httpx
from fastapi import APIRouter, HTTPException, Request, Response

from pokefinder.config import settings
from pokefinder.db import get_client
from pokefinder.db import queries

logger = logging.getLogger(__name__)
router = APIRouter()

PAYPAL_API_BASE = "https://api-m.paypal.com"
PAYPAL_SANDBOX_BASE = "https://api-m.sandbox.paypal.com"


def _paypal_base() -> str:
    return PAYPAL_API_BASE if settings.is_production else PAYPAL_SANDBOX_BASE


async def _verify_webhook_signature(request: Request, body: bytes) -> bool:
    """Verify PayPal webhook signature using the PayPal verify-webhook-signature API."""
    if not settings.paypal_client_id or not settings.paypal_secret:
        return True  # skip in dev if not configured

    headers = request.headers
    payload = {
        "auth_algo": headers.get("paypal-auth-algo", ""),
        "cert_url": headers.get("paypal-cert-url", ""),
        "transmission_id": headers.get("paypal-transmission-id", ""),
        "transmission_sig": headers.get("paypal-transmission-sig", ""),
        "transmission_time": headers.get("paypal-transmission-time", ""),
        "webhook_id": settings.paypal_webhook_id,
        "webhook_event": body.decode("utf-8"),
    }

    token_url = f"{_paypal_base()}/v1/oauth2/token"
    verify_url = f"{_paypal_base()}/v1/notifications/verify-webhook-signature"

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            token_url,
            data={"grant_type": "client_credentials"},
            auth=(settings.paypal_client_id, settings.paypal_secret),
        )
        if token_resp.status_code != 200:
            return False
        access_token = token_resp.json()["access_token"]

        verify_resp = await client.post(
            verify_url,
            json=payload,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if verify_resp.status_code != 200:
            return False
        return verify_resp.json().get("verification_status") == "SUCCESS"


@router.post("/webhooks/paypal")
async def paypal_webhook(request: Request) -> Response:
    body = await request.body()

    if not await _verify_webhook_signature(request, body):
        raise HTTPException(status_code=400, detail="Invalid signature")

    import json
    event = json.loads(body)
    event_type = event.get("event_type", "")
    resource = event.get("resource", {})

    db = await get_client()

    if event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
        subscription_id = resource.get("id")
        user_id = resource.get("custom_id")
        if user_id:
            await queries.update_user(db, user_id, {
                "is_subscribed": True,
                "paypal_subscription_id": subscription_id,
            })
            logger.info("User %s subscription activated (PayPal %s)", user_id, subscription_id)

            user = (await db.table("users").select("*").eq("id", user_id).maybe_single().execute()).data
            if user and user.get("telegram_id"):
                try:
                    from telegram import Bot
                    bot = Bot(token=settings.telegram_bot_token)
                    await bot.send_message(
                        chat_id=user["telegram_id"],
                        text="Your PokeScout subscription is now active! You'll receive unlimited deal alerts.",
                    )
                except Exception:
                    pass

    elif event_type in ("BILLING.SUBSCRIPTION.CANCELLED", "BILLING.SUBSCRIPTION.EXPIRED"):
        subscription_id = resource.get("id")
        if subscription_id:
            users_res = await db.table("users").select("*").eq("paypal_subscription_id", subscription_id).maybe_single().execute()
            user = users_res.data
            if user:
                await queries.update_user(db, user["id"], {
                    "is_subscribed": False,
                    "subscription_expires_at": None,
                })
                logger.info("User %s subscription %s (PayPal %s)", user["id"], event_type.lower(), subscription_id)

    elif event_type == "PAYMENT.SALE.COMPLETED":
        # Optional: log payment
        amount = resource.get("amount", {})
        logger.info("PayPal payment completed: %s %s", amount.get("total"), amount.get("currency"))

    return Response(content="ok", status_code=200)

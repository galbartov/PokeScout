"""
Paddle webhook handler.
Updates user subscription status based on subscription lifecycle events.
"""
from __future__ import annotations

import hashlib
import hmac
import logging

from fastapi import APIRouter, HTTPException, Request, Response

from pokefinder.config import settings
from pokefinder.db import get_client
from pokefinder.db import queries

logger = logging.getLogger(__name__)
router = APIRouter()


def _verify_signature(payload: bytes, signature_header: str) -> bool:
    """Verify Paddle webhook signature (h1 scheme)."""
    if not signature_header or not settings.paddle_webhook_secret:
        return False

    # Header format: ts=<timestamp>;h1=<signature>
    parts = dict(p.split("=", 1) for p in signature_header.split(";") if "=" in p)
    ts = parts.get("ts", "")
    h1 = parts.get("h1", "")

    signed = f"{ts}:{payload.decode('utf-8')}"
    expected = hmac.new(
        settings.paddle_webhook_secret.encode("utf-8"),
        signed.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, h1)


@router.post("/webhooks/paddle")
async def paddle_webhook(request: Request) -> Response:
    payload = await request.body()
    sig_header = request.headers.get("paddle-signature", "")

    if not _verify_signature(payload, sig_header):
        raise HTTPException(status_code=400, detail="Invalid signature")

    import json
    event = json.loads(payload)
    event_type = event.get("event_type", "")
    data = event.get("data", {})

    db = await get_client()

    if event_type == "subscription.activated":
        await _handle_activated(db, data)

    elif event_type == "subscription.updated":
        await _handle_updated(db, data)

    elif event_type == "subscription.canceled":
        await _handle_canceled(db, data)

    elif event_type == "subscription.past_due":
        await _handle_past_due(db, data)

    return Response(content="ok", status_code=200)


async def _get_user_by_paddle_id(db, paddle_customer_id: str) -> dict | None:
    res = await db.table("users").select("*").eq("paddle_customer_id", paddle_customer_id).maybe_single().execute()
    return res.data


async def _handle_activated(db, data: dict) -> None:
    customer_id = data.get("customer_id")
    subscription_id = data.get("id")
    next_billed = data.get("next_billed_at")

    # user_id is passed as custom_data when opening checkout
    custom_data = data.get("custom_data") or {}
    user_id = custom_data.get("user_id")

    if user_id:
        await queries.update_user(db, user_id, {
            "is_subscribed": True,
            "paddle_customer_id": customer_id,
            "paddle_subscription_id": subscription_id,
            "subscription_expires_at": next_billed,
        })
        logger.info("User %s subscribed via Paddle (activated)", user_id)

        # Send Telegram confirmation
        user = (await db.table("users").select("*").eq("id", user_id).maybe_single().execute()).data
        await _notify_user_subscribed(user)
    else:
        logger.warning("subscription.activated received without user_id in custom_data")


async def _handle_updated(db, data: dict) -> None:
    customer_id = data.get("customer_id")
    status = data.get("status")
    next_billed = data.get("next_billed_at")
    canceled_at = data.get("canceled_at")

    user = await _get_user_by_paddle_id(db, customer_id)
    if not user:
        return

    is_active = status in ("active", "trialing")
    expires = next_billed if is_active else canceled_at

    await queries.update_user(db, user["id"], {
        "is_subscribed": is_active,
        "subscription_expires_at": expires,
    })
    logger.info("User %s subscription updated: status=%s", user["id"], status)


async def _handle_canceled(db, data: dict) -> None:
    customer_id = data.get("customer_id")
    canceled_at = data.get("canceled_at")

    user = await _get_user_by_paddle_id(db, customer_id)
    if not user:
        return

    await queries.update_user(db, user["id"], {
        "is_subscribed": False,
        "subscription_expires_at": canceled_at,
    })
    logger.info("User %s subscription canceled", user["id"])

    if user.get("telegram_id"):
        try:
            from telegram import Bot
            from pokefinder.config import settings as s
            bot = Bot(token=s.telegram_bot_token)
            await bot.send_message(
                chat_id=user["telegram_id"],
                text="Your TCG Scout Pro subscription has been canceled. You can resubscribe anytime with /subscribe.",
            )
        except Exception:
            pass


async def _handle_past_due(db, data: dict) -> None:
    customer_id = data.get("customer_id")

    user = await _get_user_by_paddle_id(db, customer_id)
    if not user:
        return

    await queries.update_user(db, user["id"], {"is_subscribed": False})
    logger.warning("User %s subscription past due — access suspended", user["id"])

    if user.get("telegram_id"):
        try:
            from telegram import Bot
            from pokefinder.config import settings as s
            bot = Bot(token=s.telegram_bot_token)
            await bot.send_message(
                chat_id=user["telegram_id"],
                text="⚠️ Your TCG Scout Pro payment is past due. Please update your payment method to continue receiving alerts.",
            )
        except Exception:
            pass


async def _notify_user_subscribed(user: dict | None) -> None:
    if not user or not user.get("telegram_id"):
        return
    try:
        from telegram import Bot
        from pokefinder.config import settings as s
        bot = Bot(token=s.telegram_bot_token)
        await bot.send_message(
            chat_id=user["telegram_id"],
            text="✅ Your TCG Scout Pro subscription is now active! You'll receive unlimited deal alerts.",
        )
    except Exception:
        pass

"""
Stripe webhook handler.
Updates user subscription status based on checkout completion and subscription events.
"""
from __future__ import annotations

import logging

import stripe
from fastapi import APIRouter, HTTPException, Request, Response

from pokefinder.config import settings
from pokefinder.db import get_client
from pokefinder.db import queries

logger = logging.getLogger(__name__)
router = APIRouter()

stripe.api_key = settings.stripe_secret_key


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request) -> Response:
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    db = await get_client()
    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        user_id = data.get("metadata", {}).get("user_id")
        customer_id = data.get("customer")
        subscription_id = data.get("subscription")

        if user_id:
            await queries.update_user(db, user_id, {
                "is_subscribed": True,
                "stripe_customer_id": customer_id,
            })
            logger.info("User %s subscribed (checkout complete)", user_id)

            # Notify user on Telegram
            user = (await db.table("users").select("*").eq("id", user_id).maybe_single().execute()).data
            if user and user.get("telegram_id"):
                try:
                    from telegram import Bot
                    bot = Bot(token=settings.telegram_bot_token)
                    from pokefinder.i18n import t
                    locale = user.get("locale", "he")
                    await bot.send_message(
                        chat_id=user["telegram_id"],
                        text="✅ " + ("המנוי שלך הופעל בהצלחה! תקבל התראות ללא הגבלה." if locale == "he" else "Your subscription is now active! You'll receive unlimited alerts."),
                    )
                except Exception:
                    pass

    elif event_type == "customer.subscription.updated":
        customer_id = data.get("customer")
        status = data.get("status")
        current_period_end = data.get("current_period_end")

        users_res = await db.table("users").select("*").eq("stripe_customer_id", customer_id).maybe_single().execute()
        user = users_res.data
        if user:
            from datetime import datetime, timezone
            expires = datetime.fromtimestamp(current_period_end, tz=timezone.utc).isoformat() if current_period_end else None
            await queries.update_user(db, user["id"], {
                "is_subscribed": status in ("active", "trialing"),
                "subscription_expires_at": expires,
            })

    elif event_type == "customer.subscription.deleted":
        customer_id = data.get("customer")
        users_res = await db.table("users").select("*").eq("stripe_customer_id", customer_id).maybe_single().execute()
        user = users_res.data
        if user:
            await queries.update_user(db, user["id"], {
                "is_subscribed": False,
                "subscription_expires_at": None,
            })
            logger.info("User %s subscription cancelled", user["id"])

    return Response(content="ok", status_code=200)

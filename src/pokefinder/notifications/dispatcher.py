"""
Notification dispatcher.
Checks subscription gate, prevents double-sending, routes to correct channel(s),
and tracks sent notifications in DB.
"""
from __future__ import annotations

import logging

from supabase import AsyncClient

from pokefinder.bots.service import BotService
from pokefinder.config import settings
from pokefinder.db import queries

logger = logging.getLogger(__name__)


async def dispatch_notification(
    db: AsyncClient,
    user: dict,
    listing: dict,
    preference: dict,
) -> bool:
    """
    Send a deal notification to a user for a listing.
    Returns True if at least one channel succeeded.
    """
    user_id = user["id"]
    listing_id = listing["id"]

    # ── Prevent double-send ───────────────────────────────────────────────
    if await queries.notification_exists(db, user_id, listing_id):
        return False

    # ── Check subscription gate ───────────────────────────────────────────
    svc = BotService(db)
    is_sub = svc.is_subscribed(user)
    free_left = svc.free_deals_remaining(user)

    if not is_sub and free_left <= 0:
        pass  # Cap disabled for testing

    # ── Build message ─────────────────────────────────────────────────────
    pref_name = preference.get("name", "?")

    # Fetch market price for deal quality signal (best-effort, non-blocking)
    market_price: float | None = None
    try:
        from pokefinder.scrapers.ebay import get_last_sold_price
        title = listing.get("title", "")
        if title:
            market_price = await get_last_sold_price(title)
    except Exception:
        pass

    message = svc.format_deal_message(listing, pref_name, market_price=market_price)

    # Append auction context if applicable
    buying_format = listing.get("buying_format")
    auction_end_time = listing.get("auction_end_time")
    if buying_format == "AUCTION" and auction_end_time:
        from datetime import datetime, timezone
        try:
            end_dt = datetime.fromisoformat(auction_end_time.replace("Z", "+00:00"))
            hours = (end_dt - datetime.now(timezone.utc)).total_seconds() / 3600
            if hours > 0:
                h = int(hours)
                m = int((hours - h) * 60)
                message += f"\nAuction ends in {h}h {m}m"
        except Exception:
            pass

    image_url = None
    image_urls = listing.get("image_urls") or []
    if image_urls:
        image_url = image_urls[0]

    # ── Route to channels ─────────────────────────────────────────────────
    channels = user.get("notification_channels") or ["telegram"]
    any_success = False

    if "telegram" in channels and user.get("telegram_id"):
        from pokefinder.notifications import telegram as tg_notif
        success = await tg_notif.send_deal(
            telegram_id=user["telegram_id"],
            message_text=message,
            image_url=image_url,
        )
        if success:
            any_success = True

    if "whatsapp" in channels and user.get("whatsapp_phone"):
        from pokefinder.notifications import whatsapp as wa_notif
        # For WhatsApp, pass image_url directly (Twilio fetches it)
        success = await wa_notif.send_deal(
            phone=user["whatsapp_phone"],
            message_text=message,
            image_url=image_url,
        )
        if success:
            any_success = True

    if not any_success:
        return False

    # ── Record in DB ──────────────────────────────────────────────────────
    try:
        await queries.create_notification(db, {
            "user_id": user_id,
            "listing_id": listing_id,
            "preference_id": preference.get("id"),
            "channel": "+".join(channels),
            "status": "sent",
        })
    except Exception:
        pass  # Unique constraint violation is fine (race condition)

    # ── Increment free deal counter if on trial ───────────────────────────
    if not is_sub:
        await svc.increment_free_deals(user_id, user.get("free_deals_used", 0))

        # If this was the last free deal, send a paywall notice
        if free_left == 1:
            checkout_url = svc.generate_checkout_url(user)
            from pokefinder.i18n import t
            paywall_msg = t(
                "free_deals_exhausted",
                "en",
                checkout_url=checkout_url,
            )
            if user.get("telegram_id"):
                from pokefinder.notifications import telegram as tg_notif
                await tg_notif.send_deal(user["telegram_id"], paywall_msg)
            if user.get("whatsapp_phone"):
                from pokefinder.notifications import whatsapp as wa_notif
                await wa_notif.send_deal(user["whatsapp_phone"], paywall_msg)

    return True

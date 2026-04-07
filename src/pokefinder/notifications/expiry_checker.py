"""
Periodically check if notified listings are still active.
If a listing has sold or expired, edit the Telegram notification to reflect that.
"""
from __future__ import annotations

import logging

import httpx

from pokefinder.db import get_client

logger = logging.getLogger(__name__)

# How many notifications to check per run (avoid rate limits)
_BATCH_SIZE = 50


_EBAY_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

_SOLD_SIGNALS = [
    "This listing was ended",
    "This item is no longer available",
    "Bid History - Ended",
    "BidItemNotAvailable",
    "Item not found",
    "itm/sold",
    # title-tag signals (faster — appear in first ~2KB)
    "<title>404</title>",
    "Page Not Found",
]


async def _is_ebay_listing_active(url: str) -> bool:
    """Return False if the eBay listing has ended or sold."""
    try:
        async with httpx.AsyncClient(
            timeout=15,
            follow_redirects=True,
            headers=_EBAY_HEADERS,
        ) as client:
            resp = await client.get(url)

            # Explicit 404
            if resp.status_code == 404:
                return False

            # Check final URL after redirects
            final_url = str(resp.url)
            if "BidItemNotAvailable" in final_url or "/itm/sold" in final_url:
                return False

            # Scan first 6KB of HTML for sold signals (title + early body)
            text = resp.text[:6000]
            for signal in _SOLD_SIGNALS:
                if signal in text:
                    return False

        return True
    except Exception as e:
        logger.debug("Error checking listing status for %s: %s", url, e)
        return True  # Assume active on error to avoid false edits


async def _is_tcgplayer_listing_active(url: str) -> bool:
    """TCGPlayer listings don't expire the same way — skip for now."""
    return True


async def check_and_update_expired_listings() -> None:
    """
    Find recent unedited notifications with a telegram_message_id,
    check if their listing is still active, and edit the message if not.
    """
    db = await get_client()

    # Fetch recent notifications that have a telegram_message_id and aren't already marked expired
    try:
        res = await (
            db.table("notifications")
            .select("id, user_id, listing_id, telegram_message_id, status, message_text")
            .eq("status", "sent")
            .not_.is_("telegram_message_id", "null")
            .order("sent_at", desc=True)
            .limit(_BATCH_SIZE)
            .execute()
        )
        notifications = res.data or []
    except Exception as e:
        logger.error("expiry_checker: failed to fetch notifications: %s", e)
        return

    if not notifications:
        return

    listing_ids = list({n["listing_id"] for n in notifications})

    # Fetch all relevant listings in one query
    try:
        lst_res = await (
            db.table("listings")
            .select("id, url, platform, title, is_active")
            .in_("id", listing_ids)
            .execute()
        )
        listings_by_id = {l["id"]: l for l in (lst_res.data or [])}
    except Exception as e:
        logger.error("expiry_checker: failed to fetch listings: %s", e)
        return

    # Fetch user telegram_ids
    user_ids = list({n["user_id"] for n in notifications})
    try:
        usr_res = await (
            db.table("users")
            .select("id, telegram_id")
            .in_("id", user_ids)
            .execute()
        )
        users_by_id = {u["id"]: u for u in (usr_res.data or [])}
    except Exception as e:
        logger.error("expiry_checker: failed to fetch users: %s", e)
        return

    from pokefinder.notifications.telegram import edit_deal

    edited = 0
    for notif in notifications:
        listing = listings_by_id.get(notif["listing_id"])
        if not listing:
            continue

        url = listing.get("url", "")
        platform = listing.get("platform", "")

        # If already marked inactive in DB, we still need to edit the message
        # (the DB update may have succeeded but the Telegram edit failed previously)
        already_inactive = listing.get("is_active") is False

        if not already_inactive:
            if platform == "ebay":
                active = await _is_ebay_listing_active(url)
            else:
                active = await _is_tcgplayer_listing_active(url)

            if active:
                continue

            # Mark listing inactive in DB
            try:
                await db.table("listings").update({"is_active": False}).eq("id", listing["id"]).execute()
            except Exception as e:
                logger.debug("expiry_checker: failed to mark listing inactive: %s", e)

        # Edit the Telegram message — append sold notice to original message text
        user = users_by_id.get(notif["user_id"])
        telegram_id = user.get("telegram_id") if user else None
        msg_id = notif.get("telegram_message_id")

        if telegram_id and msg_id:
            original_text = notif.get("message_text") or listing.get("title", "This item")
            new_text = original_text + "\n\n❌ *This listing has ended or sold.*"
            try:
                ok = await edit_deal(
                    telegram_id=telegram_id,
                    message_id=msg_id,
                    new_text=new_text,
                )
                if ok:
                    edited += 1
                    await db.table("notifications").update({"status": "expired"}).eq("id", notif["id"]).execute()
            except Exception as e:
                logger.debug("expiry_checker: edit failed for notif %s: %s", notif["id"], e)

    if edited:
        logger.info("expiry_checker: marked %d notifications as expired and edited messages", edited)

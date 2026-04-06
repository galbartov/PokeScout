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


async def _is_ebay_listing_active(url: str) -> bool:
    """Return False if eBay returns 404 or a 'sold/ended' redirect."""
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.head(url)
            if resp.status_code == 404:
                return False
            # eBay redirects ended auctions to /itm/<id>?... with a different path pattern
            # or to /e/... — a simple heuristic: check final URL for known sold indicators
            final_url = str(resp.url)
            if "BidItemNotAvailable" in final_url or "vi/itm/sold" in final_url:
                return False
            # GET the page to check for "Item not found" in body
            if resp.status_code == 200:
                get_resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                text = get_resp.text[:4000]
                sold_signals = [
                    "This listing was ended",
                    "Item not found",
                    "This item is no longer available",
                    "Bid History - Ended",
                ]
                for signal in sold_signals:
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
            .select("id, user_id, listing_id, telegram_message_id, status")
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

        # Skip listings already marked inactive in DB
        if listing.get("is_active") is False:
            continue

        url = listing.get("url", "")
        platform = listing.get("platform", "")

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

        # Edit the Telegram message
        user = users_by_id.get(notif["user_id"])
        telegram_id = user.get("telegram_id") if user else None
        msg_id = notif.get("telegram_message_id")

        if telegram_id and msg_id:
            title = listing.get("title", "This item")
            suffix = "\n\n❌ *This listing has ended or sold.*"
            # We don't have the original message text — just append a note
            # by editing with a short status update
            try:
                ok = await edit_deal(
                    telegram_id=telegram_id,
                    message_id=msg_id,
                    new_text=f"_{title[:80]}_\n{suffix}",
                )
                if ok:
                    edited += 1
                    # Mark notification as expired
                    await db.table("notifications").update({"status": "expired"}).eq("id", notif["id"]).execute()
            except Exception as e:
                logger.debug("expiry_checker: edit failed for notif %s: %s", notif["id"], e)

    if edited:
        logger.info("expiry_checker: marked %d notifications as expired and edited messages", edited)

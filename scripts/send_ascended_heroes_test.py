"""
One-off test script: send stored Ascended Heroes ETB Facebook listings to the admin Telegram ID.
Does NOT write to the notifications table or touch free_deals_used.
"""
import asyncio
import logging
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from pokefinder.db.supabase_client import get_client
from pokefinder.notifications import telegram as tg_notif
from pokefinder.config import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

KEYWORD = "ascended heroes"


def _escape_md(text: str) -> str:
    """Escape Telegram MarkdownV1 special characters."""
    return re.sub(r'([_*\[\]`])', r'\\\1', str(text))


def format_message(listing: dict) -> str:
    title = _escape_md(listing.get("title", ""))
    price = listing.get("price")
    price_str = f"{price:,.0f}" if price else "?"
    location = _escape_md(listing.get("location_text") or "")
    seller = _escape_md(listing.get("seller_contact") or listing.get("seller_name") or "—")
    url = listing.get("url", "")

    lines = [
        "🔔 *עסקה חדשה נמצאה!*",
        "",
        f"📦 {title}",
        f"💰 ₪{price_str}",
    ]
    if location:
        lines.append(f"📍 {location}")
    lines += [
        "🏪 Facebook",
        "",
        f"👤 מוכר: {seller}",
        f"🔗 {url}",
    ]
    return "\n".join(lines)


async def main() -> None:
    db = await get_client()
    admin_id = settings.admin_telegram_id
    if not admin_id:
        logger.error("ADMIN_TELEGRAM_ID not set in .env")
        return

    # Fetch Facebook listings matching "ascended heroes"
    res = (
        await db.table("listings")
        .select("*")
        .ilike("title", f"%{KEYWORD}%")
        .eq("platform", "facebook")
        .execute()
    )
    listings = res.data

    if not listings:
        logger.info("No Facebook listings found matching '%s'", KEYWORD)
        return

    logger.info("Found %d Facebook listing(s) for '%s'", len(listings), KEYWORD)

    for listing in listings:
        message = format_message(listing)
        image_url = (listing.get("image_urls") or [None])[0]

        logger.info("Sending: %s — ₪%s", listing.get("title"), listing.get("price"))
        success = await tg_notif.send_deal(
            telegram_id=admin_id,
            message_text=message,
            image_url=image_url,
        )
        logger.info("  → %s", "sent" if success else "FAILED")

    logger.info("Done.")


if __name__ == "__main__":
    asyncio.run(main())

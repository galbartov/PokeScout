"""
APScheduler-based periodic tasks.
Runs the eBay scraper every N minutes,
persists new listings, and triggers the matching engine.
"""
from __future__ import annotations

import logging
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from pokefinder.config import settings
from pokefinder.db import get_client
from pokefinder.db import queries
from pokefinder.matching.dedup import is_title_price_duplicate
from pokefinder.matching.parser import detect_category, normalize_title, parse_grade
from pokefinder.scrapers import EbayScraper, TCGPlayerScraper
from pokefinder.scrapers.base import RawListing

logger = logging.getLogger(__name__)



async def _persist_listings(raw_listings: list[RawListing], platform: str) -> list[str]:
    """
    Persist new listings to DB after dedup checks.
    Returns list of IDs of newly inserted listings.
    """
    if not raw_listings:
        return []

    db = await get_client()
    new_ids: list[str] = []

    # Pre-load titles for dedup (only needed for listings without external_id)
    existing_titles = await queries.get_recent_normalized_titles(db, days=7)

    # Pre-load existing external_ids for this platform (paginated)
    existing_external_ids: set[str] = set()
    offset = 0
    while True:
        ext_res = await db.table("listings").select("external_id").eq("platform", platform).range(offset, offset + 999).execute()
        for r in ext_res.data:
            if r["external_id"]:
                existing_external_ids.add(r["external_id"])
        if len(ext_res.data) < 1000:
            break
        offset += 1000

    # Build list of records to insert
    pending: list[dict] = []
    for raw in raw_listings:
        # ── Check exact external_id ───────────────────────────────────────
        if raw.external_id:
            if raw.external_id in existing_external_ids:
                continue

        normalized = normalize_title(raw.title)

        # ── Title + price dedup (only for listings without a stable external_id) ──
        if not raw.external_id and is_title_price_duplicate(normalized, raw.price, existing_titles):
            logger.debug("Dedup (title/price): skipping '%s'", raw.title[:50])
            continue

        # ── Parse category + grade ────────────────────────────────────────
        grading_company, detected_grade, grade_value = parse_grade(raw.title)
        category = detect_category(raw.title)

        pending.append({
            "platform": platform,
            "external_id": raw.external_id,
            "url": raw.url,
            "title": raw.title,
            "title_normalized": normalized,
            "description": raw.description,
            "price": raw.price,
            "currency": raw.currency,
            "image_urls": raw.image_urls,
            "seller_name": raw.seller_name,
            "seller_contact": raw.seller_contact,
            "location_text": raw.location_text,
            "buying_format": raw.buying_format,
            "auction_end_time": raw.auction_end_time,
            "category": category,
            "detected_grade": detected_grade,
            "grading_company": grading_company,
            "grade_value": grade_value,
            "raw_data": raw.raw_data,
        })
        if not raw.external_id:
            existing_titles.append({"title_normalized": normalized, "price": raw.price})

    # ── Batch insert in chunks of 500 ────────────────────────────────────
    CHUNK = 500
    for i in range(0, len(pending), CHUNK):
        chunk = pending[i: i + CHUNK]
        try:
            ids = await queries.insert_listings_batch(db, chunk)
            new_ids.extend(ids)
        except Exception as e:
            # Fall back to individual inserts on batch error (e.g. unique constraint)
            for record in chunk:
                try:
                    inserted = await queries.insert_listing(db, record)
                    new_ids.append(inserted["id"])
                except Exception:
                    pass

    return new_ids


async def run_ebay_scrape() -> None:
    """Scheduled task: scrape eBay and run matching on new listings."""
    db = await get_client()
    run_id = await queries.start_scrape_run(db, "ebay")
    start = time.time()

    scraper = EbayScraper()
    raw_listings, error = await scraper.run()

    new_ids = await _persist_listings(raw_listings, "ebay")

    duration_ms = int((time.time() - start) * 1000)
    await queries.finish_scrape_run(
        db, run_id,
        status="failed" if error else "completed",
        listings_found=len(raw_listings),
        new_listings=len(new_ids),
        duration_ms=duration_ms,
        error_message=error,
    )

    if new_ids:
        from pokefinder.matching.engine import match_and_notify
        sent = await match_and_notify(new_ids)
        logger.info("eBay scrape: %d new listings, %d notifications sent", len(new_ids), sent)
    else:
        logger.info("eBay scrape: no new listings")


async def run_tcgplayer_scrape() -> None:
    """Scheduled task: scrape TCGPlayer and run matching on new listings."""
    db = await get_client()
    run_id = await queries.start_scrape_run(db, "tcgplayer")
    start = time.time()

    scraper = TCGPlayerScraper()
    raw_listings, error = await scraper.run()

    new_ids = await _persist_listings(raw_listings, "tcgplayer")

    duration_ms = int((time.time() - start) * 1000)
    await queries.finish_scrape_run(
        db, run_id,
        status="failed" if error else "completed",
        listings_found=len(raw_listings),
        new_listings=len(new_ids),
        duration_ms=duration_ms,
        error_message=error,
    )

    if new_ids:
        from pokefinder.matching.engine import match_and_notify
        sent = await match_and_notify(new_ids)
        logger.info("TCGPlayer scrape: %d new listings, %d notifications sent", len(new_ids), sent)
    else:
        logger.info("TCGPlayer scrape: no new listings")


async def run_cleanup() -> None:
    """Nightly job: delete listings older than 14 days to keep DB lean."""
    db = await get_client()
    from datetime import datetime, timezone, timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    res = await db.table("listings").delete().lt("scraped_at", cutoff).execute()
    deleted = len(res.data) if res.data else 0
    logger.info("Cleanup: deleted %d listings older than 14 days", deleted)


async def run_deadmans_switch() -> None:
    """
    Check that the last eBay scrape completed within the expected window.
    If no successful run in the last 15 minutes, alert the admin via Telegram.
    """
    db = await get_client()
    runs = await queries.get_recent_scrape_runs(db, limit=1)
    if not runs:
        return

    last = runs[0]
    if last.get("platform") != "ebay" or last.get("status") != "completed":
        return

    from datetime import datetime, timezone, timedelta
    completed_at = last.get("completed_at")
    if not completed_at:
        return

    try:
        dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
        age_minutes = (datetime.now(timezone.utc) - dt).total_seconds() / 60
        if age_minutes > 15:
            msg = (
                f"⚠️ *PokeScout alert*\n"
                f"Last eBay scrape completed {age_minutes:.0f} minutes ago.\n"
                f"The scraper may be down."
            )
            if settings.admin_telegram_id:
                from pokefinder.notifications import telegram as tg_notif
                await tg_notif.send_deal(settings.admin_telegram_id, msg)
                logger.warning("Dead-man's switch fired: last scrape %s min ago", age_minutes)
    except Exception as e:
        logger.warning("Dead-man's switch check failed: %s", e)


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    interval = settings.scrape_interval_minutes

    scheduler.add_job(
        run_ebay_scrape,
        trigger="interval",
        minutes=interval,
        id="ebay_scrape",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_tcgplayer_scrape,
        trigger="interval",
        minutes=interval,
        id="tcgplayer_scrape",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_cleanup,
        trigger="cron",
        hour=3,
        minute=0,
        id="nightly_cleanup",
        max_instances=1,
    )
    scheduler.add_job(
        run_deadmans_switch,
        trigger="interval",
        minutes=15,
        id="deadmans_switch",
        max_instances=1,
        coalesce=True,
    )
    return scheduler

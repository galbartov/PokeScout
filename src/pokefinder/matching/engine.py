"""
Core matching engine.
Takes new listings and matches them against all active user preferences,
then dispatches notifications for matches.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from haversine import haversine

from pokefinder.config import settings
from pokefinder.db import get_client
from pokefinder.db import queries
from pokefinder.matching.parser import detect_category, normalize_title, parse_grade
from pokefinder.matching.pokemon_names import expand_keyword

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def _keywords_match(title: str, description: str | None, keywords: list[str]) -> bool:
    """
    Return True if keywords match title/description.
    - 1 keyword: must be present (substring).
    - 2+ keywords: ALL unique keywords must be present (AND logic).
      This ensures e.g. ['pikachu ex', '277'] only fires when BOTH
      'pikachu ex' AND '277' appear in the title — not any Pikachu ex.
    """
    if not keywords:
        return True
    search_text = (title + " " + (description or "")).lower()
    unique_keywords = list(dict.fromkeys(kw.lower() for kw in keywords if kw))
    for kw in unique_keywords:
        matched = False
        for variant in expand_keyword(kw):
            if variant.lower() in search_text:
                matched = True
                break
        if not matched:
            return False
    return True


def _price_matches(price: float | None, price_min: float | None, price_max: float | None) -> bool:
    if price is None:
        return True  # unknown price — let it through
    if price_min and price < price_min:
        return False
    if price_max and price > price_max:
        return False
    return True


def _category_matches(listing_category: str, pref_categories: list[str]) -> bool:
    if not pref_categories:
        return True
    return listing_category in pref_categories


_SEALED_REQUIRED = {"sealed", "etb", "elite trainer box", "booster box", "factory sealed"}
_SEALED_EXCLUDED = {"tin", "tins", "mini tin", "poster collection", "premium collection",
                    "pin collection", "blister", "bundle", "promo", "jumbo", "empty"}


def _sealed_listing_ok(title: str) -> bool:
    """For sealed preferences, require sealed indicators and block non-ETB/booster products."""
    t = title.lower()
    has_sealed = any(kw in t for kw in _SEALED_REQUIRED)
    is_excluded = any(kw in t for kw in _SEALED_EXCLUDED)
    return has_sealed and not is_excluded


def _location_matches(
    user_lat: float | None,
    user_lon: float | None,
    radius_km: int | None,
    listing_lat: float | None = None,
    listing_lon: float | None = None,
) -> bool:
    if radius_km is None or radius_km == 0:
        return True  # No location filter
    if user_lat is None or user_lon is None:
        return True  # User has no location set
    if listing_lat is None or listing_lon is None:
        return True  # Listing has no location — let it through
    dist = haversine((user_lat, user_lon), (listing_lat, listing_lon))
    return dist <= radius_km


def _grade_matches(
    listing_grade: float | None,
    listing_company: str | None,
    pref_grading_companies: list[str],
    pref_min_grade: float | None,
) -> bool:
    if pref_grading_companies:
        if listing_company not in pref_grading_companies:
            return False
    if pref_min_grade and listing_grade is not None:
        if listing_grade < pref_min_grade:
            return False
    return True


def _auction_matches(buying_format: str | None, auction_end_time: str | None) -> bool:
    """
    For AUCTION listings: only alert if the auction ends within 24 hours.
    Fixed-price listings always pass.
    """
    if buying_format != "AUCTION":
        return True
    if not auction_end_time:
        return True  # unknown end time — let it through
    from datetime import datetime, timezone
    try:
        end_dt = datetime.fromisoformat(auction_end_time.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        hours_remaining = (end_dt - now).total_seconds() / 3600
        return 0 < hours_remaining <= 24
    except Exception:
        return True


def _product_matches(listing_tcg_id: str | None, pref_tcg_id: str | None) -> bool:
    """If preference has a specific product ID, listing must match it.
    If the listing has no tcg_product_id (e.g. eBay), fall back to keyword matching."""
    if not pref_tcg_id:
        return True  # No product restriction
    if not listing_tcg_id:
        return True  # Listing has no TCG ID (eBay) — rely on keyword match instead
    return listing_tcg_id == pref_tcg_id


async def match_new_preference(user: dict, pref: dict) -> int:
    """
    Run a new preference against the last 24 hours of listings and
    dispatch notifications for any matches. Called immediately after
    a preference is saved so the user sees existing deals right away.
    Returns the number of notifications sent.
    """
    from datetime import datetime, timezone, timedelta
    db = await get_client()

    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    listings = []
    page_size = 1000
    offset = 0
    while True:
        res = await db.table("listings").select("*").gte("scraped_at", since).range(offset, offset + page_size - 1).execute()
        batch = res.data
        if not batch:
            break
        listings.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    if not listings:
        return 0

    from pokefinder.notifications.dispatcher import dispatch_notification

    _HISTORICAL_CAP = 7
    sent = 0

    is_sealed_pref = "sealed" in (pref.get("categories") or [])
    for listing in listings:
        if sent >= _HISTORICAL_CAP:
            break
        # Skip inactive (sold/expired) listings
        if listing.get("is_active") is False:
            continue
        if not _category_matches(listing.get("category", "singles"), pref.get("categories") or []):
            continue
        if is_sealed_pref and not _sealed_listing_ok(listing.get("title", "")):
            continue
        if not _keywords_match(listing.get("title", ""), listing.get("description"), pref.get("keywords") or []):
            continue
        if not _price_matches(listing.get("price"), pref.get("price_min"), pref.get("price_max")):
            continue
        if not _grade_matches(listing.get("grade_value"), listing.get("grading_company"), pref.get("grading_companies") or [], pref.get("min_grade")):
            continue
        if not _product_matches(listing.get("tcg_product_id"), pref.get("tcg_product_id")):
            continue
        # Skip auction end-time check for historical matches — show them regardless
        # bypass_cap=True: historical matches don't count towards free deal quota
        dispatched = await dispatch_notification(db=db, user=user, listing=listing, preference=pref, bypass_cap=True)
        if dispatched:
            sent += 1

    return sent


async def match_and_notify(listing_ids: list[str]) -> int:
    """
    Match a batch of new listing IDs against all active preferences
    and dispatch notifications. Returns the count of notifications sent.
    """
    if not listing_ids:
        return 0

    db = await get_client()

    # Load new listings in chunks to avoid URL length limits
    new_listings = []
    for i in range(0, len(listing_ids), 200):
        chunk = listing_ids[i:i + 200]
        res = await db.table("listings").select("*").in_("id", chunk).execute()
        new_listings.extend(res.data)

    if not new_listings:
        return 0

    # Load all active preferences (with user data joined)
    prefs = await queries.get_all_active_preferences(db)
    if not prefs:
        return 0

    from pokefinder.notifications.dispatcher import dispatch_notification
    notifications_sent = 0

    for listing in new_listings:
        for pref_row in prefs:
            pref = pref_row
            user = pref_row.get("users") or {}

            # Check if user can receive notification
            if not user:
                continue

            free_left = max(0, settings.free_deals_limit - user.get("free_deals_used", 0))
            is_subscribed = user.get("is_subscribed", False)
            if not is_subscribed and free_left <= 0:
                continue

            # Run matching checks
            if not _category_matches(
                listing.get("category", "singles"),
                pref.get("categories") or [],
            ):
                continue

            if "sealed" in (pref.get("categories") or []) and not _sealed_listing_ok(listing.get("title", "")):
                continue

            if not _keywords_match(
                listing.get("title", ""),
                listing.get("description"),
                pref.get("keywords") or [],
            ):
                continue

            if not _price_matches(
                listing.get("price"),
                pref.get("price_min"),
                pref.get("price_max"),
            ):
                continue

            if not _location_matches(
                user.get("location_lat"),
                user.get("location_lon"),
                pref.get("radius_km"),
            ):
                continue

            if not _grade_matches(
                listing.get("grade_value"),
                listing.get("grading_company"),
                pref.get("grading_companies") or [],
                pref.get("min_grade"),
            ):
                continue

            if not _product_matches(
                listing.get("tcg_product_id"),
                pref.get("tcg_product_id"),
            ):
                continue

            if not _auction_matches(
                listing.get("buying_format"),
                listing.get("auction_end_time"),
            ):
                continue

            # All checks passed — send notification
            sent = await dispatch_notification(
                db=db,
                user=user,
                listing=listing,
                preference=pref,
            )
            if sent:
                notifications_sent += 1

    return notifications_sent

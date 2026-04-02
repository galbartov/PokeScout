"""
eBay Browse API scraper.
Uses OAuth2 client-credentials flow to get an access token, then searches
for Pokémon TCG listings globally on eBay.
"""
from __future__ import annotations

import base64
import logging
import time

import httpx

from pokefinder.config import settings

from .base import BaseScraper, RawListing

logger = logging.getLogger(__name__)

_BROWSE_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
_AUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"

# Search queries covering Pokémon TCG globally
SEARCH_QUERIES = [
    # Singles — broad
    "pokemon card single holo",
    "pokemon card alt art secret rare",
    "pokemon card full art ultra rare",
    # Sealed — product types
    "pokemon ETB elite trainer box",
    "pokemon booster box sealed",
    "pokemon booster bundle sealed",
    "pokemon collection box sealed",
    # Sets — current & popular
    "pokemon scarlet violet booster",
    "pokemon 151 sv card",
    "pokemon surging sparks card",
    "pokemon prismatic evolutions",
    "pokemon temporal forces card",
    "pokemon paradox rift card",
    "pokemon obsidian flames card",
    "pokemon crown zenith card",
    "pokemon paldean fates card",
    # Vintage / high value
    "pokemon base set unlimited card",
    "pokemon neo genesis card",
    "pokemon ex ruby sapphire card",
    # Graded slabs
    "pokemon graded PSA 10",
    "pokemon graded BGS 9.5",
    "pokemon graded CGC 10",
    # Bulk / lots
    "pokemon cards lot bulk",
]

_token_cache: dict = {"token": None, "expires_at": 0}

# Cache for get_last_sold_price: key = query string, value = (price, expires_at)
_price_cache: dict[str, tuple[float | None, float]] = {}
_PRICE_CACHE_TTL = 3600  # 1 hour


async def _get_access_token() -> str:
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"] - 60:
        return _token_cache["token"]

    credentials = base64.b64encode(
        f"{settings.ebay_app_id}:{settings.ebay_client_secret}".encode()
    ).decode()

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            _AUTH_URL,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data="grant_type=client_credentials&scope=https://api.ebay.com/oauth/api_scope",
        )
        resp.raise_for_status()
        data = resp.json()

    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = now + data["expires_in"]
    return _token_cache["token"]


async def get_last_sold_price(
    card_name: str,
    local_id: str | None = None,
    set_total: int | None = None,
    graded: bool = False,
) -> float | None:
    """
    Fetch a market price reference for a card on eBay.

    Uses the Browse API filtered to fixed-price listings. Returns the median
    price of the top matches.

    - local_id + set_total: appended to query for precision (e.g. "231/182")
    - graded=True: restrict to graded conditions (PSA/BGS/CGC slabs)
    - graded=False: exclude graded items by filtering to ungraded conditions
    """
    if not settings.ebay_app_id or not settings.ebay_client_secret:
        return None

    # Build cache key from all inputs
    cache_key = f"{card_name}|{local_id}|{set_total}|{graded}"
    now = time.time()
    if cache_key in _price_cache:
        cached_price, expires_at = _price_cache[cache_key]
        if now < expires_at:
            return cached_price

    try:
        token = await _get_access_token()

        # Build precise query: e.g. "Team Rocket's Mewtwo ex 231/182"
        query = card_name
        if local_id and set_total:
            query = f"{card_name} {local_id}/{set_total}"
        elif local_id:
            query = f"{card_name} {local_id}"

        # Conditions:
        #   1000 = New, 1500 = New other, 2000 = Certified refurbished (used for graded slabs)
        #   2500 = Seller refurbished, 3000 = Used
        # For ungraded: use 1000|3000 (new sealed packs / used raw cards)
        # For graded: use 2000 (graded slabs are listed as "Certified refurbished" on eBay)
        #   plus exclude any title without PSA/BGS/CGC
        if graded:
            conditions = "2000|2500"
            query = f"{query} PSA BGS CGC"
        else:
            conditions = "1000|3000"
            # Exclude graded by adding negative keywords in the query
            query = f"{query} -PSA -BGS -CGC -graded"

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                _BROWSE_URL,
                params={
                    "q": query,
                    "limit": 10,
                    "sort": "newlyListed",
                    "filter": f"buyingOptions:{{FIXED_PRICE}},conditions:{{{conditions}}}",
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
                    "Content-Type": "application/json",
                },
            )
            if resp.status_code != 200:
                return None
            items = resp.json().get("itemSummaries", [])
            prices = []
            for item in items:
                price_obj = item.get("price", {})
                val = price_obj.get("value")
                if val:
                    prices.append(float(val))
            if not prices:
                _price_cache[cache_key] = (None, now + _PRICE_CACHE_TTL)
                return None
            prices.sort()
            mid = len(prices) // 2
            result = round(prices[mid], 2)
            _price_cache[cache_key] = (result, now + _PRICE_CACHE_TTL)
            return result
    except Exception as e:
        logger.warning("eBay last sold price lookup failed for '%s': %s", card_name, e)
        return None


class EbayScraper(BaseScraper):
    platform = "ebay"

    async def scrape(self) -> list[RawListing]:
        if not settings.ebay_app_id or not settings.ebay_client_secret:
            logger.warning("eBay API credentials not configured — skipping eBay scraper")
            return []

        token = await _get_access_token()
        listings: list[RawListing] = []
        seen_ids: set[str] = set()

        async with httpx.AsyncClient(timeout=20) as client:
            for query in SEARCH_QUERIES:
                try:
                    params = {
                        "q": query,
                        "limit": 50,
                        "sort": "newlyListed",
                        "fieldgroups": "EXTENDED",
                    }
                    resp = await client.get(
                        _BROWSE_URL,
                        params=params,
                        headers={
                            "Authorization": f"Bearer {token}",
                            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
                            "Content-Type": "application/json",
                        },
                    )
                    if resp.status_code == 401:
                        # Token expired mid-run, force refresh
                        _token_cache["token"] = None
                        token = await _get_access_token()
                        continue

                    resp.raise_for_status()
                    data = resp.json()

                    for item in data.get("itemSummaries", []):
                        item_id = item.get("itemId")
                        if not item_id or item_id in seen_ids:
                            continue
                        seen_ids.add(item_id)

                        price_obj = item.get("price", {})
                        raw_price = float(price_obj.get("value", 0)) if price_obj else None
                        currency = price_obj.get("currency", "USD")
                        price_val = round(raw_price, 2) if raw_price else None

                        image_urls = []
                        if img := item.get("image", {}).get("imageUrl"):
                            image_urls.append(img)

                        seller = item.get("seller", {})
                        seller_name = seller.get("username", "")
                        seller_feedback_score = seller.get("feedbackScore")
                        seller_feedback_pct = seller.get("feedbackPercentage")
                        if seller_feedback_pct is not None:
                            try:
                                seller_feedback_pct = float(seller_feedback_pct)
                            except (ValueError, TypeError):
                                seller_feedback_pct = None

                        location = item.get("itemLocation", {})
                        location_text = ", ".join(filter(None, [
                            location.get("city"),
                            location.get("stateOrProvince"),
                            location.get("country"),
                        ]))
                        seller_country = location.get("country") or None

                        # Condition
                        condition = item.get("condition") or None

                        # Buying format: AUCTION or FIXED_PRICE
                        buying_options = item.get("buyingOptions", [])
                        if "AUCTION" in buying_options:
                            buying_format = "AUCTION"
                        else:
                            buying_format = "FIXED_PRICE"

                        auction_end_time = item.get("itemEndDate") or None

                        # Shipping cost
                        shipping_cost = None
                        shipping_currency = None
                        shipping_options = item.get("shippingOptions", [])
                        if shipping_options:
                            s = shipping_options[0]
                            sc = s.get("shippingCost", {})
                            if sc:
                                try:
                                    shipping_cost = float(sc.get("value", 0))
                                    shipping_currency = sc.get("currency", "USD")
                                except (ValueError, TypeError):
                                    pass
                        elif item.get("freeShipping"):
                            shipping_cost = 0.0

                        listings.append(RawListing(
                            platform="ebay",
                            external_id=item_id,
                            url=item.get("itemWebUrl", f"https://www.ebay.com/itm/{item_id}"),
                            title=item.get("title", ""),
                            price=price_val,
                            currency=currency,
                            image_urls=image_urls,
                            seller_name=seller_name,
                            seller_contact=f"https://www.ebay.com/usr/{seller_name}" if seller_name else None,
                            location_text=location_text or None,
                            condition=condition,
                            seller_feedback_score=seller_feedback_score,
                            seller_feedback_pct=seller_feedback_pct,
                            shipping_cost=shipping_cost,
                            shipping_currency=shipping_currency,
                            seller_country=seller_country,
                            buying_format=buying_format,
                            auction_end_time=auction_end_time,
                            raw_data=item,
                        ))

                except httpx.HTTPError as e:
                    logger.warning("eBay search error for query '%s': %s", query, e)
                    continue

        logger.info("eBay scraper: found %d listings", len(listings))
        return listings

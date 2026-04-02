"""
TCGPlayer marketplace scraper.
Uses TCGPlayer's internal search API (mp-search-api.tcgplayer.com) — no auth required.
Returns individual seller listings for Pokemon TCG products.
"""
from __future__ import annotations

import logging

import httpx

from .base import BaseScraper, RawListing

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://mp-search-api.tcgplayer.com/v1/search/request"
_PRODUCT_URL = "https://www.tcgplayer.com/product/{product_id}"
_IMAGE_URL = "https://product-images.tcgplayer.com/fit-in/437x437/{product_id}.jpg"
_PAGE_SIZE = 24
_MAX_PAGES = 5  # up to 120 products per query (~4000 total across all queries)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Referer": "https://www.tcgplayer.com/",
    "Origin": "https://www.tcgplayer.com",
}

# Search queries — broad terms to cover all high-value Pokemon TCG cards
SEARCH_QUERIES = [
    "charizard ex",
    "pikachu ex",
    "mewtwo ex",
    "umbreon vmax",
    "rayquaza vmax",
    "lugia vstar",
    "gardevoir ex",
    "miraidon ex",
    "koraidon ex",
    "iron leaves ex",
    "secret rare full art",
    "illustration rare",
    "special illustration rare",
    "hyper rare",
    "rainbow rare",
    "gold card",
    "alt art",
    "151 pokemon",
    "surging sparks",
    "obsidian flames",
    "temporal forces",
    "paldean fates",
    "twilight masquerade",
    "stellar crown",
    "prismatic evolutions",
    "elite trainer box",
    "booster box pokemon",
    "psa 10 pokemon",
    "bgs 9.5 pokemon",
    "cgc 10 pokemon",
    "base set charizard",
    "shadowless pokemon",
]


class TCGPlayerScraper(BaseScraper):
    platform = "tcgplayer"

    async def scrape(self) -> list[RawListing]:
        listings: list[RawListing] = []
        seen_ids: set[str] = set()

        async with httpx.AsyncClient(timeout=20, headers=_HEADERS) as client:
            for query in SEARCH_QUERIES:
                try:
                    page_listings = await self._scrape_query(client, query, seen_ids)
                    listings.extend(page_listings)
                    logger.debug(
                        "TCGPlayer query '%s': %d listings", query, len(page_listings)
                    )
                except Exception as e:
                    logger.warning("TCGPlayer query '%s' failed: %s", query, e)

        logger.info("TCGPlayer scrape total: %d listings", len(listings))
        return listings

    async def _scrape_query(
        self,
        client: httpx.AsyncClient,
        query: str,
        seen_ids: set[str],
    ) -> list[RawListing]:
        listings: list[RawListing] = []

        for page in range(_MAX_PAGES):
            payload = {
                "q": query,
                "inStock": True,
                "productLineName": ["pokemon", "pokemon-japan"],
                "from": page * _PAGE_SIZE,
                "size": _PAGE_SIZE,
            }

            try:
                resp = await client.post(_SEARCH_URL, json=payload)
                if resp.status_code != 200:
                    break
                data = resp.json()
            except Exception as e:
                logger.warning("TCGPlayer fetch failed (query=%s page=%d): %s", query, page, e)
                break

            results = data.get("results", [{}])[0].get("results", [])
            if not results:
                break

            for product in results:
                product_id = product.get("productId")
                product_name = product.get("productName", "").strip()
                set_name = product.get("setName", "").strip()
                market_price = product.get("marketPrice")
                image_url = _IMAGE_URL.format(product_id=int(product_id)) if product_id else None
                product_url = _PRODUCT_URL.format(product_id=int(product_id)) if product_id else None
                sealed = product.get("sealed", False)

                for seller_listing in product.get("listings", []):
                    listing_id = seller_listing.get("listingId")
                    seller_key = seller_listing.get("sellerKey", "")
                    condition_id = seller_listing.get("conditionId", 0)
                    condition = seller_listing.get("condition", "")
                    price = seller_listing.get("price")
                    seller_name = seller_listing.get("sellerName", "")
                    seller_rating = seller_listing.get("sellerRating")
                    shipping_price = seller_listing.get("shippingPrice", 0)
                    quantity = seller_listing.get("quantity", 1)
                    printing = seller_listing.get("printing", "")

                    if not listing_id or price is None:
                        continue

                    external_id = str(int(listing_id))
                    if external_id in seen_ids:
                        continue
                    seen_ids.add(external_id)

                    # Build descriptive title for keyword matching
                    title_parts = [product_name]
                    if set_name:
                        title_parts.append(f"[{set_name}]")
                    if printing and printing != "Holofoil":
                        title_parts.append(printing)
                    if condition:
                        title_parts.append(f"- {condition}")
                    title = " ".join(title_parts)

                    listings.append(RawListing(
                        platform="tcgplayer",
                        external_id=external_id,
                        url=product_url or "",
                        title=title,
                        description=None,
                        price=float(price),
                        currency="USD",
                        image_urls=[image_url] if image_url else [],
                        seller_name=seller_name,
                        seller_contact=None,
                        location_text="US",
                        buying_format="FIXED_PRICE",
                        auction_end_time=None,
                        condition=condition,
                        seller_feedback_score=None,
                        seller_feedback_pct=float(seller_rating) if seller_rating else None,
                        shipping_cost=float(shipping_price) if shipping_price else 0.0,
                        shipping_currency="USD",
                        seller_country="US",
                        raw_data={
                            "productId": product_id,
                            "productName": product_name,
                            "setName": set_name,
                            "marketPrice": market_price,
                            "condition": condition,
                            "conditionId": condition_id,
                            "printing": printing,
                            "sellerKey": seller_key,
                            "quantity": quantity,
                            "sealed": sealed,
                        },
                    ))

            total_results = data.get("results", [{}])[0].get("totalResults", 0)
            if (page + 1) * _PAGE_SIZE >= total_results:
                break

        return listings

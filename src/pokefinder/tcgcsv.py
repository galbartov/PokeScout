"""
TCGcsv client — free TCGPlayer price data, updated daily ~20:00 UTC.
https://tcgcsv.com/docs

Category IDs:
  3  = Pokemon (English)
  85 = Pokemon (Japanese)
"""
from __future__ import annotations

import logging
import time

import httpx

logger = logging.getLogger(__name__)

_BASE = "https://tcgcsv.com/tcgplayer"

CATEGORY_EN = 3
CATEGORY_JP = 85

USD_TO_ILS = 3.12

# Cache: { cache_key: (expires_at, data) }
_cache: dict[str, tuple[float, object]] = {}
_TTL = 3600 * 6  # 6 hours


async def _get(url: str) -> dict:
    now = time.monotonic()
    if url in _cache:
        expires, data = _cache[url]
        if now < expires:
            return data
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
    _cache[url] = (now + _TTL, data)
    return data


async def get_prices_for_group(category_id: int, group_id: int) -> dict[int, dict]:
    """
    Returns dict of productId → price row.
    Price row keys: lowPrice, midPrice, highPrice, marketPrice, subTypeName.
    """
    url = f"{_BASE}/{category_id}/{group_id}/prices"
    data = await _get(url)
    result: dict[int, dict] = {}
    for row in data.get("results", []):
        pid = row.get("productId")
        if pid:
            result[pid] = row
    return result


async def get_market_price_ils(category_id: int, group_id: int, product_id: int) -> float | None:
    """
    Returns the marketPrice in ILS for a specific product, or None if not found.
    Converts USD → ILS using USD_TO_ILS rate.
    """
    prices = await get_prices_for_group(category_id, group_id)
    row = prices.get(product_id)
    if not row:
        return None
    usd = row.get("marketPrice")
    if usd is None:
        usd = row.get("midPrice")
    if usd is None:
        return None
    return round(float(usd) * USD_TO_ILS, 2)

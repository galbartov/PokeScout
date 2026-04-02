"""
Three-signal deduplication:
1. Exact external_id match (handled at DB level with UNIQUE index)
2. Perceptual image hash (hamming distance < 5 within last 7 days)
3. Normalized title similarity > 85% AND price within 5%
"""
from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


def _hamming_distance(h1: str, h2: str) -> int:
    """Compute hamming distance between two hex hash strings."""
    try:
        return bin(int(h1, 16) ^ int(h2, 16)).count("1")
    except (ValueError, TypeError):
        return 999


async def compute_image_hash(image_url: str) -> str | None:
    """Download image and compute perceptual hash. Returns hex string or None."""
    try:
        import imagehash
        from PIL import Image
        import io

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(image_url, follow_redirects=True)
            resp.raise_for_status()

        img = Image.open(io.BytesIO(resp.content))
        return str(imagehash.phash(img))
    except Exception as e:
        logger.debug("Image hash failed for %s: %s", image_url, e)
        return None


def is_image_duplicate(new_hash: str, existing_hashes: list[str], threshold: int = 5) -> bool:
    """Return True if new_hash is within threshold of any existing hash."""
    for existing in existing_hashes:
        if _hamming_distance(new_hash, existing) <= threshold:
            return True
    return False


def is_title_price_duplicate(
    new_title: str,
    new_price: float | None,
    existing_records: list[dict],  # list of {"title_normalized": str, "price": float}
    title_threshold: float = 85.0,
    price_pct: float = 0.05,
) -> bool:
    """
    Return True if a record with similar title AND close price already exists.
    """
    from rapidfuzz import fuzz

    for rec in existing_records:
        title_score = fuzz.token_sort_ratio(new_title, rec.get("title_normalized", ""))
        if title_score < title_threshold:
            continue

        # Titles match — now check price
        existing_price = rec.get("price")
        if new_price is None or existing_price is None:
            return True  # Can't compare prices, treat as duplicate on title alone
        price_diff = abs(new_price - float(existing_price))
        if existing_price > 0 and price_diff / float(existing_price) <= price_pct:
            return True

    return False

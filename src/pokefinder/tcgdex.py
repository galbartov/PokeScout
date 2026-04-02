"""
TCGDex API client (https://tcgdex.dev/).
Free, no auth required. All prices are in EUR/USD from Cardmarket/TCGPlayer.
We use it only for card metadata + images.
"""
from __future__ import annotations

import logging
from functools import lru_cache

import httpx

logger = logging.getLogger(__name__)

_BASE = "https://api.tcgdex.net/v2/en"
_IMG_BASE = "https://assets.tcgdex.net/en"

# Simple in-process cache — series/sets rarely change
_series_cache: list[dict] | None = None
_sets_by_series: dict[str, list[dict]] = {}
_set_cache: dict[str, dict] = {}  # set_id → full set with cards[]


async def get_series() -> list[dict]:
    """Return all series, newest first."""
    global _series_cache
    if _series_cache is not None:
        return _series_cache
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{_BASE}/series")
        resp.raise_for_status()
        data = resp.json()
    # Exclude Pokémon TCG Pocket (digital-only, not relevant for physical card trading)
    # Reverse so newest (Scarlet & Violet) comes first
    _series_cache = list(reversed([s for s in data if s["id"] != "tcgp"]))
    return _series_cache


async def get_sets_for_series(series_id: str) -> list[dict]:
    """Return sets belonging to a series, newest first."""
    if series_id in _sets_by_series:
        return _sets_by_series[series_id]
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{_BASE}/series/{series_id}")
        resp.raise_for_status()
        data = resp.json()
    sets = list(reversed(data.get("sets", [])))
    _sets_by_series[series_id] = sets
    return sets


async def get_set(set_id: str) -> dict:
    """Return full set object including cards[]."""
    if set_id in _set_cache:
        return _set_cache[set_id]
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{_BASE}/sets/{set_id}")
        resp.raise_for_status()
        data = resp.json()
    _set_cache[set_id] = data
    return data


async def get_card(card_id: str) -> dict | None:
    """Return full card detail."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{_BASE}/cards/{card_id}")
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning("TCGDex card fetch failed for %s: %s", card_id, e)
        return None


def card_image_url(card: dict, quality: str = "high") -> str | None:
    """
    Build the card image URL.
    quality: "high" (webp, large) or "low" (webp, small)
    Returns None if the card has no image field.
    """
    image = card.get("image")
    if not image:
        return None
    return f"{image}/{quality}.webp"


EUR_TO_ILS = 3.85  # approximate, update periodically


def get_cardmarket_price_ils(card: dict) -> float | None:
    """
    Extract the Cardmarket trend price from a card detail object and convert to ILS.
    Returns None if pricing data is unavailable.
    """
    try:
        pricing = card.get("pricing") or {}
        cm = pricing.get("cardmarket") or {}
        eur = cm.get("trend") or cm.get("avg30") or cm.get("avg")
        if eur and float(eur) > 0:
            return round(float(eur) * EUR_TO_ILS)
        return None
    except Exception:
        return None


def format_card_caption(card: dict, locale: str = "he") -> str:
    """Build the caption shown under a card photo."""
    name = card.get("name", "?")
    set_info = card.get("set", {})
    set_name = set_info.get("name", "")
    local_id = card.get("localId", "")
    hp = card.get("hp")
    types = card.get("types") or []
    rarity = card.get("rarity", "")

    type_str = " / ".join(types) if types else ""
    hp_str = f"❤️ {hp} HP" if hp else ""

    lines = [f"*{name}*  #{local_id}"]
    if set_name:
        lines.append(f"📦 {set_name}")
    if type_str or hp_str:
        lines.append("  ".join(filter(None, [type_str, hp_str])))
    if rarity:
        lines.append(f"✨ {rarity}")

    return "\n".join(lines)

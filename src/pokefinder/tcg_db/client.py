"""pokemontcg.io API client for card lookups."""
from __future__ import annotations

import httpx

from pokefinder.config import settings

_BASE_URL = "https://api.pokemontcg.io/v2"


def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if settings.pokemontcg_api_key:
        h["X-Api-Key"] = settings.pokemontcg_api_key
    return h


async def search_cards(query: str, page_size: int = 10) -> list[dict]:
    """
    Search pokemontcg.io for cards matching a query string.
    Returns a list of simplified card dicts.
    """
    params = {
        "q": f'name:"{query}*"',
        "pageSize": page_size,
        "orderBy": "-set.releaseDate",
        "select": "id,name,set,number,rarity,images",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{_BASE_URL}/cards", params=params, headers=_headers())
        resp.raise_for_status()
        data = resp.json()

    cards = []
    for card in data.get("data", []):
        cards.append({
            "id": card["id"],
            "name": card["name"],
            "set_name": card.get("set", {}).get("name", ""),
            "set_id": card.get("set", {}).get("id", ""),
            "number": card.get("number", ""),
            "rarity": card.get("rarity", ""),
            "image_url": card.get("images", {}).get("small", ""),
            "product_type": "card",
        })
    return cards


async def get_card(card_id: str) -> dict | None:
    """Fetch a single card by its pokemontcg.io ID."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{_BASE_URL}/cards/{card_id}", headers=_headers())
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json().get("data")

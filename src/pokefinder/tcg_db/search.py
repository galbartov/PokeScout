"""
Fuzzy search across both pokemontcg.io cards and our curated sealed products list.
Used during bot onboarding so users can type a product name (in Hebrew or English)
and we return ranked matches for them to confirm.
"""
from __future__ import annotations

from rapidfuzz import fuzz, process

from .client import search_cards
from .sealed_products import SEALED_PRODUCTS, local_image_path


def _normalize(text: str) -> str:
    return text.lower().strip()


def _sealed_search(query: str, limit: int = 5) -> list[dict]:
    """Fuzzy-search the local sealed products list."""
    norm_query = _normalize(query)

    candidates: list[tuple[str, dict]] = []
    for product in SEALED_PRODUCTS:
        search_strings = [
            _normalize(product["en"]),
            _normalize(product.get("he", "")),
            *[_normalize(a) for a in product.get("aliases", [])],
        ]
        best_score = max(
            fuzz.token_set_ratio(norm_query, s) for s in search_strings if s
        )
        candidates.append((best_score, product))

    candidates.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, product in candidates[:limit]:
        if score >= 50:
            results.append({
                "id": product["id"],
                "name_en": product["en"],
                "name_he": product.get("he", ""),
                "set_name": product.get("set", ""),
                "product_type": "sealed",
                "score": score,
                "display": f"{product['en']} ({product.get('set', '')})",
                "local_image_path": local_image_path(product),
            })
    return results


async def search_products(query: str, limit: int = 5) -> list[dict]:
    """
    Search for Pokemon TCG products matching a query.
    Returns up to `limit` results combining sealed products and cards,
    sorted by relevance score (sealed products ranked first if they score well).
    """
    # Search sealed products (local, instant)
    sealed_results = _sealed_search(query, limit=limit)

    # Search cards via API
    card_results: list[dict] = []
    try:
        cards = await search_cards(query, page_size=limit)
        for card in cards:
            display_name = f"{card['name']} — {card['set_name']}"
            card_results.append({
                "id": card["id"],
                "name_en": card["name"],
                "name_he": "",
                "set_name": card["set_name"],
                "number": card.get("number", ""),
                "product_type": "card",
                "score": 70,  # API already ranked by relevance
                "display": display_name,
                "image_url": card.get("image_url", ""),
            })
    except Exception:
        pass  # API unavailable — fall back to sealed results only

    # Merge: sealed first if score >= 70, then cards
    high_sealed = [r for r in sealed_results if r["score"] >= 70]
    low_sealed = [r for r in sealed_results if r["score"] < 70]

    merged = high_sealed + card_results + low_sealed
    # Deduplicate by id, preserve order
    seen: set[str] = set()
    unique = []
    for r in merged:
        if r["id"] not in seen:
            seen.add(r["id"])
            unique.append(r)

    return unique[:limit]


def card_keywords(result: dict) -> list[str]:
    """
    Build a precise keyword list for a card result.
    e.g. ["charizard ex sir", "199/165", "199", "151"] for Charizard ex SIR 199/165 from 151.
    Covers how sellers typically title eBay listings.
    """
    name = result.get("name_en", "").strip()
    set_name = result.get("set_name", "").strip()
    number = result.get("number", "").strip()

    keywords = []
    if name:
        keywords.append(name.lower())
    if number:
        keywords.append(number)                  # "199/165"
        keywords.append(number.split("/")[0])    # "199" (just the card number)
    if set_name:
        keywords.append(set_name.lower())        # "151"
    return [k for k in keywords if k]


def format_search_results(results: list[dict], locale: str = "he") -> str:
    """Format search results as a numbered list for display in bot messages."""
    lines = []
    for i, r in enumerate(results, 1):
        type_emoji = "📦" if r["product_type"] == "sealed" else "🃏"
        name = r["name_he"] if locale == "he" and r.get("name_he") else r["name_en"]
        if r.get("set_name"):
            lines.append(f"{i}. {type_emoji} {name} — {r['set_name']}")
        else:
            lines.append(f"{i}. {type_emoji} {name}")
    return "\n".join(lines)

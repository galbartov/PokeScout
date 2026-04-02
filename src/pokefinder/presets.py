"""
Curated preference presets for the Israeli Pokemon TCG market.

Card presets use live prices from TCGcsv (TCGPlayer marketPrice USD, converted to ILS,
discounted 15% for "good deal" threshold).
Sealed presets use hardcoded ILS prices (no free API available).
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

DEAL_DISCOUNT = 0.85  # 15% below market = good deal threshold

PRESETS: list[dict] = [
    # ── Sealed (hardcoded ILS prices) ────────────────────────────────────────
    {
        "id": "pe_etb",
        "name_he": "Prismatic Evolutions ETB",
        "name_en": "Prismatic Evolutions ETB",
        "categories": ["sealed"],
        "keywords": ["prismatic evolutions", "etb"],
        "price_max": 180,
        "tcgdex_card_id": None,
    },
    {
        "id": "pf_etb",
        "name_he": "Paldean Fates ETB",
        "name_en": "Paldean Fates ETB",
        "categories": ["sealed"],
        "keywords": ["paldean fates", "etb"],
        "price_max": 700,
        "tcgdex_card_id": None,
    },
    {
        "id": "ss_etb",
        "name_he": "Surging Sparks ETB",
        "name_en": "Surging Sparks ETB",
        "categories": ["sealed"],
        "keywords": ["surging sparks", "etb"],
        "price_max": 720,
        "tcgdex_card_id": None,
    },
    {
        "id": "jt_etb",
        "name_he": "Journey Together ETB",
        "name_en": "Journey Together ETB",
        "categories": ["sealed"],
        "keywords": ["journey together", "etb"],
        "price_max": 400,
        "tcgdex_card_id": None,
    },
    {
        "id": "151_bb",
        "name_he": "SV 151 Booster Box",
        "name_en": "SV 151 Booster Box",
        "categories": ["sealed"],
        "keywords": ["151", "booster box"],
        "price_max": 1200,
        "tcgdex_card_id": None,
    },
    # ── Singles (live price from TCGcsv / TCGPlayer) ──────────────────────────
    {
        "id": "char_ex",
        "name_he": "Charizard ex 151 SIR",
        "name_en": "Charizard ex 151 SIR",
        "categories": ["singles"],
        "keywords": ["charizard ex", "151"],
        "price_max": None,
        "tcgcsv_category": 3, "tcgcsv_group": 23237, "tcgcsv_product": 517045,  # 199/165 SIR
    },
    {
        "id": "umbrv_aa",
        "name_he": "Umbreon VMAX Alt Art",
        "name_en": "Umbreon VMAX Alt Art",
        "categories": ["singles"],
        "keywords": ["umbreon vmax", "alt art", "215"],
        "price_max": None,
        "tcgcsv_category": 3, "tcgcsv_group": 2848, "tcgcsv_product": 246723,  # 215/203 Alt Art
    },
    {
        "id": "pika_151",
        "name_he": "Pikachu 151 IR",
        "name_en": "Pikachu 151 IR",
        "categories": ["singles"],
        "keywords": ["pikachu", "151"],
        "price_max": None,
        "tcgcsv_category": 3, "tcgcsv_group": 23237, "tcgcsv_product": 513721,  # 173/165 IR
    },
    # ── Graded (live price from TCGcsv / TCGPlayer) ───────────────────────────
    {
        "id": "char_psa10",
        "name_he": "Charizard ex 151 PSA/CGC 10",
        "name_en": "Charizard ex 151 PSA/CGC 10",
        "categories": ["graded"],
        "keywords": ["charizard ex", "151"],
        "price_max": None,
        "tcgcsv_category": 3, "tcgcsv_group": 23237, "tcgcsv_product": 517045,  # 199/165 SIR
    },
    {
        "id": "char_base",
        "name_he": "Charizard Base Set מדורג",
        "name_en": "Charizard Base Set Graded",
        "categories": ["graded", "singles"],
        "keywords": ["charizard", "base set"],
        "price_max": None,
        "tcgcsv_category": 3, "tcgcsv_group": 604, "tcgcsv_product": 42382,  # Base Set Holo
    },
]

_BY_ID: dict[str, dict] = {p["id"]: p for p in PRESETS}


def get_preset(preset_id: str) -> dict | None:
    return _BY_ID.get(preset_id)


def get_presets_for_categories(categories: set | list) -> list[dict]:
    """Return presets whose category list intersects the user's selected categories."""
    cat_set = set(categories)
    return [p for p in PRESETS if cat_set.intersection(p["categories"])]


async def resolve_price(preset: dict) -> float | None:
    """
    Return price_max in ILS.
    Sealed presets: return hardcoded value.
    Card presets: fetch live TCGPlayer marketPrice from TCGcsv, convert USD→ILS, apply 15% discount.
    """
    if preset["price_max"] is not None:
        return float(preset["price_max"])

    category = preset.get("tcgcsv_category")
    group = preset.get("tcgcsv_group")
    product = preset.get("tcgcsv_product")
    if not (category and group and product):
        return None

    try:
        from pokefinder.tcgcsv import get_market_price_ils
        price_ils = await get_market_price_ils(category, group, product)
        if price_ils and price_ils > 0:
            return round(price_ils * DEAL_DISCOUNT)
        return None
    except Exception as e:
        logger.warning("Failed to resolve price for preset %s: %s", preset["id"], e)
        return None


async def resolve_prices_for_categories(
    categories: set | list,
) -> list[tuple[dict, float | None]]:
    """Return list of (preset, price_max_ils) for all presets matching the given categories."""
    matching = get_presets_for_categories(categories)
    results = []
    for preset in matching:
        price = await resolve_price(preset)
        results.append((preset, price))
    return results

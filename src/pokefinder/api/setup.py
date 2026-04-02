"""
FastAPI router for the web setup page (/setup).

Endpoints:
  GET  /api/setup/products?q=...&type=...   — search products for the web UI
  GET  /api/setup/price?name=...            — eBay market price for a product
  POST /api/setup/token                     — generate a setup token (bot calls this)
  POST /api/setup/confirm                   — validate token + bulk-save preferences
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pokefinder.db import get_client
from pokefinder.db import queries as q

router = APIRouter(prefix="/api/setup", tags=["setup"])


# ── GET /api/setup/products ───────────────────────────────────────────────────

@router.get("/products")
async def search_products_endpoint(
    q: str = "",
    type: str = "",
    limit: int = 10,
) -> list[dict]:
    """Search for TCG products. Used by the web setup page search bar."""
    from pokefinder.tcg_db.search import search_products as _search

    results = await _search(q or "", limit=limit)
    if type:
        results = [r for r in results if r.get("product_type") == type]
    # Remove local_image_path — not useful to the browser
    for r in results:
        r.pop("local_image_path", None)
    return results


# ── GET /api/setup/popular ───────────────────────────────────────────────────

# Curated popular items with known pokemontcg.io card IDs for reliable images
_POPULAR: list[dict] = [
    # Singles
    {"id": "sv3pt5-199",  "name_en": "Charizard ex SIR",       "set_name": "151",                "product_type": "card",   "keywords": ["charizard ex", "sir", "151"]},
    {"id": "swsh7-215",   "name_en": "Umbreon VMAX Rainbow",   "set_name": "Evolving Skies",     "product_type": "card",   "keywords": ["umbreon vmax", "evolving skies"]},
    {"id": "sv8-238",     "name_en": "Pikachu ex SIR",         "set_name": "Surging Sparks",     "product_type": "card",   "keywords": ["pikachu ex", "sir", "surging sparks"]},
    {"id": "swsh9-174",   "name_en": "Charizard VSTAR Rainbow","set_name": "Brilliant Stars",    "product_type": "card",   "keywords": ["charizard vstar", "brilliant stars"]},
    {"id": "swsh8-268",   "name_en": "Mew VMAX Rainbow",       "set_name": "Fusion Strike",      "product_type": "card",   "keywords": ["mew vmax", "fusion strike"]},
    # Sealed
    {"id": "sv-pe-etb",   "name_en": "Prismatic Evolutions ETB", "set_name": "Prismatic Evolutions", "product_type": "sealed", "keywords": ["prismatic evolutions", "etb"]},
    {"id": "sv-ss-etb",   "name_en": "Surging Sparks ETB",     "set_name": "Surging Sparks",     "product_type": "sealed", "keywords": ["surging sparks", "etb"]},
    {"id": "sv-jt-etb",   "name_en": "Journey Together ETB",   "set_name": "Journey Together",   "product_type": "sealed", "keywords": ["journey together", "etb"]},
    {"id": "sv-151-bb",   "name_en": "SV 151 Booster Box",     "set_name": "SV 151",             "product_type": "sealed", "keywords": ["151", "booster box"]},
    {"id": "sv-obf-bb",   "name_en": "Obsidian Flames Booster Box", "set_name": "Obsidian Flames", "product_type": "sealed", "keywords": ["obsidian flames", "booster box"]},
]

_popular_cache: list | None = None


async def _build_popular() -> list[dict]:
    """Enrich popular items with images and market prices (cached after first call)."""
    global _popular_cache
    if _popular_cache is not None:
        return _popular_cache

    from pokefinder.tcg_db.client import get_card
    from pokefinder.tcg_db.sealed_products import SEALED_PRODUCTS, local_image_path
    import asyncio

    # Build sealed image map from local files → serve as relative URL path
    sealed_map: dict[str, str] = {}
    for p in SEALED_PRODUCTS:
        lp = local_image_path(p)
        if lp:
            # Extract just the /sealed/xxx.jpg portion for the web
            import os
            fname = os.path.basename(lp)
            sealed_map[p["id"]] = f"/sealed/{fname}"
        # Also index by keyword fragments for fuzzy matching
        for kw in p.get("aliases", [p["en"].lower()]):
            sealed_map[kw.lower()] = sealed_map.get(p["id"], "")

    enriched = []
    for item in _POPULAR:
        result = dict(item)

        if item["product_type"] == "card":
            # Fetch card image from pokemontcg.io
            try:
                card = await get_card(item["id"])
                if card:
                    result["image_url"] = card.get("images", {}).get("large") or card.get("images", {}).get("small", "")
                else:
                    result["image_url"] = ""
            except Exception:
                result["image_url"] = ""
        else:
            # Match sealed product by keyword search
            from pokefinder.tcg_db.search import search_products as _search
            try:
                hits = await _search(item["name_en"], limit=1)
                if hits:
                    # Convert local_image_path to a web-accessible URL
                    lp = hits[0].get("local_image_path", "")
                    if lp:
                        import os
                        result["image_url"] = f"/sealed/{os.path.basename(lp)}"
                    else:
                        result["image_url"] = ""
                else:
                    result["image_url"] = ""
            except Exception:
                result["image_url"] = ""

        result.pop("keywords", None)
        enriched.append(result)

    _popular_cache = enriched
    return enriched


@router.get("/popular")
async def get_popular() -> list[dict]:
    """Return curated popular items with images for the setup page default view."""
    return await _build_popular()


# ── GET /api/setup/price ──────────────────────────────────────────────────────

@router.get("/price")
async def get_market_price(name: str) -> dict:
    """Return eBay last-sold price for a product name (cached 1h)."""
    from pokefinder.scrapers.ebay import get_last_sold_price
    price = await get_last_sold_price(name)
    return {"name": name, "price": price}


# ── POST /api/setup/token ─────────────────────────────────────────────────────

class TokenRequest(BaseModel):
    user_id: str


@router.post("/token")
async def create_token(body: TokenRequest) -> dict:
    """Generate a 15-min setup token. Called by the bot's /setup command."""
    db = await get_client()
    token = await q.create_setup_token(db, body.user_id)
    return {"token": token}


# ── POST /api/setup/confirm ───────────────────────────────────────────────────

class AlertItem(BaseModel):
    product_id: str | None = None
    name: str
    product_type: str = "card"   # "card" | "sealed" | "keyword"
    price_min: float | None = None
    price_max: float | None = None
    keywords: list[str] = []


class ConfirmRequest(BaseModel):
    token: str
    alerts: list[AlertItem]


@router.post("/confirm")
async def confirm_setup(body: ConfirmRequest) -> dict:
    """
    Validate token + bulk-save preferences.
    Sends a Telegram confirmation message to the user after saving.
    """
    db = await get_client()
    token_row = await q.get_setup_token(db, body.token)

    if not token_row:
        raise HTTPException(status_code=404, detail="Token not found")

    if token_row["used"]:
        raise HTTPException(status_code=410, detail="Token already used")

    expires_at = datetime.fromisoformat(token_row["expires_at"].replace("Z", "+00:00"))
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Token expired")

    user_id = token_row["user_id"]
    from pokefinder.bots.service import BotService
    svc = BotService(db)

    # Load user for cap check
    res = await db.table("users").select("*").eq("id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="User not found")
    user = res.data[0]

    saved = 0
    skipped = 0
    for alert in body.alerts:
        allowed, _, limit = await svc.can_add_preference(user)
        if not allowed:
            skipped += 1
            continue

        if alert.product_type == "keyword":
            categories = ["singles", "sealed", "graded", "bulk"]
            keywords = alert.keywords or [alert.name.lower()]
        elif alert.product_type == "sealed":
            categories = ["sealed"]
            keywords = alert.keywords or [alert.name.lower()]
        else:
            categories = ["singles"]
            keywords = alert.keywords or [alert.name.lower()]

        pref_data: dict[str, Any] = {
            "name": alert.name,
            "categories": categories,
            "keywords": keywords,
            "tcg_product_id": alert.product_id,
            "price_min": alert.price_min,
            "price_max": alert.price_max,
            "radius_km": None,
        }

        duplicate = await svc.find_duplicate_preference(user_id, pref_data)
        if duplicate:
            skipped += 1
            continue

        await svc.add_preference(user_id, pref_data)
        saved += 1

        # Refresh user for next cap check
        res2 = await db.table("users").select("*").eq("id", user_id).execute()
        if res2.data:
            user = res2.data[0]

    # Mark token as used
    await q.mark_token_used(db, body.token)

    # Notify user on Telegram
    try:
        from pokefinder.i18n import t
        from pokefinder.config import settings
        from telegram import Bot
        bot = Bot(token=settings.telegram_bot_token)
        tg_id = user.get("telegram_id")
        if tg_id and saved > 0:
            await bot.send_message(
                chat_id=tg_id,
                text=t("setup_confirmed", "en", count=saved),
            )
    except Exception:
        pass  # Don't fail the response if Telegram notify fails

    return {"saved": saved, "skipped": skipped}

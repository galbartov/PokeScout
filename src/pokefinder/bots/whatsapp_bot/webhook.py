"""
WhatsApp bot via Twilio webhook.
Conversational state machine stored in memory (per phone number).
State persists for 30 minutes after last message.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, Form, Request, Response
from twilio.rest import Client as TwilioClient
from twilio.twiml.messaging_response import MessagingResponse

from pokefinder.bots.service import BotService
from pokefinder.config import settings
from pokefinder.db import get_client
from pokefinder.i18n import t
from pokefinder.tcg_db import format_search_results, search_products

logger = logging.getLogger(__name__)
router = APIRouter()

# ── In-memory conversation state ──────────────────────────────────────────────
# { phone: {"state": str, "data": dict, "locale": str, "last_seen": float} }
_sessions: dict[str, dict] = {}
_SESSION_TTL = 1800  # 30 minutes


def _get_session(phone: str) -> dict:
    now = time.time()
    sess = _sessions.get(phone)
    if sess and now - sess["last_seen"] < _SESSION_TTL:
        sess["last_seen"] = now
        return sess
    # New session
    _sessions[phone] = {"state": "idle", "data": {}, "locale": "he", "last_seen": now}
    return _sessions[phone]


def _send(to: str, body: str, media_url: str | None = None) -> None:
    if not settings.twilio_account_sid:
        logger.warning("Twilio not configured — skipping WA message to %s", to)
        return
    client = TwilioClient(settings.twilio_account_sid, settings.twilio_auth_token)
    kwargs: dict[str, Any] = {
        "from_": settings.twilio_whatsapp_from,
        "to": f"whatsapp:{to}",
        "body": body,
    }
    if media_url:
        kwargs["media_url"] = [media_url]
    client.messages.create(**kwargs)


# ── State machine ─────────────────────────────────────────────────────────────

STATES = [
    "idle",
    "await_language",
    "await_categories",
    "await_product_search",
    "await_product_choice",
    "await_keywords",
    "await_price",
    "await_price_min",
    "await_price_max",
    "await_location",
    "await_radius",
    "await_name",
]

CATEGORY_KEYWORDS = {
    "1": "sealed", "sealed": "sealed", "מוצרים סגורים": "sealed",
    "2": "singles", "singles": "singles", "קלפים בודדים": "singles",
    "3": "graded", "graded": "graded", "קלפים מדורגים": "graded",
    "4": "bulk", "bulk": "bulk", "לוטים": "bulk", "באלק": "bulk",
}

RADIUS_KEYWORDS = {
    "1": 10, "10": 10,
    "2": 25, "25": 25,
    "3": 50, "50": 50,
    "4": 0, "0": 0, "כל הארץ": 0, "country": 0,
}


async def _handle_message(phone: str, text: str, display_name: str | None) -> str:
    """Process inbound message and return reply text."""
    sess = _get_session(phone)
    state = sess["state"]
    locale = sess["locale"]
    data = sess["data"]
    text_lower = text.strip().lower()

    db = await get_client()
    svc = BotService(db)
    user = await svc.get_or_create_whatsapp_user(phone, display_name)

    # ── Global commands (work from any state) ──────────────────────────────
    if text_lower in ("status", "סטטוס"):
        pref_count = await svc.count_active_preferences(user["id"])
        sess["state"] = "idle"
        return svc.format_status_message(user, pref_count, locale)

    if text_lower in ("subscribe", "מנוי"):
        if svc.is_subscribed(user):
            return t("already_subscribed", locale, expires=user.get("subscription_expires_at", ""))
        url = await svc.generate_checkout_url(user, locale)
        return t("subscribe_prompt", locale, price=BotService.SUBSCRIPTION_PRICE_ILS, checkout_url=url)

    if text_lower in ("help", "עזרה"):
        return t("help_text", locale)

    if text_lower in ("היי", "hi", "hello", "start", "התחל", "/start"):
        sess["state"] = "await_language"
        sess["data"] = {}
        return t("welcome", locale) + "\n\n" + t("choose_language", locale) + "\n1. 🇮🇱 עברית\n2. 🇬🇧 English"

    if text_lower in ("preferences", "העדפות"):
        prefs = await svc.get_preferences(user["id"])
        return svc.format_preferences_list(prefs, locale)

    if text_lower in ("add", "הוסף"):
        sess["state"] = "await_categories"
        sess["data"] = {}
        return t("choose_categories", locale) + "\n1. 📦 " + t("category_sealed", locale) + "\n2. 🃏 " + t("category_singles", locale) + "\n3. ⭐ " + t("category_graded", locale) + "\n4. 📚 " + t("category_bulk", locale) + "\n\nשלח מספרים (לדוגמה: 1,3) | Send numbers (e.g. 1,3)"

    # ── State machine ──────────────────────────────────────────────────────

    if state == "await_language":
        if text_lower in ("1", "עברית", "he", "hebrew"):
            locale = "he"
        elif text_lower in ("2", "english", "en"):
            locale = "en"
        else:
            return t("choose_language", locale) + "\n1. עברית\n2. English"
        sess["locale"] = locale
        await svc.set_locale(user["id"], locale)
        sess["state"] = "await_categories"
        return t("language_set", locale) + "\n\n" + t("choose_categories", locale) + "\n1. " + t("category_sealed", locale) + "\n2. " + t("category_singles", locale) + "\n3. " + t("category_graded", locale) + "\n4. " + t("category_bulk", locale) + "\n\n" + ("שלח מספרים (1,3) או שמות | Send numbers or names" if locale == "he" else "Send numbers (1,3) or category names")

    if state == "await_categories":
        selected = set()
        for part in text.replace("،", ",").split(","):
            key = part.strip().lower()
            if key in CATEGORY_KEYWORDS:
                selected.add(CATEGORY_KEYWORDS[key])
        if not selected:
            return ("בחר לפחות קטגוריה אחת (1-4)" if locale == "he" else "Select at least one category (1-4)")
        data["categories"] = list(selected)
        sess["state"] = "await_product_search"
        return t("enter_product_search", locale)

    if state == "await_product_search":
        if text_lower in ("skip", "דלג", "/skip"):
            data["tcg_product_id"] = None
            data["tcg_product_name"] = None
            sess["state"] = "await_keywords"
            return t("product_search_skipped", locale) + "\n\n" + t("enter_keywords", locale)

        results = await search_products(text, limit=5)
        if not results:
            return t("product_not_found", locale)

        data["_search_results"] = results
        formatted = format_search_results(results, locale)
        sess["state"] = "await_product_choice"
        return t("product_search_results", locale, results=formatted)

    if state == "await_product_choice":
        if text_lower in ("skip", "דלג", "/skip", "לא מצאתי"):
            data["tcg_product_id"] = None
            data["tcg_product_name"] = None
            sess["state"] = "await_keywords"
            return t("product_search_skipped", locale) + "\n\n" + t("enter_keywords", locale)

        try:
            idx = int(text.strip()) - 1
            results = data.get("_search_results", [])
            product = results[idx]
            data["tcg_product_id"] = product["id"]
            data["tcg_product_name"] = product.get("name_he") if locale == "he" and product.get("name_he") else product["name_en"]
            sess["state"] = "await_keywords"
            return t("product_selected", locale, name=data["tcg_product_name"]) + "\n\n" + t("enter_keywords", locale)
        except (ValueError, IndexError):
            return t("product_not_found", locale)

    if state == "await_keywords":
        if text_lower in ("skip", "דלג"):
            data["keywords"] = []
        else:
            data["keywords"] = [k.strip() for k in text.split(",") if k.strip()]
        sess["state"] = "await_price"
        return t("enter_price_range", locale) + "\n1. " + t("price_up_to_100", locale) + "\n2. " + t("price_up_to_250", locale) + "\n3. " + t("price_up_to_500", locale) + "\n4. " + t("price_up_to_1000", locale) + "\n5. " + t("price_any", locale) + "\n6. " + t("price_custom", locale)

    if state == "await_price":
        price_map = {"1": (0, 100), "2": (0, 250), "3": (0, 500), "4": (0, 1000), "5": (None, None)}
        if text_lower in price_map:
            mn, mx = price_map[text_lower]
            data["price_min"] = mn
            data["price_max"] = mx
            sess["state"] = "await_location"
            return t("enter_location", locale)
        elif text_lower == "6":
            sess["state"] = "await_price_min"
            return t("enter_price_min", locale)
        return t("enter_price_range", locale) + " (1-6)"

    if state == "await_price_min":
        try:
            data["price_min"] = float(text.strip()) or None
            sess["state"] = "await_price_max"
            return t("enter_price_max", locale)
        except ValueError:
            return t("error_generic", locale)

    if state == "await_price_max":
        try:
            data["price_max"] = float(text.strip()) or None
            sess["state"] = "await_location"
            return t("enter_location", locale)
        except ValueError:
            return t("error_generic", locale)

    if state == "await_location":
        if text_lower in ("skip", "דלג"):
            data["radius_km"] = None
            sess["state"] = "await_name"
            return t("location_skipped", locale) + "\n\n" + t("enter_preference_name", locale)
        data["location_name"] = text.strip()
        sess["state"] = "await_radius"
        return t("enter_radius", locale) + "\n1. " + t("radius_10", locale) + "\n2. " + t("radius_25", locale) + "\n3. " + t("radius_50", locale) + "\n4. " + t("radius_country", locale)

    if state == "await_radius":
        km = RADIUS_KEYWORDS.get(text_lower)
        if km is None:
            return t("enter_radius", locale) + " (1-4)"
        data["radius_km"] = km if km > 0 else None
        sess["state"] = "await_name"
        return t("enter_preference_name", locale)

    if state == "await_name":
        name = text.strip()
        pref_data = {k: v for k, v in data.items() if not k.startswith("_")}
        pref_data["name"] = name
        await svc.add_preference(user["id"], pref_data)
        free_left = svc.free_deals_remaining(user)
        sess["state"] = "idle"
        sess["data"] = {}
        return t("preference_saved", locale, name=name, free_left=free_left)

    # Default: show help
    return t("help_text", locale)


# ── FastAPI webhook route ─────────────────────────────────────────────────────

@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    ProfileName: str = Form(default=""),
) -> Response:
    """Twilio sends a POST with form data for each inbound WhatsApp message."""
    phone = From.replace("whatsapp:", "")
    try:
        reply_text = await _handle_message(phone, Body, ProfileName or None)
    except Exception as e:
        logger.exception("WhatsApp handler error for %s: %s", phone, e)
        reply_text = t("error_generic", "he")

    resp = MessagingResponse()
    resp.message(reply_text)
    return Response(content=str(resp), media_type="application/xml")

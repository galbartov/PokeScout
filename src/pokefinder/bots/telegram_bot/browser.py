"""
/browse — TCGDex card browser conversation.

Flow:
  /browse
    → Series list
    → Set list for chosen series
    → Card grid (5 per page as buttons) + 🔍 Search button
        - Scroll: ◀️ page ▶️
        - Search: user types name fragment → filtered results shown as buttons
    → Card detail (photo + caption + 🔔 Alert me)
    → Price range → preference saved

States:
  BROWSE_SERIES → BROWSE_SET → BROWSE_GRID → BROWSE_SEARCH
  → BROWSE_CARD_DETAIL → BROWSE_ALERT_PRICE
  → BROWSE_ALERT_PRICE_CUSTOM_MIN → BROWSE_ALERT_PRICE_CUSTOM_MAX
"""
from __future__ import annotations

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from pokefinder import tcgdex
from pokefinder.i18n import t

from .keyboards import market_price_keyboard

logger = logging.getLogger(__name__)

CARDS_PER_PAGE = 5
SETS_PER_PAGE = 8

(
    BROWSE_SERIES,
    BROWSE_SET,
    BROWSE_GRID,
    BROWSE_SEARCH,
    BROWSE_CARD_DETAIL,
    BROWSE_ALERT_PRICE,
    BROWSE_ALERT_PRICE_CUSTOM_MIN,
    BROWSE_ALERT_PRICE_CUSTOM_MAX,
) = range(8)


# ── Keyboards ─────────────────────────────────────────────────────────────────

def _series_keyboard(series_list: list[dict], page: int = 0) -> InlineKeyboardMarkup:
    per_page = 8
    start = page * per_page
    chunk = series_list[start: start + per_page]
    rows = [[InlineKeyboardButton(s["name"], callback_data=f"br_series:{s['id']}")] for s in chunk]
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"br_series_page:{page-1}"))
    if start + per_page < len(series_list):
        nav.append(InlineKeyboardButton("▶️", callback_data=f"br_series_page:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("❌ Cancel", callback_data="br_cancel")])
    return InlineKeyboardMarkup(rows)


def _sets_keyboard(sets: list[dict], series_id: str, page: int = 0) -> InlineKeyboardMarkup:
    start = page * SETS_PER_PAGE
    chunk = sets[start: start + SETS_PER_PAGE]
    rows = []
    for s in chunk:
        count = s.get("cardCount", {}).get("total", "?")
        rows.append([InlineKeyboardButton(
            f"{s['name']} ({count})",
            callback_data=f"br_set:{series_id}:{s['id']}",
        )])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"br_sets_page:{series_id}:{page-1}"))
    if start + SETS_PER_PAGE < len(sets):
        nav.append(InlineKeyboardButton("▶️", callback_data=f"br_sets_page:{series_id}:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("↩️ Series", callback_data="br_back_series")])
    return InlineKeyboardMarkup(rows)


def _grid_keyboard(cards: list[dict], page: int) -> InlineKeyboardMarkup:
    """5 cards as buttons per page + search + pagination + back."""
    start = page * CARDS_PER_PAGE
    chunk = cards[start: start + CARDS_PER_PAGE]
    rows = []
    for card in chunk:
        label = f"#{card.get('localId', '?')}  {card.get('name', '?')}"
        rows.append([InlineKeyboardButton(label, callback_data=f"br_card:{card['id']}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"br_grid_page:{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{-(-len(cards)//CARDS_PER_PAGE)}", callback_data="br_noop"))
    if start + CARDS_PER_PAGE < len(cards):
        nav.append(InlineKeyboardButton("▶️", callback_data=f"br_grid_page:{page+1}"))
    rows.append(nav)

    rows.append([
        InlineKeyboardButton("🔍 Search", callback_data="br_search"),
        InlineKeyboardButton("↩️ Sets", callback_data="br_back_set"),
    ])
    return InlineKeyboardMarkup(rows)


def _search_results_keyboard(cards: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for card in cards[:20]:  # cap at 20 results
        label = f"#{card.get('localId', '?')}  {card.get('name', '?')}"
        rows.append([InlineKeyboardButton(label, callback_data=f"br_card:{card['id']}")])
    rows.append([InlineKeyboardButton("↩️ Back to list", callback_data="br_back_grid")])
    return InlineKeyboardMarkup(rows)


def _card_detail_keyboard(card: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 Alert me", callback_data=f"br_alert:{card['id']}")],
        [InlineKeyboardButton("↩️ List", callback_data="br_back_grid")],
    ])


# ── Grid helpers ──────────────────────────────────────────────────────────────

def _grid_header(cards: list[dict], page: int, set_name: str) -> str:
    total = len(cards)
    start = page * CARDS_PER_PAGE + 1
    end = min(start + CARDS_PER_PAGE - 1, total)
    return f"📦 *{set_name}*\n{start}–{end} of {total} cards\n\nPick a card or search by name:"


async def _send_grid(target, ctx: ContextTypes.DEFAULT_TYPE, edit: bool = True) -> None:
    """Send/edit the card grid message."""
    cards = ctx.user_data["br_cards"]
    page = ctx.user_data.get("br_grid_page", 0)
    set_name = ctx.user_data.get("br_set_name", "")
    text = _grid_header(cards, page, set_name)
    keyboard = _grid_keyboard(cards, page)
    if edit:
        try:
            await target.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            return
        except Exception:
            pass
        # If message has a photo (coming back from card detail), send new message
        try:
            await target.delete()
        except Exception:
            pass
        await target.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    else:
        await target.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


# ── Handlers ──────────────────────────────────────────────────────────────────

async def browse_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        series_list = await tcgdex.get_series()
    except Exception as e:
        logger.error("TCGDex series fetch error: %s", e)
        await update.message.reply_text(t("error_generic", "en"))
        return ConversationHandler.END

    ctx.user_data["br_series_list"] = series_list
    ctx.user_data["br_series_page"] = 0
    await update.message.reply_text("📚 Choose a series:", reply_markup=_series_keyboard(series_list))
    return BROWSE_SERIES


async def series_page(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    page = int(query.data.split(":")[1])
    ctx.user_data["br_series_page"] = page
    await query.edit_message_text(
        "📚 Choose a series:", reply_markup=_series_keyboard(ctx.user_data["br_series_list"], page)
    )
    return BROWSE_SERIES


async def choose_series(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    series_id = query.data.split(":")[1]
    ctx.user_data["br_series_id"] = series_id
    ctx.user_data["br_sets_page"] = 0

    try:
        sets = await tcgdex.get_sets_for_series(series_id)
    except Exception as e:
        logger.error("TCGDex sets fetch error: %s", e)
        await query.edit_message_text(t("error_generic", "en"))
        return ConversationHandler.END

    ctx.user_data["br_sets"] = sets
    series_name = next(
        (s["name"] for s in ctx.user_data["br_series_list"] if s["id"] == series_id), series_id
    )
    header = f"📦 *{series_name}*\nChoose a set:"
    await query.edit_message_text(
        header, parse_mode=ParseMode.MARKDOWN,
        reply_markup=_sets_keyboard(sets, series_id, page=0)
    )
    return BROWSE_SET


async def sets_page(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, series_id, page_str = query.data.split(":")
    page = int(page_str)
    ctx.user_data["br_sets_page"] = page
    await query.edit_message_text(
        "📦 Choose a set:", reply_markup=_sets_keyboard(ctx.user_data["br_sets"], series_id, page)
    )
    return BROWSE_SET


async def back_to_series(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    page = ctx.user_data.get("br_series_page", 0)
    await query.edit_message_text(
        "📚 Choose a series:", reply_markup=_series_keyboard(ctx.user_data.get("br_series_list", []), page)
    )
    return BROWSE_SERIES


async def choose_set(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, series_id, set_id = query.data.split(":")
    ctx.user_data["br_set_id"] = set_id

    try:
        full_set = await tcgdex.get_set(set_id)
    except Exception as e:
        logger.error("TCGDex set fetch error: %s", e)
        await query.edit_message_text(t("error_generic", "en"))
        return ConversationHandler.END

    cards = list(reversed(full_set.get("cards", [])))
    if not cards:
        msg = "This set has no cards."
        await query.edit_message_text(msg)
        return BROWSE_SET

    ctx.user_data["br_cards"] = cards
    ctx.user_data["br_grid_page"] = 0
    ctx.user_data["br_set_name"] = full_set.get("name", set_id)

    await _send_grid(query, ctx, edit=True)
    return BROWSE_GRID


async def grid_page(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    page = int(query.data.split(":")[1])
    ctx.user_data["br_grid_page"] = page
    await _send_grid(query, ctx, edit=True)
    return BROWSE_GRID


async def back_to_grid(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _send_grid(query, ctx, edit=True)
    return BROWSE_GRID


async def back_to_set(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    series_id = ctx.user_data.get("br_series_id", "")
    sets = ctx.user_data.get("br_sets", [])
    page = ctx.user_data.get("br_sets_page", 0)
    try:
        await query.edit_message_text(
            "📦 Choose a set:", reply_markup=_sets_keyboard(sets, series_id, page)
        )
    except Exception:
        try:
            await query.delete()
        except Exception:
            pass
        await query.message.reply_text(
            "📦 Choose a set:", reply_markup=_sets_keyboard(sets, series_id, page)
        )
    return BROWSE_SET


async def prompt_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """User tapped 🔍 Search — ask for text input."""
    query = update.callback_query
    await query.answer()
    set_name = ctx.user_data.get("br_set_name", "")
    msg = f"🔍 Search in *{set_name}*\nType a card name (partial or full):"
    await query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN)
    return BROWSE_SEARCH


async def do_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """User typed a search query — filter cards and show results."""
    query_text = update.message.text.strip().lower()
    all_cards = ctx.user_data.get("br_cards", [])
    matches = [c for c in all_cards if query_text in c.get("name", "").lower()]

    if not matches:
        await update.message.reply_text(f"No cards found for \"{query_text}\". Try again:")
        return BROWSE_SEARCH

    set_name = ctx.user_data.get("br_set_name", "")
    header = f"🔍 *{len(matches)} result(s)* for \"{query_text}\" in {set_name}:"
    await update.message.reply_text(
        header,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=_search_results_keyboard(matches),
    )
    return BROWSE_GRID  # reuse grid state — card tap works the same


async def show_card_detail(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """User tapped a card from grid or search results — show photo + alert button."""
    query = update.callback_query
    await query.answer()
    card_id = query.data.split(":")[1]

    card = await tcgdex.get_card(card_id)
    if not card:
        await query.answer("Failed to load card", show_alert=True)
        return BROWSE_GRID

    ctx.user_data["br_current_card"] = card
    caption = tcgdex.format_card_caption(card, "en")
    keyboard = _card_detail_keyboard(card)
    image_url = tcgdex.card_image_url(card)

    try:
        await query.delete()
    except Exception:
        pass

    if image_url:
        await query.message.reply_photo(
            photo=image_url,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
        )
    else:
        await query.message.reply_text(
            caption + "\n\n_(no image)_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
        )
    return BROWSE_CARD_DETAIL


async def alert_card(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    card_id = query.data.split(":")[1]
    card = ctx.user_data.get("br_current_card", {})
    ctx.user_data["br_alert_card_id"] = card_id
    ctx.user_data["br_alert_card_name"] = card.get("name", card_id)
    ctx.user_data["br_alert_card_number"] = card.get("localId", "")
    ctx.user_data["br_alert_set_name"] = card.get("set", {}).get("name", "")

    from pokefinder.scrapers.ebay import get_last_sold_price
    card_name = card.get("name", card_id)
    local_id = card.get("localId")
    set_total = card.get("set", {}).get("cardCount", {}).get("official")
    # Detect graded: set if user came from graded category selection or /graded command
    pref_cats = ctx.user_data.get("new_pref", {}).get("categories", set())
    graded = (
        ctx.user_data.get("br_category") == "graded"
        or "graded" in pref_cats
    )
    last_sold = await get_last_sold_price(
        card_name,
        local_id=local_id,
        set_total=set_total,
        graded=graded,
    )
    ctx.user_data["br_last_sold"] = last_sold
    if last_sold:
        number_str = f" · {local_id}/{set_total}" if local_id and set_total else ""
        price_line = f"\n📊 Last sold on eBay: *${last_sold:,.2f}*{number_str}"
    else:
        price_line = ""

    auction_note = t("auction_threshold_note", "en")
    msg = f"🔔 *{card_name}*{price_line}\n\nWhat price range interests you?\n\n{auction_note}"
    kb = market_price_keyboard(last_sold, "br_price", back="br_back_grid")
    try:
        await query.edit_message_caption(caption=msg, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    except Exception:
        # Message has no photo (text-only card) — edit as text
        await query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    return BROWSE_ALERT_PRICE


async def alert_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")

    if parts[1] == "custom":
        await query.edit_message_caption(caption=t("enter_price_min", "en"))
        return BROWSE_ALERT_PRICE_CUSTOM_MIN

    price_min = None if parts[1] == "any" else (float(parts[1]) if float(parts[1]) > 0 else None)
    price_max = None if parts[1] == "any" else float(parts[2])
    return await _save_card_alert(query, ctx, price_min, price_max)


async def alert_price_custom_min(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text.strip())
        ctx.user_data["br_price_min"] = val if val > 0 else None
        await update.message.reply_text(t("enter_price_max", "en"))
        return BROWSE_ALERT_PRICE_CUSTOM_MAX
    except ValueError:
        await update.message.reply_text(t("error_generic", "en"))
        return BROWSE_ALERT_PRICE_CUSTOM_MIN


async def alert_price_custom_max(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text.strip())
        price_max = val if val > 0 else None
        return await _save_card_alert(
            update.message, ctx, ctx.user_data.get("br_price_min"), price_max
        )
    except ValueError:
        await update.message.reply_text(t("error_generic", "en"))
        return BROWSE_ALERT_PRICE_CUSTOM_MAX


async def _save_card_alert(
    message_or_query,
    ctx: ContextTypes.DEFAULT_TYPE,
    price_min: float | None,
    price_max: float | None,
) -> int:
    from pokefinder.bots.service import BotService
    from pokefinder.db import get_client

    card_id = ctx.user_data["br_alert_card_id"]
    card_name = ctx.user_data["br_alert_card_name"]

    db = await get_client()
    svc = BotService(db)

    if hasattr(message_or_query, "from_user"):
        tg_user = message_or_query.from_user
    else:
        tg_user = message_or_query.message.from_user

    user = await svc.get_or_create_telegram_user(tg_user.id, tg_user.username, tg_user.full_name)
    free_left = svc.free_deals_remaining(user)

    allowed, _, limit = await svc.can_add_preference(user)
    if not allowed:
        from pokefinder.i18n import t as _t
        upgrade_hint = _t("preference_limit_pro_hint", "en") if svc.is_subscribed(user) else _t("preference_limit_upgrade_hint", "en")
        cap_msg = _t("preference_limit_reached", "en", limit=limit, upgrade_hint=upgrade_hint)
        try:
            if hasattr(message_or_query, "edit_message_caption"):
                await message_or_query.edit_message_caption(caption=cap_msg)
            elif hasattr(message_or_query, "edit_message_text"):
                await message_or_query.edit_message_text(cap_msg)
            else:
                await message_or_query.reply_text(cap_msg)
        except Exception:
            pass
        return ConversationHandler.END

    card_number = ctx.user_data.get("br_alert_card_number", "")
    set_name = ctx.user_data.get("br_alert_set_name", "")
    keywords = [card_name.lower()]
    if card_number:
        keywords.append(card_number)
        keywords.append(card_number.split("/")[0])
    if set_name:
        keywords.append(set_name.lower())

    pref_data = {
        "name": card_name,
        "categories": ["singles", "graded"],
        "keywords": keywords,
        "tcg_product_id": card_id,
        "price_min": price_min,
        "price_max": price_max,
        "radius_km": None,
    }
    duplicate = await svc.find_duplicate_preference(user["id"], pref_data)
    if duplicate:
        dup_msg = t("preference_duplicate", "en", name=duplicate["name"])
        try:
            if hasattr(message_or_query, "edit_message_caption"):
                await message_or_query.edit_message_caption(caption=dup_msg)
            elif hasattr(message_or_query, "edit_message_text"):
                await message_or_query.edit_message_text(dup_msg)
            else:
                await message_or_query.reply_text(dup_msg)
        except Exception:
            pass
        return ConversationHandler.END

    saved_pref = await svc.add_preference(user["id"], pref_data)

    price_str = ""
    if price_min and price_max:
        price_str = f" (${int(price_min)}–${int(price_max)})"
    elif price_max:
        price_str = f" (up to ${int(price_max)})"

    msg = f"✅ *{card_name}*{price_str}\n\nI'll alert you when a deal is found!"

    try:
        if hasattr(message_or_query, "edit_message_caption"):
            await message_or_query.edit_message_caption(caption=msg, parse_mode=ParseMode.MARKDOWN)
        elif hasattr(message_or_query, "edit_message_text"):
            await message_or_query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN)
        else:
            await message_or_query.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        pass

    for key in list(ctx.user_data.keys()):
        if key.startswith("br_"):
            del ctx.user_data[key]

    from pokefinder.matching.engine import match_new_preference
    import asyncio
    asyncio.create_task(match_new_preference(user, saved_pref))

    return ConversationHandler.END


async def browse_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(t("cancel", "en"))
        except Exception:
            await update.callback_query.message.reply_text(t("cancel", "en"))
    else:
        await update.message.reply_text(t("cancel", "en"))
    for key in list(ctx.user_data.keys()):
        if key.startswith("br_"):
            del ctx.user_data[key]
    return ConversationHandler.END


async def noop(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    return BROWSE_GRID


# ── Build handler ─────────────────────────────────────────────────────────────

def build_browser_handler() -> ConversationHandler:
    card_tap = CallbackQueryHandler(show_card_detail, pattern="^br_card:")
    return ConversationHandler(
        entry_points=[CommandHandler("browse", browse_start)],
        states={
            BROWSE_SERIES: [
                CallbackQueryHandler(series_page, pattern="^br_series_page:"),
                CallbackQueryHandler(choose_series, pattern="^br_series:"),
                CallbackQueryHandler(browse_cancel, pattern="^br_cancel$"),
            ],
            BROWSE_SET: [
                CallbackQueryHandler(sets_page, pattern="^br_sets_page:"),
                CallbackQueryHandler(choose_set, pattern="^br_set:"),
                CallbackQueryHandler(back_to_series, pattern="^br_back_series$"),
            ],
            BROWSE_GRID: [
                card_tap,
                CallbackQueryHandler(grid_page, pattern="^br_grid_page:"),
                CallbackQueryHandler(prompt_search, pattern="^br_search$"),
                CallbackQueryHandler(back_to_set, pattern="^br_back_set$"),
                CallbackQueryHandler(noop, pattern="^br_noop$"),
            ],
            BROWSE_SEARCH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, do_search),
                CallbackQueryHandler(back_to_grid, pattern="^br_back_grid$"),
            ],
            BROWSE_CARD_DETAIL: [
                CallbackQueryHandler(alert_card, pattern="^br_alert:"),
                CallbackQueryHandler(back_to_grid, pattern="^br_back_grid$"),
            ],
            BROWSE_ALERT_PRICE: [
                CallbackQueryHandler(alert_price, pattern="^br_price:"),
                CallbackQueryHandler(back_to_grid, pattern="^br_back_grid$"),
            ],
            BROWSE_ALERT_PRICE_CUSTOM_MIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, alert_price_custom_min),
            ],
            BROWSE_ALERT_PRICE_CUSTOM_MAX: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, alert_price_custom_max),
            ],
        },
        fallbacks=[CommandHandler("cancel", browse_cancel)],
        allow_reentry=True,
        per_message=False,
    )

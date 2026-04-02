"""
Telegram ConversationHandler for /start onboarding and /add alert setup.

/add flow (search-first, 3 messages):
  User: /add
  Bot:  "What are you looking for?"
  User: charizard ex sir
  Bot:  [Searching…] → edit to result buttons
  User: taps result
  Bot:  photo + market price + price tier buttons
  User: taps price → ✅ saved
"""
from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from pokefinder.i18n import t
from pokefinder.tcg_db.search import card_keywords

from .keyboards import (
    keyword_fallback_keyboard,
    market_price_keyboard,
    search_results_keyboard,
)

logger = logging.getLogger(__name__)

# ── Conversation states ───────────────────────────────────────────────────────
(
    SEARCH_QUERY,
    CONFIRM_RESULT,
    CONFIRM_PRICE,
    CONFIRM_PRICE_MIN,
    CONFIRM_PRICE_MAX,
) = range(5)

_SA = "_sa"  # namespace key in user_data


def _sa(ctx: ContextTypes.DEFAULT_TYPE) -> dict:
    if _SA not in ctx.user_data:
        ctx.user_data[_SA] = {}
    return ctx.user_data[_SA]


def _clear_sa(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    ctx.user_data.pop(_SA, None)


# ── Entry points ──────────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point: /start — register user, show browse hint."""
    from pokefinder.db import get_client
    from pokefinder.bots.service import BotService
    db = await get_client()
    svc = BotService(db)
    tg = update.effective_user
    await svc.get_or_create_telegram_user(tg.id, tg.username, tg.full_name)
    ctx.user_data["locale"] = "en"
    await update.message.reply_text(
        t("onboarding_browse", "en"),
        parse_mode=ParseMode.MARKDOWN,
    )
    return ConversationHandler.END


async def add(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point: /add — cap check then prompt for search query."""
    from pokefinder.db import get_client
    from pokefinder.bots.service import BotService
    db = await get_client()
    svc = BotService(db)
    tg = update.effective_user
    user = await svc.get_or_create_telegram_user(tg.id, tg.username, tg.full_name)

    allowed, _, limit = await svc.can_add_preference(user)
    if not allowed:
        upgrade_hint = (
            t("preference_limit_pro_hint", "en")
            if svc.is_subscribed(user)
            else t("preference_limit_upgrade_hint", "en")
        )
        await update.message.reply_text(
            t("preference_limit_reached", "en", limit=limit, upgrade_hint=upgrade_hint),
        )
        return ConversationHandler.END

    _clear_sa(ctx)
    ctx.user_data["locale"] = "en"
    await update.message.reply_text(t("add_search_prompt", "en"))
    return SEARCH_QUERY


# ── State handlers ────────────────────────────────────────────────────────────

async def _send_results_page(target, results: list[dict], query: str, page: int = 0):
    """
    Send a photo album (numbered 1–5) + picker keyboard for the current page.
    Returns the picker message so its ID can be saved for later editing.
    """
    import os
    from telegram import InputMediaPhoto

    _SA_PAGE_SIZE = 5
    start = page * _SA_PAGE_SIZE
    chunk = results[start: start + _SA_PAGE_SIZE]

    # Open any local file handles so they stay open during the send call
    open_files = []
    media = []
    try:
        for i, r in enumerate(chunk):
            caption = f"{i + 1}. {r['name_en']}" + (f"\n{r['set_name']}" if r.get("set_name") else "")
            url_img = r.get("image_url", "")
            local_img = r.get("local_image_path", "")

            if url_img and url_img.startswith("http"):
                media.append(InputMediaPhoto(media=url_img, caption=caption))
            elif local_img and os.path.exists(local_img):
                fh = open(local_img, "rb")
                open_files.append(fh)
                media.append(InputMediaPhoto(media=fh, caption=caption))
            # If no image available for this result, skip it from the album
            # (picker still shows all results)

        if media:
            try:
                await target.reply_media_group(media=media)
            except Exception:
                pass  # Fall through to text-only picker if album fails
    finally:
        for fh in open_files:
            fh.close()

    picker = await target.reply_text(
        f"*Results for {query}* — tap a number:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=search_results_keyboard(results, query, page=page),
    )
    return picker


async def search_query(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """User typed a search query — show spinner then results."""
    from pokefinder.tcg_db.search import search_products

    query = update.message.text.strip()
    _sa(ctx)["query"] = query

    # Show "Searching…" immediately, then edit to results
    msg = await update.message.reply_text(t("add_searching", "en"))

    results = await search_products(query, limit=20)
    _sa(ctx)["results"] = results
    _sa(ctx)["page"] = 0

    if results:
        await msg.delete()
        picker_msg = await _send_results_page(update.message, results, query, page=0)
        _sa(ctx)["picker_msg_id"] = picker_msg.message_id
        return CONFIRM_RESULT
    else:
        await msg.edit_text(
            t("add_no_results", "en", query=query),
            reply_markup=keyword_fallback_keyboard(query),
        )
        return CONFIRM_RESULT


async def confirm_result(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """User tapped a result button."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "sa_noop":
        return CONFIRM_RESULT

    if data.startswith("sa_page:"):
        page = int(data.split(":")[1])
        _sa(ctx)["page"] = page
        results = _sa(ctx).get("results", [])
        search_q = _sa(ctx).get("query", "")
        # Delete old picker + send fresh album + new picker
        try:
            await query.delete()
        except Exception:
            pass
        picker = await _send_results_page(query.message, results, search_q, page=page)
        _sa(ctx)["picker_msg_id"] = picker.message_id
        return CONFIRM_RESULT

    if data == "sa_retry":
        await query.edit_message_text(t("add_search_prompt", "en"))
        _sa(ctx).pop("results", None)
        _sa(ctx).pop("query", None)
        return SEARCH_QUERY

    if data == "sa_keyword":
        # Keyword-based alert — skip to price
        keyword = _sa(ctx).get("query", "")
        _sa(ctx)["type"] = "keyword"
        _sa(ctx)["keyword"] = keyword
        last_sold = None
        price_line = ""
        auction_note = t("auction_threshold_note", "en")
        msg_text = t("add_set_price", "en", name=f'"{keyword}"', price_line=price_line, auction_note=auction_note)
        await query.edit_message_text(
            msg_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=market_price_keyboard(last_sold, "sa_price", back="sa_back"),
        )
        return CONFIRM_PRICE

    # sa_pick:N
    if data.startswith("sa_pick:"):
        idx = int(data.split(":")[1])
        results = _sa(ctx).get("results", [])
        if idx >= len(results):
            await query.answer("Invalid selection", show_alert=True)
            return CONFIRM_RESULT

        result = results[idx]
        _sa(ctx)["result"] = result

        name = result["name_en"]
        set_name = result.get("set_name", "")
        product_type = result.get("product_type", "card")

        # Fetch market price
        from pokefinder.scrapers.ebay import get_last_sold_price
        last_sold = await get_last_sold_price(name)
        _sa(ctx)["last_sold"] = last_sold

        price_line = f"\n📊 Current eBay market price: *${last_sold:,.2f}*" if last_sold else ""
        auction_note = t("auction_threshold_note", "en")
        caption = t("add_set_price", "en", name=name, price_line=price_line, auction_note=auction_note)
        price_kb = market_price_keyboard(last_sold, "sa_price", back="sa_back")

        # Try to show product image
        image_sent = False
        local_img = result.get("local_image_path")
        url_img = result.get("image_url")

        try:
            await query.delete()
        except Exception:
            pass

        if local_img:
            import os
            if os.path.exists(local_img):
                with open(local_img, "rb") as f:
                    await query.message.reply_photo(
                        photo=f,
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=price_kb,
                    )
                image_sent = True
        elif url_img and url_img.startswith("http"):
            await query.message.reply_photo(
                photo=url_img,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=price_kb,
            )
            image_sent = True

        if not image_sent:
            await query.message.reply_text(
                caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=price_kb,
            )
        return CONFIRM_PRICE

    return CONFIRM_RESULT


async def confirm_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """User tapped a price tier button (or Back)."""
    query = update.callback_query
    await query.answer()

    if query.data == "sa_back":
        results = _sa(ctx).get("results", [])
        search_q = _sa(ctx).get("query", "")
        page = _sa(ctx).get("page", 0)
        try:
            await query.delete()
        except Exception:
            pass
        picker = await _send_results_page(query.message, results, search_q, page=page)
        _sa(ctx)["picker_msg_id"] = picker.message_id
        return CONFIRM_RESULT

    parts = query.data.split(":")

    if parts[1] == "custom":
        msg = t("enter_price_min", "en")
        try:
            await query.edit_message_caption(caption=msg)
        except Exception:
            await query.edit_message_text(msg)
        return CONFIRM_PRICE_MIN

    price_min = None if parts[1] == "any" else (float(parts[1]) if float(parts[1]) > 0 else None)
    price_max = None if parts[1] == "any" else float(parts[2])
    return await _save_search_alert(query, ctx, price_min, price_max)


async def confirm_price_min(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text.strip())
        _sa(ctx)["price_min"] = val if val > 0 else None
        await update.message.reply_text(t("enter_price_max", "en"))
        return CONFIRM_PRICE_MAX
    except ValueError:
        await update.message.reply_text(t("error_generic", "en"))
        return CONFIRM_PRICE_MIN


async def confirm_price_max(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text.strip())
        price_max = val if val > 0 else None
        return await _save_search_alert(
            update.message, ctx, _sa(ctx).get("price_min"), price_max
        )
    except ValueError:
        await update.message.reply_text(t("error_generic", "en"))
        return CONFIRM_PRICE_MAX


# ── Save helper ───────────────────────────────────────────────────────────────

async def _save_search_alert(
    message_or_query,
    ctx: ContextTypes.DEFAULT_TYPE,
    price_min: float | None,
    price_max: float | None,
) -> int:
    from pokefinder.db import get_client
    from pokefinder.bots.service import BotService

    db = await get_client()
    svc = BotService(db)

    if hasattr(message_or_query, "from_user"):
        tg_user = message_or_query.from_user
    else:
        tg_user = message_or_query.message.from_user

    user = await svc.get_or_create_telegram_user(tg_user.id, tg_user.username, tg_user.full_name)
    free_left = svc.free_deals_remaining(user)

    # Re-check cap (race condition guard)
    allowed, _, limit = await svc.can_add_preference(user)
    if not allowed:
        upgrade_hint = (
            t("preference_limit_pro_hint", "en")
            if svc.is_subscribed(user)
            else t("preference_limit_upgrade_hint", "en")
        )
        cap_msg = t("preference_limit_reached", "en", limit=limit, upgrade_hint=upgrade_hint)
        await _reply_or_edit_async(message_or_query, cap_msg)
        _clear_sa(ctx)
        return ConversationHandler.END

    sa = _sa(ctx)
    alert_type = sa.get("type", "product")

    if alert_type == "keyword":
        keyword = sa.get("keyword", "")
        pref_data = {
            "name": keyword,
            "categories": ["singles", "sealed", "graded", "bulk"],
            "keywords": [keyword],
            "price_min": price_min,
            "price_max": price_max,
            "radius_km": None,
        }
        name = f'"{keyword}"'
    else:
        result = sa.get("result", {})
        product_type = result.get("product_type", "card")
        name = result.get("name_en", "?")
        pref_data = {
            "name": name,
            "categories": ["sealed"] if product_type == "sealed" else ["singles"],
            "keywords": card_keywords(result) if product_type == "card" else [name.lower()],
            "tcg_product_id": result.get("id"),
            "price_min": price_min,
            "price_max": price_max,
            "radius_km": None,
        }

    duplicate = await svc.find_duplicate_preference(user["id"], pref_data)
    if duplicate:
        dup_msg = t("preference_duplicate", "en", name=duplicate["name"])
        await _reply_or_edit_async(message_or_query, dup_msg)
        _clear_sa(ctx)
        return ConversationHandler.END

    saved_pref = await svc.add_preference(user["id"], pref_data)

    price_str = ""
    if price_min and price_max:
        price_str = f" (${int(price_min)}–${int(price_max)})"
    elif price_max:
        price_str = f" (up to ${int(price_max)})"

    conf_msg = f"✅ *{name}*{price_str}\n\nI'll alert you when a deal is found!"
    await _reply_or_edit_async(message_or_query, conf_msg, parse_mode=ParseMode.MARKDOWN)
    _clear_sa(ctx)

    # Fire-and-forget: send matching listings from the last 24h
    from pokefinder.matching.engine import match_new_preference
    import asyncio
    asyncio.create_task(match_new_preference(user, saved_pref))

    return ConversationHandler.END


async def _reply_or_edit_async(message_or_query, text: str, parse_mode=None) -> None:
    kwargs = {"parse_mode": parse_mode} if parse_mode else {}
    try:
        if hasattr(message_or_query, "edit_message_caption"):
            await message_or_query.edit_message_caption(caption=text, **kwargs)
        elif hasattr(message_or_query, "edit_message_text"):
            await message_or_query.edit_message_text(text, **kwargs)
        else:
            await message_or_query.reply_text(text, **kwargs)
    except Exception:
        try:
            await message_or_query.message.reply_text(text, **kwargs)
        except Exception:
            pass



async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    _clear_sa(ctx)
    await update.message.reply_text(t("cancel", "en"))
    return ConversationHandler.END


# ── Build the ConversationHandler ─────────────────────────────────────────────

def build_onboarding_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("add", add),
        ],
        states={
            SEARCH_QUERY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_query),
            ],
            CONFIRM_RESULT: [
                CallbackQueryHandler(confirm_result, pattern="^sa_"),
            ],
            CONFIRM_PRICE: [
                CallbackQueryHandler(confirm_price, pattern="^sa_price:|^sa_back$"),
            ],
            CONFIRM_PRICE_MIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_price_min),
            ],
            CONFIRM_PRICE_MAX: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_price_max),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
        per_message=False,
    )

"""
/sealed — Sealed product browser conversation.

Flow:
  /sealed
    → Category filter (ETB / Booster Box / All)
    → Product list (paginated, grouped by era)
    → Product detail (box art photo + name)
        - 🔔 Alert me → price range → saved
        - ↩️ Back to list
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
    filters,
    MessageHandler,
)

from pokefinder.i18n import t
from pokefinder.tcg_db.sealed_products import SEALED_PRODUCTS, local_image_path

from .keyboards import market_price_keyboard

logger = logging.getLogger(__name__)

PRODUCTS_PER_PAGE = 8

(
    SEALED_CATEGORY,
    SEALED_LIST,
    SEALED_DETAIL,
    SEALED_PRICE,
    SEALED_PRICE_CUSTOM_MIN,
    SEALED_PRICE_CUSTOM_MAX,
) = range(6)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _filter_products(category: str) -> list[dict]:
    if category == "etb":
        filtered = [p for p in SEALED_PRODUCTS if p.get("product_type") == "etb"]
    elif category == "booster":
        filtered = [p for p in SEALED_PRODUCTS if p.get("product_type") == "booster_box"]
    else:
        filtered = list(SEALED_PRODUCTS)
    return sorted(filtered, key=lambda p: p.get("tcgplayer_id", 0), reverse=True)


def _product_label(p: dict) -> str:
    return ("📦 " if "booster" in p["id"] else "🎁 ") + p["en"]


# ── Keyboards ─────────────────────────────────────────────────────────────────

def _category_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Elite Trainer Box", callback_data="sl_cat:etb")],
        [InlineKeyboardButton("📦 Booster Box",       callback_data="sl_cat:booster")],
        [InlineKeyboardButton("🔍 All",               callback_data="sl_cat:all")],
        [InlineKeyboardButton("❌ Cancel",             callback_data="sl_cancel")],
    ])


def _list_keyboard(products: list[dict], page: int) -> InlineKeyboardMarkup:
    start = page * PRODUCTS_PER_PAGE
    chunk = products[start: start + PRODUCTS_PER_PAGE]
    rows = []
    for p in chunk:
        rows.append([InlineKeyboardButton(
            _product_label(p),
            callback_data=f"sl_product:{p['id']}",
        )])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"sl_page:{page-1}"))
    total_pages = -(-len(products) // PRODUCTS_PER_PAGE)
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="sl_noop"))
    if start + PRODUCTS_PER_PAGE < len(products):
        nav.append(InlineKeyboardButton("▶️", callback_data=f"sl_page:{page+1}"))
    if len(products) > PRODUCTS_PER_PAGE:
        rows.append(nav)

    rows.append([InlineKeyboardButton("↩️ Category", callback_data="sl_back_category")])
    return InlineKeyboardMarkup(rows)


def _detail_keyboard(product_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 Alert me", callback_data=f"sl_alert:{product_id}")],
        [InlineKeyboardButton("↩️ List",     callback_data="sl_back_list")],
    ])



# ── Send helpers ──────────────────────────────────────────────────────────────

async def _send_list(target, ctx: ContextTypes.DEFAULT_TYPE, edit: bool = True) -> None:
    products = ctx.user_data["sl_products"]
    page = ctx.user_data.get("sl_page", 0)
    category = ctx.user_data.get("sl_category", "all")

    cat_label = {
        "etb": "🎁 Elite Trainer Boxes",
        "booster": "📦 Booster Boxes",
        "all": "🔍 All Products",
    }[category]

    header = f"*{cat_label}*\nSelect a product to set an alert:"
    keyboard = _list_keyboard(products, page)

    if edit:
        try:
            await target.edit_message_text(header, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            return
        except Exception:
            pass
        try:
            await target.delete()
        except Exception:
            pass
        await target.message.reply_text(header, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    else:
        await target.reply_text(header, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


# ── Handlers ──────────────────────────────────────────────────────────────────

async def sealed_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "📦 What type of sealed product are you looking for?",
        reply_markup=_category_keyboard(),
    )
    return SEALED_CATEGORY


async def choose_category(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    category = query.data.split(":")[1]

    ctx.user_data["sl_category"] = category
    ctx.user_data["sl_products"] = _filter_products(category)
    ctx.user_data["sl_page"] = 0

    await _send_list(query, ctx, edit=True)
    return SEALED_LIST


async def list_page(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    ctx.user_data["sl_page"] = int(query.data.split(":")[1])
    await _send_list(query, ctx, edit=True)
    return SEALED_LIST


async def back_to_category(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📦 What type of sealed product are you looking for?",
        reply_markup=_category_keyboard(),
    )
    return SEALED_CATEGORY


async def back_to_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _send_list(query, ctx, edit=True)
    return SEALED_LIST


async def show_product(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    product_id = query.data.split(":")[1]

    product = next((p for p in SEALED_PRODUCTS if p["id"] == product_id), None)
    if not product:
        await query.answer("Product not found", show_alert=True)
        return SEALED_LIST

    ctx.user_data["sl_current_product"] = product
    name = product["en"]
    set_name = product.get("set", "")
    caption = f"*{name}*\n📦 {set_name}"
    keyboard = _detail_keyboard(product_id)
    img_path = local_image_path(product)

    try:
        await query.delete()
    except Exception:
        pass

    if img_path:
        with open(img_path, "rb") as f:
            await query.message.reply_photo(
                photo=f,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
            )
    else:
        await query.message.reply_text(
            caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
        )
    return SEALED_DETAIL


async def alert_product(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    product = ctx.user_data.get("sl_current_product", {})
    name = product.get("en", product.get("id", "?"))

    # Fetch live eBay market price for context
    from pokefinder.scrapers.ebay import get_last_sold_price
    last_sold = await get_last_sold_price(name)
    ctx.user_data["sl_last_sold"] = last_sold

    if last_sold:
        price_line = f"\n📊 Current eBay market price: *${last_sold:,.2f}*"
    else:
        price_line = ""

    auction_note = t("auction_threshold_note", "en")
    msg = f"🔔 *{name}*{price_line}\n\nWhat price range interests you?\n\n{auction_note}"
    kb = market_price_keyboard(last_sold, "sl_price", back="sl_back_list")
    try:
        await query.edit_message_caption(caption=msg, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    except Exception:
        await query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    return SEALED_PRICE


async def choose_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")

    if parts[1] == "custom":
        msg = "Enter min price ($), or 0 for none:"
        try:
            await query.edit_message_caption(caption=msg)
        except Exception:
            await query.edit_message_text(msg)
        return SEALED_PRICE_CUSTOM_MIN

    price_min = None if parts[1] == "any" else (float(parts[1]) if float(parts[1]) > 0 else None)
    price_max = None if parts[1] == "any" else float(parts[2])
    return await _save_alert(query, ctx, price_min, price_max)


async def price_custom_min(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text.strip())
        ctx.user_data["sl_price_min"] = val if val > 0 else None
        await update.message.reply_text("Enter max price ($), or 0 for none:")
        return SEALED_PRICE_CUSTOM_MAX
    except ValueError:
        await update.message.reply_text(t("error_generic", "en"))
        return SEALED_PRICE_CUSTOM_MIN


async def price_custom_max(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text.strip())
        price_max = val if val > 0 else None
        return await _save_alert(
            update.message, ctx, ctx.user_data.get("sl_price_min"), price_max
        )
    except ValueError:
        await update.message.reply_text(t("error_generic", "en"))
        return SEALED_PRICE_CUSTOM_MAX


async def _save_alert(
    message_or_query,
    ctx: ContextTypes.DEFAULT_TYPE,
    price_min: float | None,
    price_max: float | None,
) -> int:
    from pokefinder.bots.service import BotService
    from pokefinder.db import get_client

    product = ctx.user_data["sl_current_product"]
    name = product["en"]

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
        upgrade_hint = t("preference_limit_pro_hint", "en") if svc.is_subscribed(user) else t("preference_limit_upgrade_hint", "en")
        cap_msg = t("preference_limit_reached", "en", limit=limit, upgrade_hint=upgrade_hint)
        try:
            if hasattr(message_or_query, "edit_message_caption"):
                await message_or_query.edit_message_caption(caption=cap_msg)
            elif hasattr(message_or_query, "edit_message_text"):
                await message_or_query.edit_message_text(cap_msg)
            else:
                await message_or_query.reply_text(cap_msg)
        except Exception:
            pass
        for key in list(ctx.user_data.keys()):
            if key.startswith("sl_"):
                del ctx.user_data[key]
        return ConversationHandler.END

    pref_data = {
        "name": name,
        "categories": ["sealed"],
        "keywords": product.get("aliases", [product["en"].lower()]),
        "tcg_product_id": product["id"],
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
        for key in list(ctx.user_data.keys()):
            if key.startswith("sl_"):
                del ctx.user_data[key]
        return ConversationHandler.END

    saved_pref = await svc.add_preference(user["id"], pref_data)

    price_str = ""
    if price_min and price_max:
        price_str = f" (${int(price_min)}–${int(price_max)})"
    elif price_max:
        price_str = f" (up to ${int(price_max)})"

    msg = f"✅ *{name}*{price_str}\n\nI'll alert you when a deal is found!"

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
        if key.startswith("sl_"):
            del ctx.user_data[key]

    from pokefinder.matching.engine import match_new_preference
    import asyncio
    asyncio.create_task(match_new_preference(user, saved_pref))

    return ConversationHandler.END


async def sealed_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(t("cancel", "en"))
        except Exception:
            await update.callback_query.message.reply_text(t("cancel", "en"))
    else:
        await update.message.reply_text(t("cancel", "en"))
    for key in list(ctx.user_data.keys()):
        if key.startswith("sl_"):
            del ctx.user_data[key]
    return ConversationHandler.END


async def noop(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    return SEALED_LIST


# ── Build handler ─────────────────────────────────────────────────────────────

def build_sealed_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("sealed", sealed_start)],
        states={
            SEALED_CATEGORY: [
                CallbackQueryHandler(choose_category, pattern="^sl_cat:"),
                CallbackQueryHandler(sealed_cancel, pattern="^sl_cancel$"),
            ],
            SEALED_LIST: [
                CallbackQueryHandler(show_product, pattern="^sl_product:"),
                CallbackQueryHandler(list_page, pattern="^sl_page:"),
                CallbackQueryHandler(back_to_category, pattern="^sl_back_category$"),
                CallbackQueryHandler(noop, pattern="^sl_noop$"),
            ],
            SEALED_DETAIL: [
                CallbackQueryHandler(alert_product, pattern="^sl_alert:"),
                CallbackQueryHandler(back_to_list, pattern="^sl_back_list$"),
            ],
            SEALED_PRICE: [
                CallbackQueryHandler(choose_price, pattern="^sl_price:"),
                CallbackQueryHandler(back_to_list, pattern="^sl_back_list$"),
            ],
            SEALED_PRICE_CUSTOM_MIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, price_custom_min),
            ],
            SEALED_PRICE_CUSTOM_MAX: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, price_custom_max),
            ],
        },
        fallbacks=[CommandHandler("cancel", sealed_cancel)],
        allow_reentry=True,
        per_message=False,
    )

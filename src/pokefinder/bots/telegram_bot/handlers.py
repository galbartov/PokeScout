"""
Non-conversation Telegram command handlers:
/preferences, /status, /subscribe, /help
Admin: /admin_stats, /admin_health
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

from pokefinder.bots.service import BotService
from pokefinder.config import settings
from pokefinder.db import get_client
from pokefinder.db import queries
from pokefinder.i18n import t

from .keyboards import categories_keyboard, preference_edit_keyboard, preference_list_keyboard, price_keyboard

logger = logging.getLogger(__name__)


async def _get_user(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> tuple[dict, BotService]:
    db = await get_client()
    svc = BotService(db)
    tg = update.effective_user
    user = await svc.get_or_create_telegram_user(tg.id, tg.username, tg.full_name)
    ctx.user_data["locale"] = "en"
    return user, svc


def _is_admin(update: Update) -> bool:
    return update.effective_user.id == settings.admin_telegram_id


# ── /preferences ──────────────────────────────────────────────────────────────

async def preferences_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user, svc = await _get_user(update, ctx)
    prefs = await svc.get_preferences(user["id"])

    if not prefs:
        await update.message.reply_text(t("no_preferences", "en"))
        return

    text = svc.format_preferences_list(prefs)
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=preference_list_keyboard(prefs),
    )


async def preference_edit_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    action = parts[1]

    if action == "list":
        db = await get_client()
        svc = BotService(db)
        tg = update.effective_user
        user = await svc.get_or_create_telegram_user(tg.id, tg.username, tg.full_name)
        prefs = await svc.get_preferences(user["id"])
        text = svc.format_preferences_list(prefs)
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN,
                                      reply_markup=preference_list_keyboard(prefs))

    elif action == "edit":
        pref_id = parts[2]
        db = await get_client()
        svc = BotService(db)
        user, _ = await _get_user(update, ctx)
        prefs = await svc.get_preferences(user["id"])
        pref = next((p for p in prefs if p["id"] == pref_id), None)
        if pref:
            await query.edit_message_text(
                t("preference_edit_menu", "en", name=pref["name"]),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=preference_edit_keyboard(pref_id),
            )

    elif action == "add":
        await query.edit_message_text("Use /add to create a new alert.")


# ── Conversation states for preference editing ────────────────────────────────
(PEDIT_KEYWORDS, PEDIT_PRICE, PEDIT_CATEGORIES) = range(100, 103)


async def preference_edit_action(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")  # "pedit:delete:pref_id" / "pedit:keywords:pref_id"
    action = parts[1]
    pref_id = parts[2]

    db = await get_client()
    svc = BotService(db)

    if action == "delete":
        user, _ = await _get_user(update, ctx)
        prefs = await svc.get_preferences(user["id"])
        pref = next((p for p in prefs if p["id"] == pref_id), None)
        name = pref["name"] if pref else "?"
        await svc.delete_preference(pref_id)
        await query.edit_message_text(t("preference_deleted", "en", name=name))
        return ConversationHandler.END

    elif action == "keywords":
        ctx.user_data["_edit_pref_id"] = pref_id
        await query.edit_message_text(
            "Enter new keywords (comma-separated), or /skip to keep current:"
        )
        return PEDIT_KEYWORDS

    elif action == "price":
        ctx.user_data["_edit_pref_id"] = pref_id
        await query.edit_message_text(
            "Choose a new price range:", reply_markup=price_keyboard()
        )
        return PEDIT_PRICE

    elif action == "categories":
        ctx.user_data["_edit_pref_id"] = pref_id
        # Load current categories to show checked state
        user, _ = await _get_user(update, ctx)
        prefs = await svc.get_preferences(user["id"])
        pref = next((p for p in prefs if p["id"] == pref_id), None)
        current_cats = set(pref.get("categories") or []) if pref else set()
        ctx.user_data["_edit_cats"] = current_cats
        await query.edit_message_text(
            "Choose categories:", reply_markup=categories_keyboard(current_cats)
        )
        return PEDIT_CATEGORIES

    return ConversationHandler.END


async def pedit_keywords_received(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    pref_id = ctx.user_data.get("_edit_pref_id")
    keywords = [k.strip() for k in update.message.text.strip().split(",") if k.strip()]
    db = await get_client()
    await db.table("preferences").update({"keywords": keywords}).eq("id", pref_id).execute()
    await update.message.reply_text(f"Keywords updated: {', '.join(keywords)}")
    return ConversationHandler.END


async def pedit_keywords_skip(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Keywords unchanged.")
    return ConversationHandler.END


async def pedit_price_chosen(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    pref_id = ctx.user_data.get("_edit_pref_id")
    parts = query.data.split(":")

    if parts[1] == "custom":
        ctx.user_data["_edit_price_step"] = "min"
        await query.edit_message_text(t("enter_price_min", "en"))
        return PEDIT_PRICE

    if parts[1] == "any":
        price_min, price_max = None, None
    else:
        price_min = float(parts[1]) if float(parts[1]) > 0 else None
        price_max = float(parts[2])

    db = await get_client()
    await db.table("preferences").update({
        "price_min": price_min,
        "price_max": price_max,
    }).eq("id", pref_id).execute()

    price_str = f"up to ${int(price_max)}" if price_max else "any price"
    await query.edit_message_text(f"Price range updated: {price_str}")
    return ConversationHandler.END


async def pedit_price_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles both min and max text input for custom price editing."""
    step = ctx.user_data.get("_edit_price_step", "min")
    try:
        val = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(t("error_generic", "en"))
        return PEDIT_PRICE

    if step == "min":
        ctx.user_data["_edit_price_min"] = val if val > 0 else None
        ctx.user_data["_edit_price_step"] = "max"
        await update.message.reply_text(t("enter_price_max", "en"))
        return PEDIT_PRICE
    else:
        price_max = val if val > 0 else None
        price_min = ctx.user_data.pop("_edit_price_min", None)
        ctx.user_data.pop("_edit_price_step", None)
        pref_id = ctx.user_data.get("_edit_pref_id")
        db = await get_client()
        await db.table("preferences").update({
            "price_min": price_min,
            "price_max": price_max,
        }).eq("id", pref_id).execute()
        price_str = f"up to ${int(price_max)}" if price_max else "any price"
        await update.message.reply_text(f"Price range updated: {price_str}")
        return ConversationHandler.END


async def pedit_category_toggle(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    cat = query.data.split(":")[1]
    pref_id = ctx.user_data.get("_edit_pref_id")

    if cat == "done":
        cats = ctx.user_data.get("_edit_cats", set())
        if not cats:
            await query.answer("Select at least one category!", show_alert=True)
            return PEDIT_CATEGORIES
        db = await get_client()
        await db.table("preferences").update({"categories": list(cats)}).eq("id", pref_id).execute()
        await query.edit_message_text(f"Categories updated: {', '.join(sorted(cats))}")
        return ConversationHandler.END

    cats = ctx.user_data.setdefault("_edit_cats", set())
    if cat in cats:
        cats.discard(cat)
    else:
        cats.add(cat)
    await query.edit_message_reply_markup(categories_keyboard(cats))
    return PEDIT_CATEGORIES


async def pedit_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Edit cancelled.")
    return ConversationHandler.END


# ── /setup ────────────────────────────────────────────────────────────────────

async def setup_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user, svc = await _get_user(update, ctx)
    from pokefinder.db import queries as q
    db = await get_client()
    token = await q.create_setup_token(db, user["id"])
    url = f"{settings.base_url.rstrip('/')}/setup?token={token}"
    await update.message.reply_text(
        t("setup_prompt", "en", url=url),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


# ── /status ───────────────────────────────────────────────────────────────────

async def status_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user, svc = await _get_user(update, ctx)
    pref_count = await svc.count_active_preferences(user["id"])
    text = svc.format_status_message(user, pref_count)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ── /subscribe ────────────────────────────────────────────────────────────────

async def subscribe_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user, svc = await _get_user(update, ctx)

    if svc.is_subscribed(user):
        expires = user.get("subscription_expires_at", "")
        await update.message.reply_text(t("already_subscribed", "en", expires=expires))
        return

    url = svc.generate_checkout_url(user)
    await update.message.reply_text(
        t("subscribe_prompt", "en", checkout_url=url),
        parse_mode=ParseMode.MARKDOWN,
    )


# ── /help ─────────────────────────────────────────────────────────────────────

async def help_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(t("help_text", "en"), parse_mode=ParseMode.MARKDOWN)


# ── Admin commands ────────────────────────────────────────────────────────────

async def admin_stats_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update):
        await update.message.reply_text(t("admin_only", "en"))
        return

    db = await get_client()
    users = await queries.get_all_active_users(db)
    subscribed = sum(1 for u in users if u.get("is_subscribed"))
    notifs_today = await queries.count_notifications_today(db)
    prefs = await queries.get_all_active_preferences(db)

    runs = await queries.get_recent_scrape_runs(db, limit=2)
    ebay_status = "✅" if any(r["platform"] == "ebay" and r["status"] == "completed" for r in runs) else "⚠️"

    await update.message.reply_text(
        t("admin_stats", "en",
          users=len(users), subscribed=subscribed,
          notifs_today=notifs_today, prefs=len(prefs),
          ebay_status=ebay_status),
        parse_mode=ParseMode.MARKDOWN,
    )


async def admin_health_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update):
        await update.message.reply_text(t("admin_only", "en"))
        return

    db = await get_client()
    runs = await queries.get_recent_scrape_runs(db, limit=10)
    if not runs:
        await update.message.reply_text("No scrape runs recorded yet.")
        return

    lines = []
    for r in runs:
        status_emoji = {"completed": "✅", "failed": "❌", "running": "🔄"}.get(r["status"], "?")
        duration = f"{r['duration_ms']}ms" if r.get("duration_ms") else "-"
        lines.append(f"{status_emoji} {r['platform']} | +{r['new_listings']} new | {duration}")

    await update.message.reply_text(
        t("admin_health", "en", runs="\n".join(lines)),
        parse_mode=ParseMode.MARKDOWN,
    )


# ── Register all handlers ─────────────────────────────────────────────────────

def register_handlers(app) -> None:
    app.add_handler(CommandHandler("preferences", preferences_command))
    app.add_handler(CommandHandler("setup", setup_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("subscribe", subscribe_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("admin_stats", admin_stats_command))
    app.add_handler(CommandHandler("admin_health", admin_health_command))
    app.add_handler(CallbackQueryHandler(preference_edit_callback, pattern="^pref:"))

    # Preference editing conversation
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(preference_edit_action, pattern="^pedit:")],
        states={
            PEDIT_KEYWORDS: [
                CommandHandler("skip", pedit_keywords_skip),
                MessageHandler(filters.TEXT & ~filters.COMMAND, pedit_keywords_received),
            ],
            PEDIT_PRICE: [
                CallbackQueryHandler(pedit_price_chosen, pattern="^price:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, pedit_price_text),
            ],
            PEDIT_CATEGORIES: [
                CallbackQueryHandler(pedit_category_toggle, pattern="^cat:"),
            ],
        },
        fallbacks=[CommandHandler("cancel", pedit_cancel)],
        allow_reentry=True,
        per_message=False,
    ))

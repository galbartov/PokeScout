"""Inline keyboard builders for Telegram bot."""
from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from pokefinder.i18n import t


def categories_keyboard(selected: set[str]) -> InlineKeyboardMarkup:
    cats = [
        ("sealed",  t("category_sealed", "en")),
        ("singles", t("category_singles", "en")),
        ("graded",  t("category_graded", "en")),
        ("bulk",    t("category_bulk", "en")),
    ]
    rows = []
    for cat_id, label in cats:
        check = "✅ " if cat_id in selected else ""
        rows.append([InlineKeyboardButton(f"{check}{label}", callback_data=f"cat:{cat_id}")])
    rows.append([InlineKeyboardButton("✅ Done", callback_data="cat:done")])
    return InlineKeyboardMarkup(rows)


def price_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Up to $25",  callback_data="price:0:25")],
        [InlineKeyboardButton("Up to $50",  callback_data="price:0:50")],
        [InlineKeyboardButton("Up to $100", callback_data="price:0:100")],
        [InlineKeyboardButton("Up to $250", callback_data="price:0:250")],
        [InlineKeyboardButton("Any price",  callback_data="price:any")],
        [InlineKeyboardButton("Custom",     callback_data="price:custom")],
    ])


def preference_list_keyboard(prefs: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for pref in prefs:
        rows.append([InlineKeyboardButton(
            f"✏️ {pref['name']}",
            callback_data=f"pref:edit:{pref['id']}",
        )])
    rows.append([InlineKeyboardButton("➕ Add preference", callback_data="pref:add")])
    return InlineKeyboardMarkup(rows)


def preference_edit_keyboard(pref_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("edit_keywords", "en"),   callback_data=f"pedit:keywords:{pref_id}")],
        [InlineKeyboardButton(t("edit_price", "en"),      callback_data=f"pedit:price:{pref_id}")],
        [InlineKeyboardButton(t("edit_categories", "en"), callback_data=f"pedit:categories:{pref_id}")],
        [InlineKeyboardButton(t("delete_preference", "en"), callback_data=f"pedit:delete:{pref_id}")],
        [InlineKeyboardButton(t("back", "en"),            callback_data="pref:list")],
    ])


def presets_keyboard(
    presets_with_prices: list[tuple[dict, float | None]],
    selected_categories: set[str],
) -> InlineKeyboardMarkup:
    rows = []
    cat_order = ["sealed", "singles", "graded", "bulk"]
    show_headers = len(selected_categories) > 1

    if show_headers:
        for cat in cat_order:
            if cat not in selected_categories:
                continue
            cat_presets = [(p, price) for p, price in presets_with_prices if cat in p["categories"]]
            if not cat_presets:
                continue
            rows.append([InlineKeyboardButton(
                f"── {t(f'category_{cat}', 'en')} ──", callback_data="preset:_header"
            )])
            for preset, price in cat_presets:
                price_str = f" (up to ${int(price):,})" if price is not None else ""
                rows.append([InlineKeyboardButton(
                    f"{preset['name_en']}{price_str}",
                    callback_data=f"preset:{preset['id']}",
                )])
    else:
        for preset, price in presets_with_prices:
            price_str = f" (up to ${int(price):,})" if price is not None else ""
            rows.append([InlineKeyboardButton(
                f"{preset['name_en']}{price_str}",
                callback_data=f"preset:{preset['id']}",
            )])

    rows.append([InlineKeyboardButton(t("preset_custom", "en"), callback_data="preset:custom")])
    rows.append([InlineKeyboardButton(t("preset_skip", "en"),   callback_data="preset:skip")])
    return InlineKeyboardMarkup(rows)


def product_selection_keyboard(results: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for i, _ in enumerate(results, 1):
        rows.append([InlineKeyboardButton(str(i), callback_data=f"product:{i-1}")])
    rows.append([InlineKeyboardButton("⏭️ Skip", callback_data="product:skip")])
    return InlineKeyboardMarkup(rows)


# ── Search-first /add flow keyboards ──────────────────────────────────────────

def _snap(v: float) -> int:
    """Round a price to the nearest clean number for display."""
    if v < 20:   return max(1, round(v))
    if v < 100:  return round(v / 5) * 5
    if v < 500:  return round(v / 10) * 10
    return round(v / 50) * 50


def market_price_keyboard(last_sold: float | None, prefix: str, back: str | None = None) -> InlineKeyboardMarkup:
    """
    Build price tier buttons relative to a known eBay market price.
    Falls back to generic tiers if no price is available.
    `prefix` controls callback_data (e.g. 'br_price' or 'sa_price').
    `back` is an optional callback_data string for a Back button.
    """
    if last_sold and last_sold > 0:
        t1 = _snap(last_sold * 0.8)
        t2 = _snap(last_sold * 1.0)
        t3 = _snap(last_sold * 1.2)
        rows = [
            [InlineKeyboardButton(f"Up to ${t1}",           callback_data=f"{prefix}:0:{t1}")],
            [InlineKeyboardButton(f"Up to ${t2} (market)",  callback_data=f"{prefix}:0:{t2}")],
            [InlineKeyboardButton(f"Up to ${t3}",           callback_data=f"{prefix}:0:{t3}")],
            [InlineKeyboardButton("Any price",              callback_data=f"{prefix}:any")],
            [InlineKeyboardButton("Custom",                 callback_data=f"{prefix}:custom")],
        ]
    else:
        rows = [
            [InlineKeyboardButton("Up to $25",  callback_data=f"{prefix}:0:25")],
            [InlineKeyboardButton("Up to $50",  callback_data=f"{prefix}:0:50")],
            [InlineKeyboardButton("Up to $100", callback_data=f"{prefix}:0:100")],
            [InlineKeyboardButton("Up to $250", callback_data=f"{prefix}:0:250")],
            [InlineKeyboardButton("Any price",  callback_data=f"{prefix}:any")],
            [InlineKeyboardButton("Custom",     callback_data=f"{prefix}:custom")],
        ]
    if back:
        rows.append([InlineKeyboardButton("← Back", callback_data=back)])
    return InlineKeyboardMarkup(rows)


_SA_PAGE_SIZE = 5


def search_results_keyboard(results: list[dict], query: str, page: int = 0) -> InlineKeyboardMarkup:
    """
    Numbered pick buttons (1–5) for the search-first /add flow.
    Shown below a photo album so the user taps the number matching the card they want.
    """
    start = page * _SA_PAGE_SIZE
    chunk = results[start: start + _SA_PAGE_SIZE]

    # Single row of number buttons: 1 2 3 4 5
    number_row = [
        InlineKeyboardButton(str(i + 1), callback_data=f"sa_pick:{start + i}")
        for i in range(len(chunk))
    ]
    rows = [number_row]

    # Pagination nav
    total_pages = -(-len(results) // _SA_PAGE_SIZE)
    if total_pages > 1:
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"sa_page:{page-1}"))
        nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="sa_noop"))
        if start + _SA_PAGE_SIZE < len(results):
            nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"sa_page:{page+1}"))
        rows.append(nav)

    rows.append([InlineKeyboardButton(
        f'🔍 Use "{query[:30]}" as keyword alert', callback_data="sa_keyword"
    )])
    return InlineKeyboardMarkup(rows)


def keyword_fallback_keyboard(query: str) -> InlineKeyboardMarkup:
    """Shown when search returns no results."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f'🔍 Alert for "{query[:30]}"', callback_data="sa_keyword"
        )],
        [InlineKeyboardButton("🔄 Try different search", callback_data="sa_retry")],
    ])

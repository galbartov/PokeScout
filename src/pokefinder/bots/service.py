"""
BotService — shared logic for both Telegram and WhatsApp bots.
Handles user/preference CRUD, subscription checks, and message formatting.
"""
from __future__ import annotations

from supabase import AsyncClient

from pokefinder.config import settings
from pokefinder.db import queries
from pokefinder.i18n import t

SUBSCRIPTION_PRICE_USD = 9.99
FREE_PREF_LIMIT = 10
PRO_PREF_LIMIT = 50


class BotService:
    def __init__(self, db: AsyncClient) -> None:
        self.db = db

    # ── User management ───────────────────────────────────────────────────────

    async def get_or_create_telegram_user(
        self,
        telegram_id: int,
        username: str | None,
        display_name: str | None,
    ) -> dict:
        user = await queries.get_user_by_telegram(self.db, telegram_id)
        if user:
            return user
        return await queries.upsert_user(self.db, {
            "telegram_id": telegram_id,
            "telegram_username": username,
            "display_name": display_name,
            "locale": "en",
            "notification_channels": ["telegram"],
        })

    async def get_or_create_whatsapp_user(self, phone: str, display_name: str | None) -> dict:
        user = await queries.get_user_by_whatsapp(self.db, phone)
        if user:
            return user
        return await queries.upsert_user(self.db, {
            "whatsapp_phone": phone,
            "display_name": display_name,
            "locale": "en",
            "notification_channels": ["whatsapp"],
        })

    async def set_locale(self, user_id: str, locale: str) -> None:
        await queries.update_user(self.db, user_id, {"locale": locale})

    async def set_location(
        self, user_id: str, lat: float, lon: float, name: str
    ) -> None:
        await queries.update_user(self.db, user_id, {
            "location_lat": lat,
            "location_lon": lon,
            "location_name": name,
        })

    # ── Preferences ───────────────────────────────────────────────────────────

    async def get_preferences(self, user_id: str) -> list[dict]:
        return await queries.get_preferences(self.db, user_id)

    async def find_duplicate_preference(self, user_id: str, pref_data: dict) -> dict | None:
        """Return an existing preference that is effectively identical to pref_data, or None."""
        existing = await queries.get_preferences(self.db, user_id)
        new_tcg_id = pref_data.get("tcg_product_id")
        new_keywords = set(k.lower() for k in (pref_data.get("keywords") or []))
        new_cats = set(pref_data.get("categories") or [])

        for p in existing:
            # Exact TCG product ID match (from /browse or /sealed)
            if new_tcg_id and p.get("tcg_product_id") == new_tcg_id:
                return p
            # Same keyword set + same categories
            p_keywords = set(k.lower() for k in (p.get("keywords") or []))
            p_cats = set(p.get("categories") or [])
            if new_keywords and new_keywords == p_keywords and new_cats == p_cats:
                return p
        return None

    def preference_limit(self, user: dict) -> int:
        return PRO_PREF_LIMIT if self.is_subscribed(user) else FREE_PREF_LIMIT

    async def can_add_preference(self, user: dict) -> tuple[bool, int, int]:
        """Returns (allowed, current_count, limit). Cap disabled for now."""
        current = len(await queries.get_preferences(self.db, user["id"]))
        limit = self.preference_limit(user)
        return True, current, limit

    async def add_preference(self, user_id: str, pref_data: dict) -> dict:
        data = {"user_id": user_id, **pref_data}
        return await queries.create_preference(self.db, data)

    async def update_preference(self, pref_id: str, pref_data: dict) -> dict:
        return await queries.update_preference(self.db, pref_id, pref_data)

    async def delete_preference(self, pref_id: str) -> None:
        await queries.delete_preference(self.db, pref_id)

    async def count_active_preferences(self, user_id: str) -> int:
        return len(await self.get_preferences(user_id))

    # ── Subscription ─────────────────────────────────────────────────────────

    def is_subscribed(self, user: dict) -> bool:
        from datetime import datetime, timezone
        if not user.get("is_subscribed"):
            return False
        expires = user.get("subscription_expires_at")
        if not expires:
            return True
        if isinstance(expires, str):
            from datetime import datetime
            expires_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
            return expires_dt > datetime.now(timezone.utc)
        return True

    def free_deals_remaining(self, user: dict) -> int:
        used = user.get("free_deals_used", 0)
        return max(0, settings.free_deals_limit - used)

    def can_receive_notification(self, user: dict) -> bool:
        return self.is_subscribed(user) or self.free_deals_remaining(user) > 0

    async def increment_free_deals(self, user_id: str, current_used: int) -> None:
        await queries.update_user(self.db, user_id, {"free_deals_used": current_used + 1})

    def generate_checkout_url(self, user: dict, locale: str = "en") -> str:
        """Return the Paddle checkout URL with user_id embedded."""
        user_id = user.get("id", "")
        return f"https://tcg-scout.com/subscribe?user_id={user_id}"

    # ── Message formatting ────────────────────────────────────────────────────

    def format_deal_message(
        self,
        listing: dict,
        preference_name: str,
        market_price: float | None = None,
        market_price_source: str | None = None,
    ) -> str:
        """Format a deal notification message for Telegram (Markdown-safe)."""
        price = listing.get("price")
        price_str = f"{price:,.2f}" if price else "?"
        platform = listing.get("platform", "")
        platform_name = {"ebay": "eBay", "tcgplayer": "TCGPlayer"}.get(platform, platform)

        # Escape chars that break Telegram MarkdownV1: _ * ` [
        def esc(s: str) -> str:
            return s.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`").replace("[", "\\[")

        title = esc(listing.get("title", ""))
        pref = esc(preference_name)
        url = listing.get("url", "")

        buying_format = listing.get("buying_format", "FIXED_PRICE")
        format_tag = "🔨 Auction" if buying_format == "AUCTION" else "🏷 Buy It Now"

        # ── Deal quality: discount vs market price ────────────────────────
        discount_line = ""
        if market_price and price and market_price > 0:
            pct = ((market_price - price) / market_price) * 100
            source_tag = f" · {market_price_source}" if market_price_source else ""
            if pct >= 5:
                discount_line = f"📉 *{pct:.0f}% below market* (~${market_price:,.0f}{source_tag})\n"
            elif pct <= -5:
                discount_line = f"📈 {abs(pct):.0f}% above market (~${market_price:,.0f}{source_tag})\n"

        # ── Condition ────────────────────────────────────────────────────
        condition = listing.get("condition")
        condition_line = f"🏷 Condition: {condition}\n" if condition else ""

        # ── Shipping ─────────────────────────────────────────────────────
        shipping_cost = listing.get("shipping_cost")
        if shipping_cost is None:
            shipping_line = ""
        elif shipping_cost == 0.0:
            shipping_line = "📦 Free shipping\n"
        else:
            shipping_line = f"📦 Shipping: +${shipping_cost:,.2f}\n"

        # ── Seller trust ─────────────────────────────────────────────────
        feedback_score = listing.get("seller_feedback_score")
        feedback_pct = listing.get("seller_feedback_pct")
        if feedback_pct is not None and feedback_score is not None:
            pct_str = f"{feedback_pct:.1f}%".rstrip("0").rstrip(".")
            if feedback_pct < 97:
                seller_line = f"⚠️ Seller: {feedback_score} ({pct_str} feedback)\n"
            else:
                seller_line = f"✅ Seller: {feedback_score} ({pct_str} feedback)\n"
        elif feedback_score is not None:
            seller_line = f"✅ Seller: {feedback_score} feedback\n"
        else:
            seller_line = ""

        # ── Country ──────────────────────────────────────────────────────
        country = listing.get("seller_country")
        country_line = f"🌍 Ships from: {country}\n" if country else ""

        return (
            f"🔔 *New Deal Found*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📦 {title}\n\n"
            f"💰 *${price_str}*  {format_tag} · {platform_name}\n"
            f"{discount_line}"
            f"{condition_line}"
            f"{shipping_line}"
            f"{seller_line}"
            f"{country_line}"
            f"\n🔗 [View on {platform_name}]({url})\n\n"
            f"🏷 Alert: _{pref}_"
        )

    def format_status_message(self, user: dict, pref_count: int) -> str:
        if self.is_subscribed(user):
            expires = user.get("subscription_expires_at", "")
            if expires:
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
                    expires = dt.strftime("%Y-%m-%d")
                except Exception:
                    pass
            return t("status_subscribed", locale="en", expires=expires, pref_count=pref_count)
        else:
            free_left = self.free_deals_remaining(user)
            return t(
                "status_free",
                locale="en",
                free_left=free_left,
                free_limit=settings.free_deals_limit,
                pref_count=pref_count,
            )

    def format_preferences_list(self, prefs: list[dict]) -> str:
        if not prefs:
            return t("no_preferences", locale="en")
        lines = []
        for i, pref in enumerate(prefs, 1):
            name = pref.get("name", f"#{i}")
            cats = pref.get("categories") or []
            price_min = pref.get("price_min")
            price_max = pref.get("price_max")
            price_str = ""
            if price_min and price_max:
                price_str = f" | ${price_min:.0f}–${price_max:.0f}"
            elif price_max:
                price_str = f" | up to ${price_max:.0f}"
            cat_str = ", ".join(cats) if cats else ""
            lines.append(f"{i}. *{name}*{price_str}")
            if cat_str:
                lines.append(f"   {cat_str}")
        list_text = "\n".join(lines)
        return t("preferences_list", locale="en", list=list_text)

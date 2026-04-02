"""Reusable database query helpers."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from supabase import AsyncClient


# ── Users ────────────────────────────────────────────────────────────────────

async def get_user_by_telegram(db: AsyncClient, telegram_id: int) -> dict | None:
    res = await db.table("users").select("*").eq("telegram_id", telegram_id).execute()
    return res.data[0] if res.data else None


async def get_user_by_whatsapp(db: AsyncClient, phone: str) -> dict | None:
    res = await db.table("users").select("*").eq("whatsapp_phone", phone).execute()
    return res.data[0] if res.data else None


async def upsert_user(db: AsyncClient, data: dict) -> dict:
    res = await db.table("users").upsert(data, on_conflict="telegram_id").execute()
    return res.data[0]


async def update_user(db: AsyncClient, user_id: str, data: dict) -> dict:
    res = await db.table("users").update(data).eq("id", user_id).execute()
    return res.data[0]


async def get_all_active_users(db: AsyncClient) -> list[dict]:
    res = await db.table("users").select("*").eq("is_active", True).execute()
    return res.data


# ── Preferences ──────────────────────────────────────────────────────────────

async def get_preferences(db: AsyncClient, user_id: str) -> list[dict]:
    res = (
        await db.table("preferences")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .order("created_at")
        .execute()
    )
    return res.data


async def get_all_active_preferences(db: AsyncClient) -> list[dict]:
    res = await db.table("preferences").select("*, users(*)").eq("is_active", True).execute()
    return res.data


async def create_preference(db: AsyncClient, data: dict) -> dict:
    res = await db.table("preferences").insert(data).execute()
    return res.data[0]


async def update_preference(db: AsyncClient, pref_id: str, data: dict) -> dict:
    res = await db.table("preferences").update(data).eq("id", pref_id).execute()
    return res.data[0]


async def delete_preference(db: AsyncClient, pref_id: str) -> None:
    await db.table("preferences").update({"is_active": False}).eq("id", pref_id).execute()


# ── Listings ─────────────────────────────────────────────────────────────────

async def listing_exists(db: AsyncClient, platform: str, external_id: str) -> bool:
    res = (
        await db.table("listings")
        .select("id")
        .eq("platform", platform)
        .eq("external_id", external_id)
        .execute()
    )
    return bool(res.data)


async def insert_listing(db: AsyncClient, data: dict) -> dict:
    res = await db.table("listings").insert(data).execute()
    return res.data[0]


async def insert_listings_batch(db: AsyncClient, records: list[dict]) -> list[str]:
    """Insert multiple listings in one request. Returns list of inserted IDs."""
    if not records:
        return []
    res = await db.table("listings").insert(records).execute()
    return [r["id"] for r in res.data]


async def get_recent_listings_hashes(db: AsyncClient, days: int = 7) -> list[str]:
    """Return image hashes from the last N days for dedup checking."""
    from datetime import datetime, timezone, timedelta
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    res = await (
        db.table("listings")
        .select("image_hash")
        .not_.is_("image_hash", "null")
        .gte("scraped_at", since)
        .execute()
    )
    return [r["image_hash"] for r in res.data]


async def get_recent_normalized_titles(db: AsyncClient, days: int = 7) -> list[dict]:
    from datetime import datetime, timezone, timedelta
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    res = await (
        db.table("listings")
        .select("id, title_normalized, price")
        .gte("scraped_at", since)
        .execute()
    )
    return res.data


# ── Notifications ─────────────────────────────────────────────────────────────

async def notification_exists(db: AsyncClient, user_id: str, listing_id: str) -> bool:
    res = (
        await db.table("notifications")
        .select("id")
        .eq("user_id", user_id)
        .eq("listing_id", listing_id)
        .execute()
    )
    return bool(res.data)


async def create_notification(db: AsyncClient, data: dict) -> dict:
    res = await db.table("notifications").insert(data).execute()
    return res.data[0]


async def count_notifications_today(db: AsyncClient) -> int:
    from datetime import datetime, timezone, timedelta
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    res = (
        await db.table("notifications")
        .select("id", count="exact")
        .gte("sent_at", since)
        .execute()
    )
    return res.count or 0


# ── Scrape Runs ───────────────────────────────────────────────────────────────

async def start_scrape_run(db: AsyncClient, platform: str) -> str:
    res = await db.table("scrape_runs").insert({"platform": platform, "status": "running"}).execute()
    return res.data[0]["id"]


async def finish_scrape_run(
    db: AsyncClient,
    run_id: str,
    *,
    status: str,
    listings_found: int,
    new_listings: int,
    duration_ms: int,
    error_message: str | None = None,
) -> None:
    await db.table("scrape_runs").update({
        "status": status,
        "listings_found": listings_found,
        "new_listings": new_listings,
        "duration_ms": duration_ms,
        "error_message": error_message,
        "completed_at": "now()",
    }).eq("id", run_id).execute()


async def get_recent_scrape_runs(db: AsyncClient, limit: int = 10) -> list[dict]:
    res = (
        await db.table("scrape_runs")
        .select("*")
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data


# ── TCG Products Cache ────────────────────────────────────────────────────────

async def get_cached_product(db: AsyncClient, product_id: str) -> dict | None:
    res = await db.table("tcg_products_cache").select("*").eq("id", product_id).execute()
    return res.data[0] if res.data else None


async def upsert_cached_product(db: AsyncClient, data: dict) -> None:
    await db.table("tcg_products_cache").upsert(data, on_conflict="id").execute()


# ── Setup Tokens ──────────────────────────────────────────────────────────────

async def create_setup_token(db: AsyncClient, user_id: str) -> str:
    """Generate a 15-minute single-use token for the web setup page."""
    from datetime import datetime, timezone, timedelta
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
    res = await db.table("setup_tokens").insert({
        "user_id": user_id,
        "expires_at": expires_at,
    }).execute()
    return res.data[0]["token"]


async def get_setup_token(db: AsyncClient, token: str) -> dict | None:
    """Return token row if it exists, regardless of validity."""
    res = await db.table("setup_tokens").select("*").eq("token", token).execute()
    return res.data[0] if res.data else None


async def mark_token_used(db: AsyncClient, token: str) -> None:
    await db.table("setup_tokens").update({"used": True}).eq("token", token).execute()

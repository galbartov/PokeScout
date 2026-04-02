from functools import lru_cache

from supabase import AsyncClient, acreate_client

from pokefinder.config import settings

_client: AsyncClient | None = None


async def get_client() -> AsyncClient:
    global _client
    if _client is None:
        _client = await acreate_client(settings.supabase_url, settings.supabase_service_role_key)
    return _client

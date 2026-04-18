import logging

from supabase import AsyncClient, acreate_client

from lib.config import get_config

logger = logging.getLogger(__name__)


# ── Anon client (public, respects RLS) ───────────────────────────────────────
_anon_client: AsyncClient | None = None

async def get_supabase() -> AsyncClient:
    global _anon_client
    if _anon_client is None:
        cfg = get_config()
        _anon_client = await acreate_client(cfg.supabase_url, cfg.supabase_anon_key)
        logger.debug("Supabase anon client initialised")
    return _anon_client


# ── Service-role client (server-only, bypasses RLS) ──────────────────────────
_service_client: AsyncClient | None = None

async def get_supabase_admin() -> AsyncClient:
    """
    Use for server-side operations that need to bypass RLS.
    Never expose this client to browser requests directly.
    """
    global _service_client
    if _service_client is None:
        cfg = get_config()
        _service_client = await acreate_client(cfg.supabase_url, cfg.supabase_service_key)
        logger.debug("Supabase admin client initialised")
    return _service_client

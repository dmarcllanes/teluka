"""
Two-layer cache: Redis (shared across all workers) → in-memory (per-process).

If REDIS_URL is set: reads hit Redis first, writes go to both.
If REDIS_URL is not set: falls back to in-memory only (zero extra cost).

Upstash Redis free tier: 10k commands/day — enough for ~2,500 page loads/day.
"""
import asyncio
import logging
import pickle
import time
from typing import Any

logger = logging.getLogger(__name__)

# ── TTL constants (seconds) ───────────────────────────────────────────────────
TTL_USER     = 30   # user profile rows
TTL_TX_LIST  = 10   # per-user transaction list
TTL_SELLER   = 60   # seller lookup by phone
TTL_ACTIVITY = 3    # activity feed per deal
TTL_LANDING  = 60   # landing page rendered HTML


# ── In-memory layer (always present, synchronous, per-process) ────────────────

class _MemCache:
    __slots__ = ("_store",)

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if not entry:
            return None
        value, exp = entry
        if time.monotonic() > exp:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: float) -> None:
        self._store[key] = (value, time.monotonic() + ttl)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def delete_prefix(self, prefix: str) -> None:
        for k in list(self._store):
            if k.startswith(prefix):
                del self._store[k]

    def size(self) -> int:
        return len(self._store)


_mem: _MemCache = _MemCache()

# Backwards-compat alias (landing page uses sync cache.get/set)
cache = _mem


# ── Redis layer (optional, shared across workers) ─────────────────────────────

_redis = None   # set by init_redis()


async def init_redis(url: str) -> None:
    """Call once at startup when REDIS_URL is configured."""
    global _redis
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(
            url,
            decode_responses=False,
            socket_timeout=2,
            socket_connect_timeout=2,
        )
        await client.ping()
        _redis = client
        logger.info("Redis cache connected url=...%s", url.split("@")[-1] if "@" in url else url[-20:])
    except Exception as exc:
        logger.warning("Redis unavailable (%s) — using in-memory cache only", exc)
        _redis = None


# ── Async cache API (use these in route handlers) ─────────────────────────────

async def aget(key: str) -> Any | None:
    """Check in-memory first, then Redis on miss."""
    local = _mem.get(key)
    if local is not None:
        return local
    if _redis:
        try:
            raw = await _redis.get(key)
            if raw:
                value = pickle.loads(raw)
                _mem.set(key, value, TTL_USER)   # warm local cache
                return value
        except Exception as exc:
            logger.debug("Redis get failed: %s", exc)
    return None


async def aset(key: str, value: Any, ttl: float) -> None:
    """Write to in-memory and Redis."""
    _mem.set(key, value, ttl)
    if _redis:
        try:
            await _redis.setex(key, max(1, int(ttl)), pickle.dumps(value))
        except Exception as exc:
            logger.debug("Redis set failed: %s", exc)


async def adelete(key: str) -> None:
    """Invalidate in both layers."""
    _mem.delete(key)
    if _redis:
        try:
            await _redis.delete(key)
        except Exception as exc:
            logger.debug("Redis delete failed: %s", exc)


async def adelete_prefix(prefix: str) -> None:
    _mem.delete_prefix(prefix)
    if _redis:
        try:
            keys = await _redis.keys(f"{prefix}*")
            if keys:
                await _redis.delete(*keys)
        except Exception as exc:
            logger.debug("Redis delete_prefix failed: %s", exc)

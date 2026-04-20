"""
arq async job queue — decouples slow I/O (email, SMS) from the request path.

If REDIS_URL is set: jobs are enqueued in Redis and processed by the worker.
If REDIS_URL is not set: falls back to calling the function directly (dev mode).

Run the worker alongside the web process:
  python worker.py

Upstash free tier handles this easily — same Redis instance as the cache.
"""
import logging

from lib.config import get_config

logger = logging.getLogger(__name__)

_pool = None   # arq connection pool, initialised lazily


async def _get_pool():
    global _pool
    if _pool is not None:
        return _pool
    cfg = get_config()
    if not cfg.redis_url:
        return None
    try:
        from arq import create_pool
        from arq.connections import RedisSettings
        _pool = await create_pool(RedisSettings.from_dsn(cfg.redis_url))
        logger.info("arq job queue ready")
        return _pool
    except Exception as exc:
        logger.warning("arq pool unavailable (%s) — running jobs inline", exc)
        return None


# ── Job definitions (imported by the worker) ──────────────────────────────────

async def send_otp_email_job(ctx, to_email: str, code: str) -> bool:
    from lib.email_sender import send_otp_email
    return await send_otp_email(to_email, code)


class WorkerSettings:
    functions = [send_otp_email_job]
    max_jobs  = 10
    job_timeout = 30

    @classmethod
    def redis_settings(cls):
        from arq.connections import RedisSettings
        cfg = get_config()
        if cfg.redis_url:
            return RedisSettings.from_dsn(cfg.redis_url)
        return RedisSettings()   # localhost fallback


# ── Public API (use in route handlers) ────────────────────────────────────────

async def enqueue_send_otp(to_email: str, code: str) -> bool:
    """
    Enqueue OTP email delivery.
    Returns True immediately (fire-and-forget when Redis is available).
    Falls back to inline send if Redis is not configured.
    """
    pool = await _get_pool()
    if pool:
        try:
            await pool.enqueue_job("send_otp_email_job", to_email, code)
            logger.info("OTP email enqueued to=...%s", to_email.split("@")[-1])
            return True
        except Exception as exc:
            logger.error("arq enqueue failed (%s) — sending inline", exc)

    # Inline fallback
    from lib.email_sender import send_otp_email
    return await send_otp_email(to_email, code)

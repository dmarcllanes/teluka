"""
Web Push notification delivery via VAPID + pywebpush.

Setup:
  1. Install:  uv add pywebpush
  2. Generate keys (run once):
       python -c "from py_vapid import Vapid; v=Vapid(); v.generate_keys();
                  print('VAPID_PRIVATE_KEY='+v.private_pem().decode());
                  print('VAPID_PUBLIC_KEY='+v.public_key.decode())"
  3. Add VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY, VAPID_EMAIL to .env

Push is silently skipped when VAPID keys are not configured (dev/mock mode).
"""
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


def _send_sync(subscription: dict, payload: str, private_key: str, email: str) -> None:
    """Blocking call — must run in a thread."""
    from pywebpush import webpush, WebPushException
    webpush(
        subscription_info=subscription,
        data=payload,
        vapid_private_key=private_key,
        vapid_claims={"sub": f"mailto:{email}"},
    )


async def _send_one(subscription_row: dict, title: str, body: str, url: str,
                    private_key: str, email: str) -> bool:
    """Send to one subscription. Returns False if subscription is stale (410)."""
    payload = json.dumps({"title": title, "body": body, "url": url, "icon": "/static/icons/icon-192.png"})
    try:
        await asyncio.to_thread(
            _send_sync, subscription_row["subscription"], payload, private_key, email
        )
        return True
    except Exception as exc:
        resp = getattr(exc, "response", None)
        if resp is not None and getattr(resp, "status_code", 0) == 410:
            return False   # expired — caller will delete it
        logger.warning("Push send error endpoint=%s err=%s",
                       subscription_row.get("endpoint", "?")[:60], exc)
        return True  # keep the subscription — transient error


async def notify_user(user_id: str, title: str, body: str, url: str = "/dashboard") -> None:
    """
    Deliver a push notification to every registered browser for this user.
    Silently no-ops when VAPID is not configured.
    """
    from lib.config import get_config
    cfg = get_config()
    if not cfg.vapid_private_key or not cfg.vapid_public_key:
        return

    try:
        from lib.supabase_client import get_supabase_admin
        supabase = await get_supabase_admin()
        rows = (
            await supabase.table("push_subscriptions")
            .select("id, endpoint, subscription")
            .eq("user_id", user_id)
            .execute()
        ).data or []

        stale = []
        for row in rows:
            ok = await _send_one(row, title, body, url, cfg.vapid_private_key, cfg.vapid_email)
            if not ok:
                stale.append(row["id"])

        if stale:
            await supabase.table("push_subscriptions").delete().in_("id", stale).execute()
            logger.info("Removed %d stale push subscriptions for user=%s", len(stale), user_id)

    except Exception:
        logger.exception("notify_user failed user=%s", user_id)

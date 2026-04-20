"""
Transaction activity log — records every state change as a timestamped event.

In mock mode (MOCK_PAYMENTS=true) events live in an in-process dict so the
full interactive timeline works with zero DB changes.
In production, events are persisted to the `transaction_events` Supabase table.

Supabase schema (run once):
  CREATE TABLE transaction_events (
    id          uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    tx_id       text NOT NULL,
    event_type  text NOT NULL,
    actor_id    text,
    title       text NOT NULL,
    description text NOT NULL,
    icon        text NOT NULL DEFAULT '📋',
    created_at  timestamptz DEFAULT now()
  );
  CREATE INDEX ON transaction_events (tx_id, created_at DESC);
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import TypedDict

logger = logging.getLogger(__name__)

# ── In-memory store for mock/dev mode ────────────────────────────────────────
_mock_events: dict[str, list[dict]] = {}


class ActivityEvent(TypedDict):
    id: str
    tx_id: str
    event_type: str
    actor_id: str | None
    title: str
    description: str
    icon: str
    created_at: str   # ISO-8601
    actor_lat: float | None
    actor_lon: float | None


# ── Event type catalogue ──────────────────────────────────────────────────────

EVENT_TEMPLATES: dict[str, tuple[str, str]] = {
    # (icon, title template)
    "deal_created":          ("🤝", "Deal created"),
    "payment_held":          ("🔒", "Funds held securely"),
    "evidence_submitted":    ("📸", "Evidence photos submitted"),
    "item_shipped":          ("🚚", "Item marked as shipped"),
    "unboxing_uploaded":     ("🎥", "Unboxing video uploaded"),
    "payment_released":      ("✅", "Payment released to seller"),
    "dispute_raised":        ("⚠️", "Dispute raised"),
    "deal_cancelled":        ("❌", "Deal cancelled"),
    "deal_refunded":         ("↩️", "Funds refunded to buyer"),
    "liveness_passed":       ("🛡️", "Photo liveness verified"),
    "tier_upgraded":         ("🔒", "Security tier applied"),
}


# ── Public API ────────────────────────────────────────────────────────────────

async def log_event(
    tx_id: str,
    event_type: str,
    description: str,
    actor_id: str | None = None,
    icon: str | None = None,
    title: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> None:
    """Append one event to the activity log for a transaction."""
    from lib.config import get_config
    cfg = get_config()

    _icon, _title = EVENT_TEMPLATES.get(event_type, ("📋", event_type.replace("_", " ").title()))
    event: ActivityEvent = {
        "id":          str(uuid.uuid4()),
        "tx_id":       tx_id,
        "event_type":  event_type,
        "actor_id":    actor_id,
        "title":       title or _title,
        "description": description,
        "icon":        icon or _icon,
        "created_at":  datetime.now(timezone.utc).isoformat(),
        "actor_lat":   lat,
        "actor_lon":   lon,
    }

    if cfg.mock_payments:
        _mock_events.setdefault(tx_id, []).append(event)
        logger.info("[MOCK] Activity logged tx=%s type=%s", tx_id, event_type)
        return

    try:
        from lib.supabase_client import get_supabase_admin
        supabase = await get_supabase_admin()
        await supabase.table("transaction_events").insert(event).execute()
    except Exception:
        logger.exception("Failed to persist activity event tx=%s type=%s", tx_id, event_type)


async def get_events(tx_id: str, limit: int = 30) -> list[ActivityEvent]:
    """Return events for a transaction, newest first."""
    from lib.config import get_config
    cfg = get_config()

    if cfg.mock_payments:
        events = list(reversed(_mock_events.get(tx_id, [])))
        return events[:limit]

    try:
        from lib.supabase_client import get_supabase_admin
        supabase = await get_supabase_admin()
        rows = (
            await supabase.table("transaction_events")
            .select("*")
            .eq("tx_id", tx_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        ).data or []
        return rows  # type: ignore[return-value]
    except Exception:
        logger.exception("Failed to fetch activity events tx=%s", tx_id)
        return []


def format_relative_time(iso: str) -> str:
    """'just now', '3m ago', '2h ago', '4 Apr'"""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = int((now - dt).total_seconds())
        if diff < 60:
            return "just now"
        if diff < 3600:
            return f"{diff // 60}m ago"
        if diff < 86400:
            return f"{diff // 3600}h ago"
        return dt.strftime("%-d %b")
    except Exception:
        return ""

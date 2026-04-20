"""
Session helpers — expiry enforcement and clean login/logout.

Two limits:
  Absolute cap   — 30 days from login (hard ceiling)
  Idle timeout   — 7 days since last activity (rolling window)
"""
import time

_SESSION_MAX_AGE_SECONDS  = 30 * 24 * 3600   # 30-day absolute cap
_SESSION_IDLE_SECONDS     =  7 * 24 * 3600   #  7-day rolling idle window


def get_session_user(session: dict) -> str | None:
    """
    Return the authenticated user_id, or None if session is missing/expired.
    Updates last_active_at on every valid call (rolling idle window).
    Clears an expired session so the cookie is invalidated.
    """
    user_id = session.get("user_id")
    if not user_id:
        return None

    now      = time.time()
    login_at = session.get("login_at", 0)
    last_act = session.get("last_active_at", login_at)

    # Hard 30-day absolute cap
    if now - login_at > _SESSION_MAX_AGE_SECONDS:
        session.clear()
        return None

    # Rolling 7-day idle timeout
    if now - last_act > _SESSION_IDLE_SECONDS:
        session.clear()
        return None

    session["last_active_at"] = int(now)
    return user_id


def set_session_user(session: dict, user_id: str, phone: str) -> None:
    """
    Write auth data into the session.
    Call this exactly once, after OTP is verified.
    Clears any prior session data first to prevent session fixation.
    """
    session.clear()
    now = int(time.time())
    session["user_id"]        = user_id
    session["phone"]          = phone
    session["login_at"]       = now
    session["last_active_at"] = now


def clear_session(session: dict) -> None:
    """Invalidate the session (logout)."""
    session.clear()

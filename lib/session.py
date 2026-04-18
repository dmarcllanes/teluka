"""
Session helpers — expiry enforcement and clean login/logout.
"""
import time

# Sessions expire after 30 days of inactivity.
# Starlette's SessionMiddleware will also enforce its own max_age,
# so this is a double-check at the application layer.
_SESSION_MAX_AGE_SECONDS = 30 * 24 * 3600  # 30 days


def get_session_user(session: dict) -> str | None:
    """
    Return the authenticated user_id from the session, or None if:
      - no session exists
      - session is older than _SESSION_MAX_AGE_SECONDS
    Clears an expired session so the cookie is invalidated.
    """
    user_id = session.get("user_id")
    if not user_id:
        return None

    login_at = session.get("login_at", 0)
    if time.time() - login_at > _SESSION_MAX_AGE_SECONDS:
        session.clear()
        return None

    return user_id


def set_session_user(session: dict, user_id: str, phone: str) -> None:
    """
    Write auth data into the session.
    Call this exactly once, after OTP is verified.
    Clears any prior session data first to prevent session fixation.
    """
    session.clear()
    session["user_id"]  = user_id
    session["phone"]    = phone
    session["login_at"] = int(time.time())


def clear_session(session: dict) -> None:
    """Invalidate the session (logout)."""
    session.clear()

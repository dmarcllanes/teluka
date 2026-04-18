"""
OTP lifecycle: generate → store (hashed) → verify → get/create user.

OTP is now keyed on the user's EMAIL (not phone), because email is the
delivery channel. Phone is still the immutable identity for deal lookup.

Required tables:
  otp_requests(phone, otp_hash, expires_at, attempts)  ← 'phone' stores email
  users(id, phone, email, ...)
"""
import hashlib
import logging
import re
import secrets
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from lib.supabase_client import get_supabase_admin as get_supabase

logger = logging.getLogger(__name__)

OTP_TTL_MINUTES = 10
MAX_ATTEMPTS    = 5

_RATE_LIMIT_MAX    = 3
_RATE_LIMIT_WINDOW = 15 * 60   # 15 minutes
_rate_limit: dict[str, list[float]] = defaultdict(list)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ── Rate limiter ──────────────────────────────────────────────────────────────

def _check_rate_limit(key: str) -> None:
    now   = time.monotonic()
    times = _rate_limit[key]
    times[:] = [t for t in times if now - t < _RATE_LIMIT_WINDOW]
    if len(times) >= _RATE_LIMIT_MAX:
        wait_secs = int(_RATE_LIMIT_WINDOW - (now - times[0]))
        wait_min  = (wait_secs + 59) // 60
        raise ValueError(
            f"Too many OTP requests. Please wait ~{wait_min} minute(s) before trying again."
        )
    times.append(now)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _gen_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _hash(key: str, code: str) -> str:
    return hashlib.sha256(f"{key}:{code}".encode()).hexdigest()


def is_email(value: str) -> bool:
    return bool(_EMAIL_RE.match(value.strip()))


# ── User lookup ───────────────────────────────────────────────────────────────

async def get_user_by_identifier(identifier: str) -> dict | None:
    """
    Look up a user by phone (E.164) or email.
    Returns the full user row or None if not found.
    """
    supabase = await get_supabase()

    if identifier.startswith("+"):
        # Phone lookup
        rows = (
            await supabase.table("users")
            .select("*")
            .eq("phone", identifier)
            .execute()
        ).data
    else:
        # Email lookup (case-insensitive)
        rows = (
            await supabase.table("users")
            .select("*")
            .ilike("email", identifier.strip())
            .execute()
        ).data

    return rows[0] if rows else None


# ── OTP lifecycle ─────────────────────────────────────────────────────────────

async def create_otp(email: str) -> str:
    """
    Generate OTP keyed on the user's email.
    Returns the plaintext code to be sent via email.
    Raises ValueError if rate limit is exceeded.
    """
    key = email.lower().strip()
    _check_rate_limit(key)

    supabase   = await get_supabase()
    code       = _gen_code()
    expires_at = (
        datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES)
    ).isoformat()

    await supabase.table("otp_requests").delete().eq("phone", key).execute()
    await supabase.table("otp_requests").insert({
        "phone":      key,          # 'phone' column stores email
        "otp_hash":   _hash(key, code),
        "expires_at": expires_at,
        "attempts":   0,
    }).execute()

    logger.info("OTP created for email domain=...%s", email.split("@")[-1])
    return code


async def verify_otp(email: str, code: str) -> tuple[bool, str]:
    """
    Returns (success, error_message).
    """
    key      = email.lower().strip()
    supabase = await get_supabase()

    rows = (
        await supabase.table("otp_requests")
        .select("*")
        .eq("phone", key)
        .execute()
    ).data

    if not rows:
        return False, "No active code found. Please request a new one."

    row = rows[0]

    expires_at = datetime.fromisoformat(row["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        await supabase.table("otp_requests").delete().eq("phone", key).execute()
        return False, "Code expired. Please request a new one."

    if row["attempts"] >= MAX_ATTEMPTS:
        await supabase.table("otp_requests").delete().eq("phone", key).execute()
        return False, "Too many wrong attempts. Please request a new code."

    new_attempts = row["attempts"] + 1
    await (
        supabase.table("otp_requests")
        .update({"attempts": new_attempts})
        .eq("phone", key)
        .execute()
    )

    if _hash(key, code) != row["otp_hash"]:
        remaining = MAX_ATTEMPTS - new_attempts
        if remaining <= 0:
            await supabase.table("otp_requests").delete().eq("phone", key).execute()
            return False, "Too many wrong attempts. Please request a new code."
        plural = "s" if remaining != 1 else ""
        return False, f"Incorrect code. {remaining} attempt{plural} remaining."

    await supabase.table("otp_requests").delete().eq("phone", key).execute()
    logger.info("OTP verified for email domain=...%s", email.split("@")[-1])
    return True, ""


async def get_or_create_user(phone: str, email: str, pin_hash: str = "") -> str:
    """
    Get existing user by phone, or create new user with phone + email + pin_hash.
    Returns the user's UUID.
    """
    supabase = await get_supabase()

    rows = (
        await supabase.table("users")
        .select("id")
        .eq("phone", phone)
        .execute()
    ).data

    if rows:
        return rows[0]["id"]

    payload: dict = {
        "phone":          phone,
        "email":          email.lower().strip(),
        "trust_score":    50.0,
        "scam_reports":   0,
        "gcash_verified": False,
        "maya_verified":  False,
    }
    if pin_hash:
        payload["pin_hash"] = pin_hash

    result = (
        await supabase.table("users")
        .insert(payload)
        .execute()
    ).data

    logger.info("New user created phone=...%s", phone[-4:])
    return result[0]["id"]

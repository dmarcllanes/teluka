"""
OTP lifecycle: generate → store (hashed) → verify → get/create user.

OTP is keyed on the user's EMAIL (not phone), because email is the
delivery channel. Phone is still the immutable identity for deal lookup.

Required tables:
  otp_requests(phone, otp_hash, expires_at, attempts, requester_ip)  ← 'phone' stores email
  otp_lockouts(phone, locked_until, reason)
  auth_events(event_type, user_id, identifier, ip, success)
  users(id, phone, email, ...)
"""
import hashlib
import hmac as _hmac
import logging
import re
import secrets
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from lib.supabase_client import get_supabase_admin as get_supabase

logger = logging.getLogger(__name__)

OTP_TTL_MINUTES  = 10
MAX_ATTEMPTS     = 5
_LOCKOUT_MINUTES = 30

_RATE_LIMIT_MAX    = 3
_RATE_LIMIT_WINDOW = 15 * 60   # 15 minutes in-memory fast-path (per worker)
_rate_limit: dict[str, list[float]] = defaultdict(list)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Known disposable/throwaway email providers
_DISPOSABLE_DOMAINS: frozenset[str] = frozenset({
    "mailinator.com", "guerrillamail.com", "guerrillamail.net",
    "guerrillamail.org", "guerrillamail.biz", "guerrillamail.de",
    "guerrillamail.info", "throwam.com", "yopmail.com", "yopmail.fr",
    "cool.fr.nf", "jetable.fr.nf", "nospam.ze.tc", "nomail.xl.cx",
    "mega.zik.dj", "speed.1s.fr", "courriel.fr.nf", "moncourrier.fr.nf",
    "fakeinbox.com", "trashmail.com", "trashmail.at", "trashmail.io",
    "trashmail.me", "trashmail.net", "trashmail.org", "tempmail.com",
    "temp-mail.org", "dispostable.com", "sharklasers.com", "grr.la",
    "guerrillamailblock.com", "spam4.me", "tempr.email", "maildrop.cc",
    "spamgourmet.com", "spamgourmet.net", "spamgourmet.org",
    "spamfree24.org", "mailnull.com", "discard.email", "dodgeit.com",
    "spamhereplease.com", "getairmail.com", "mailexpire.com",
    "throwam.net", "trashmail.xyz", "tmpmail.net", "10minutemail.com",
    "10minutemail.net", "minutemail.com", "mailnesia.com",
})


# ── Helpers ───────────────────────────────────────────────────────────────────

def _gen_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _hash(key: str, code: str, secret: str = "") -> str:
    msg = f"{key}:{code}".encode()
    if secret:
        return _hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    return hashlib.sha256(msg).hexdigest()


def _mask_identifier(identifier: str) -> str:
    if "@" in identifier:
        local, domain = identifier.split("@", 1)
        return local[:2] + "***@" + domain
    return "***" + identifier[-4:]


def is_email(value: str) -> bool:
    return bool(_EMAIL_RE.match(value.strip()))


def _is_disposable(email: str) -> bool:
    domain = email.lower().split("@")[-1] if "@" in email else ""
    return domain in _DISPOSABLE_DOMAINS


# ── In-memory rate limiter (per-worker fast path) ─────────────────────────────

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


# ── DB-level lockout (persistent, works across all Gunicorn workers) ──────────

async def _check_db_lockout(identifier: str) -> str | None:
    """Returns error message if locked out, else None. Cleans up expired locks."""
    try:
        supabase = await get_supabase()
        rows = (
            await supabase.table("otp_lockouts")
            .select("locked_until")
            .eq("phone", identifier)
            .execute()
        ).data
        if not rows:
            return None
        locked_until_str = rows[0]["locked_until"]
        locked_until = datetime.fromisoformat(
            locked_until_str.replace("Z", "+00:00")
        )
        now = datetime.now(timezone.utc)
        if now >= locked_until:
            await supabase.table("otp_lockouts").delete().eq("phone", identifier).execute()
            return None
        remaining = locked_until - now
        mins = max(1, int(remaining.total_seconds() / 60) + 1)
        return f"Account temporarily locked. Try again in ~{mins} minute(s)."
    except Exception:
        logger.warning("_check_db_lockout failed for identifier (non-fatal)")
        return None


async def _write_db_lockout(identifier: str, reason: str = "too_many_failed_attempts") -> None:
    locked_until = (datetime.now(timezone.utc) + timedelta(minutes=_LOCKOUT_MINUTES)).isoformat()
    try:
        supabase = await get_supabase()
        await supabase.table("otp_lockouts").upsert(
            {"phone": identifier, "locked_until": locked_until, "reason": reason},
            on_conflict="phone",
        ).execute()
    except Exception:
        logger.warning("_write_db_lockout failed for identifier (non-fatal)")


# ── Auth event logging ────────────────────────────────────────────────────────

async def log_auth_event(
    event_type: str,
    *,
    user_id: str | None = None,
    identifier: str | None = None,
    ip: str | None = None,
    success: bool = False,
) -> None:
    """Write a row to auth_events. Non-fatal — never raises."""
    try:
        supabase = await get_supabase()
        await supabase.table("auth_events").insert({
            "event_type": event_type,
            "user_id":    user_id,
            "identifier": identifier,
            "ip":         ip,
            "success":    success,
        }).execute()
    except Exception:
        logger.warning("auth_events insert failed type=%s (non-fatal)", event_type)


# ── User lookup ───────────────────────────────────────────────────────────────

async def get_user_by_identifier(identifier: str) -> dict | None:
    """Look up a user by phone (E.164) or email. Returns the full user row or None."""
    supabase = await get_supabase()

    if identifier.startswith("+"):
        rows = (
            await supabase.table("users")
            .select("*")
            .eq("phone", identifier)
            .execute()
        ).data
    else:
        rows = (
            await supabase.table("users")
            .select("*")
            .ilike("email", identifier.strip())
            .execute()
        ).data

    return rows[0] if rows else None


# ── OTP lifecycle ─────────────────────────────────────────────────────────────

async def create_otp(email: str, ip: str | None = None) -> str:
    """
    Generate OTP keyed on the user's email.
    Returns the plaintext code to be sent via email.
    Raises ValueError on lockout / rate limit / disposable email.
    """
    from lib.config import get_config
    key = email.lower().strip()

    # DB lockout check (works across all workers)
    lockout_msg = await _check_db_lockout(key)
    if lockout_msg:
        await log_auth_event("otp_request", identifier=_mask_identifier(key), ip=ip, success=False)
        raise ValueError(lockout_msg)

    # In-memory fast-path rate limit (per-worker burst protection)
    _check_rate_limit(key)

    if _is_disposable(key):
        raise ValueError("Please use a real email address — disposable addresses are not accepted.")

    cfg    = get_config()
    secret = cfg.otp_secret
    supabase   = await get_supabase()
    code       = _gen_code()
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES)).isoformat()

    await supabase.table("otp_requests").delete().eq("phone", key).execute()
    await supabase.table("otp_requests").insert({
        "phone":        key,
        "otp_hash":     _hash(key, code, secret),
        "expires_at":   expires_at,
        "attempts":     0,
        "requester_ip": ip,
    }).execute()

    await log_auth_event("otp_request", identifier=_mask_identifier(key), ip=ip, success=True)
    logger.info("OTP created for email domain=...%s", email.split("@")[-1])
    return code


async def verify_otp(email: str, code: str, ip: str | None = None) -> tuple[bool, str]:
    """Returns (success, error_message)."""
    from lib.config import get_config
    key      = email.lower().strip()
    masked   = _mask_identifier(key)
    cfg      = get_config()
    secret   = cfg.otp_secret
    supabase = await get_supabase()

    # DB lockout check
    lockout_msg = await _check_db_lockout(key)
    if lockout_msg:
        await log_auth_event("otp_fail", identifier=masked, ip=ip, success=False)
        return False, lockout_msg

    rows = (
        await supabase.table("otp_requests")
        .select("*")
        .eq("phone", key)
        .execute()
    ).data

    if not rows:
        await log_auth_event("otp_fail", identifier=masked, ip=ip, success=False)
        return False, "No active code found. Please request a new one."

    row = rows[0]

    expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expires_at:
        await supabase.table("otp_requests").delete().eq("phone", key).execute()
        await log_auth_event("otp_fail", identifier=masked, ip=ip, success=False)
        return False, "Code expired. Please request a new one."

    if row["attempts"] >= MAX_ATTEMPTS:
        await supabase.table("otp_requests").delete().eq("phone", key).execute()
        await _write_db_lockout(key)
        await log_auth_event("lockout", identifier=masked, ip=ip, success=False)
        return False, "Too many wrong attempts. Please request a new code."

    new_attempts = row["attempts"] + 1
    await (
        supabase.table("otp_requests")
        .update({"attempts": new_attempts})
        .eq("phone", key)
        .execute()
    )

    expected = _hash(key, code, secret)
    if not _hmac.compare_digest(expected, row["otp_hash"]):
        remaining = MAX_ATTEMPTS - new_attempts
        if remaining <= 0:
            await supabase.table("otp_requests").delete().eq("phone", key).execute()
            await _write_db_lockout(key)
            await log_auth_event("lockout", identifier=masked, ip=ip, success=False)
            return False, "Too many wrong attempts. Account locked for 30 minutes."
        await log_auth_event("otp_fail", identifier=masked, ip=ip, success=False)
        plural = "s" if remaining != 1 else ""
        return False, f"Incorrect code. {remaining} attempt{plural} remaining."

    await supabase.table("otp_requests").delete().eq("phone", key).execute()
    await log_auth_event("otp_success", identifier=masked, ip=ip, success=True)
    logger.info("OTP verified for email domain=...%s", email.split("@")[-1])
    return True, ""


async def get_or_create_user(phone: str, email: str, pin_hash: str = "") -> str:
    """Get existing user by phone, or create new user. Returns the user's UUID."""
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

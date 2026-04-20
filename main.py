import asyncio
import logging
import logging.config
import time as _time

from dotenv import load_dotenv
load_dotenv()

# ── Logging — configure before any app imports ────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Crash fast on missing required env vars ───────────────────────────────────
from lib.config import get_config  # noqa: E402  (import after logging setup)
cfg = get_config()

from datetime import datetime as _dt
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from starlette.staticfiles import StaticFiles
from fasthtml.common import *

from components.pages.landing import landing_page
from components.pages.login import (
    login_page, otp_step, pin_step, identifier_form_fragment, signup_form_fragment,
)
from components.pages.dashboard import dashboard_page
from components.pages.profile import (
    profile_page, verify_pending_html, verify_done_html,
)
from components.pages.new_deal import (
    new_deal_page, seller_found_card, seller_not_found, seller_blocked,
)
from components.pages.deal_detail import deal_detail_page
from lib.otp_store import (
    create_otp, get_or_create_user, verify_otp as check_otp,
    get_user_by_identifier, is_email, log_auth_event,
)
from lib.pin import hash_pin, verify_pin, validate_pin
from lib.email_sender import mask_email
from lib.jobs import enqueue_send_otp
from lib.storage import upload_evidence_photo, upload_unboxing_video, upload_avatar, upload_trust_photo
from core.escrow import cancel_escrow, initiate_escrow, release_escrow
from core.exceptions import ScamDetected, VerificationFailed
from core.forensics import analyze_risk
from core.verification import verify_photo_liveness, check_evidence_complete, check_release_gate
from core.tiers import get_tier, get_plan, PLANS
from lib.phone import normalize_ph_phone, PhoneValidationError
from lib.session import get_session_user, set_session_user, clear_session
from lib.middleware import apply_middleware
from lib.supabase_client import get_supabase_admin
from lib.cache import (
    aget as cache_get, aset as cache_set, adelete as cache_del,
    init_redis, cache,
    TTL_USER, TTL_TX_LIST, TTL_SELLER, TTL_ACTIVITY, TTL_LANDING,
)
from lib.activity import log_event, get_events, format_relative_time
from lib.push import notify_user
from schemas.transaction import CreateTransactionRequest, Transaction, TransactionStatus
from schemas.user import UserProfile

fapp, rt = fast_app(secret_key=cfg.session_secret)
fapp.mount("/static", StaticFiles(directory="static"), name="static")

logger.info("Teluka starting — env=%s", cfg.env)


# ---------------------------------------------------------------------------
# Startup: connect Redis if configured
# ---------------------------------------------------------------------------

@fapp.on_event("startup")
async def _startup():
    if cfg.redis_url:
        await init_redis(cfg.redis_url)
    logger.info("Startup complete workers=ready")


# ---------------------------------------------------------------------------
# PIN brute-force lockout (in-memory per worker, resets on restart)
# ---------------------------------------------------------------------------

import time as _ptime  # separate alias to avoid shadowing

_pin_fails: dict[str, tuple[int, float]] = {}  # user_id → (count, lockout_until)
_PIN_MAX_TRIES  = 5
_PIN_LOCKOUT_S  = 15 * 60   # 15 minutes


def _check_pin_lockout(user_id: str) -> str | None:
    """Returns an error message if locked out, else None."""
    entry = _pin_fails.get(user_id)
    if not entry:
        return None
    count, until = entry
    if _ptime.monotonic() < until:
        mins = max(1, int((until - _ptime.monotonic()) / 60) + 1)
        return f"Too many wrong PINs. Try again in {mins} minute(s)."
    return None


def _record_pin_fail(user_id: str) -> None:
    entry = _pin_fails.get(user_id, (0, 0.0))
    count = entry[0] + 1
    until = _ptime.monotonic() + _PIN_LOCKOUT_S if count >= _PIN_MAX_TRIES else 0.0
    _pin_fails[user_id] = (count, until)


def _clear_pin_lockout(user_id: str) -> None:
    _pin_fails.pop(user_id, None)


# ---------------------------------------------------------------------------
# File type validation
# ---------------------------------------------------------------------------

import io
_ALLOWED_IMAGE_EXTS  = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
_ALLOWED_VIDEO_EXTS  = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}
_ALLOWED_VIDEO_MIMES = {
    "video/mp4", "video/quicktime", "video/webm",
    "video/x-matroska", "video/x-msvideo",
}


def _validate_image_file(file_bytes: bytes, filename: str) -> str | None:
    """Returns error string or None if valid."""
    ext = ("." + filename.rsplit(".", 1)[-1]).lower() if "." in filename else ""
    if ext not in _ALLOWED_IMAGE_EXTS:
        return f"'{filename}' must be an image (JPEG, PNG, WebP)."
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()
    except Exception:
        return f"'{filename}' is not a valid image file."
    return None


def _validate_video_file(filename: str, content_type: str) -> str | None:
    ext = ("." + filename.rsplit(".", 1)[-1]).lower() if "." in filename else ""
    if ext not in _ALLOWED_VIDEO_EXTS:
        return "Please upload a video file (MP4, MOV, WebM)."
    mime = (content_type or "").split(";")[0].strip().lower()
    if mime and mime not in _ALLOWED_VIDEO_MIMES:
        return "Please upload a video file (MP4, MOV, WebM)."
    return None


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

async def _get_user(user_id: str) -> dict | None:
    key = f"user:{user_id}"
    row = await cache_get(key)
    if row is None:
        sb  = await get_supabase_admin()
        row = (await sb.table("users").select("*").eq("id", user_id).single().execute()).data
        if row:
            await cache_set(key, row, TTL_USER)
    return row


async def _get_tx_list(user_id: str) -> list:
    key = f"txlist:{user_id}"
    rows = await cache_get(key)
    if rows is None:
        sb   = await get_supabase_admin()
        rows = (
            await sb.table("transactions")
            .select("*")
            .or_(f"buyer_id.eq.{user_id},seller_id.eq.{user_id}")
            .order("created_at", desc=True)
            .execute()
        ).data or []
        await cache_set(key, rows, TTL_TX_LIST)
    return rows


async def _bust_user(*user_ids: str) -> None:
    for uid in user_ids:
        await cache_del(f"user:{uid}")


async def _bust_tx_lists(*user_ids: str) -> None:
    for uid in user_ids:
        await cache_del(f"txlist:{uid}")


# Landing-page HTML cache (module-level, not per-request)
_landing_html: str | None = None
_landing_expires: float = 0.0


def _parse_location(form) -> tuple[float | None, float | None]:
    """Extract action_lat / action_lon from a form, return (lat, lon) or (None, None)."""
    try:
        lat = form.get("action_lat", "").strip()
        lon = form.get("action_lon", "").strip()
        if lat and lon:
            return float(lat), float(lon)
    except (ValueError, AttributeError):
        pass
    return None, None


def _get_client_ip(request: Request) -> str | None:
    """Extract the real client IP, respecting X-Forwarded-For set by the platform."""
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    return getattr(request.client, "host", None)


# ---------------------------------------------------------------------------
# Health check (used by deployment platforms)
# ---------------------------------------------------------------------------

@fapp.get("/health")
async def health():
    return JSONResponse({"status": "ok", "env": cfg.env})


# ---------------------------------------------------------------------------
# Web Push
# ---------------------------------------------------------------------------

@fapp.get("/push/public-key")
async def push_public_key():
    return JSONResponse({"key": cfg.vapid_public_key or ""})


@fapp.post("/push/subscribe")
async def push_subscribe(request: Request, session):
    user_id = get_session_user(session)
    if not user_id:
        return JSONResponse({"error": "unauthenticated"}, status_code=401)
    body = await request.json()
    endpoint = body.get("endpoint", "")
    if not endpoint:
        return JSONResponse({"error": "missing endpoint"}, status_code=400)
    try:
        supabase = await get_supabase_admin()
        await supabase.table("push_subscriptions").upsert(
            {"user_id": user_id, "endpoint": endpoint, "subscription": body},
            on_conflict="user_id,endpoint",
        ).execute()
        logger.info("Push subscription saved user=%s", user_id)
    except Exception:
        logger.exception("push_subscribe failed user=%s", user_id)
    return JSONResponse({"ok": True})


@fapp.post("/push/unsubscribe")
async def push_unsubscribe(request: Request, session):
    user_id = get_session_user(session)
    if not user_id:
        return JSONResponse({"error": "unauthenticated"}, status_code=401)
    body = await request.json()
    endpoint = body.get("endpoint", "")
    if endpoint:
        try:
            supabase = await get_supabase_admin()
            await supabase.table("push_subscriptions").delete().eq("user_id", user_id).eq("endpoint", endpoint).execute()
        except Exception:
            logger.exception("push_unsubscribe failed user=%s", user_id)
    return JSONResponse({"ok": True})


# ---------------------------------------------------------------------------
# Landing
# ---------------------------------------------------------------------------

@rt("/")
def get():
    global _landing_html, _landing_expires
    now = _time.monotonic()
    if _landing_html and now < _landing_expires:
        return HTMLResponse(_landing_html)
    html = to_xml(landing_page())
    _landing_html = html
    _landing_expires = now + TTL_LANDING
    return HTMLResponse(html)


# ---------------------------------------------------------------------------
# Auth: Login
# ---------------------------------------------------------------------------

@rt("/login")
def get(session):
    if get_session_user(session):
        return RedirectResponse("/dashboard", status_code=303)
    return login_page()


@rt("/login/identifier-form")
def get():
    """HTMX fragment — returns identifier form (for '← Back')."""
    return identifier_form_fragment()


@rt("/check-identifier")
async def post(request: Request, identifier: str, mode: str = ""):
    """
    Step 1: user enters phone or email.
    - Phone + existing user  → send OTP to their email → otp_step
    - Phone + new user       → ask for email → register_email_step
    - Email + existing user  → send OTP to that email → otp_step
    - Email + not found      → error
    mode='signin' → error if user not found (don't offer sign-up)
    """
    identifier = identifier.strip()
    client_ip  = _get_client_ip(request)

    if not identifier:
        return identifier_form_fragment(error="Please enter your phone number or email.")

    # ── Email identifier ──────────────────────────────────────────────────────
    if is_email(identifier):
        user = await get_user_by_identifier(identifier)
        if not user:
            return identifier_form_fragment(
                error="No account found with that email. Use your phone number to register."
            )
        email = user["email"]
        try:
            code = await create_otp(email, ip=client_ip)
            sent = await enqueue_send_otp(email, code)
            if not sent:
                return identifier_form_fragment(error="Failed to send email. Please try again.")
        except ValueError as e:
            return identifier_form_fragment(error=str(e))
        except Exception:
            logger.exception("check-identifier email send error")
            return identifier_form_fragment(error="Something went wrong. Please try again.")
        return otp_step(mask_email(email), email)

    # ── Phone identifier ──────────────────────────────────────────────────────
    try:
        normalised = normalize_ph_phone(identifier).e164
    except PhoneValidationError as e:
        return identifier_form_fragment(error=str(e))

    user = await get_user_by_identifier(normalised)

    if not user:
        if mode == "signin":
            return identifier_form_fragment(
                error="No account found with that number. Please sign up instead."
            )
        return signup_form_fragment(phone=normalised)

    email = user.get("email")
    if not email:
        return identifier_form_fragment(
            error="Account has no email on file. Please contact support."
        )

    try:
        code = await create_otp(email, ip=client_ip)
        sent = await enqueue_send_otp(email, code)
        if not sent:
            return identifier_form_fragment(error="Failed to send email. Please try again.")
    except ValueError as e:
        return identifier_form_fragment(error=str(e))
    except Exception:
        logger.exception("check-identifier phone send error")
        return identifier_form_fragment(error="Something went wrong. Please try again.")

    return otp_step(mask_email(email), email)


@rt("/register")
async def post(request: Request, phone: str, email: str, pin: str = "", pin_confirm: str = ""):
    """
    Sign-up step: phone + email + PIN (all collected upfront in new wizard).
    Creates OTP keyed on email, sends it, returns otp_step with PIN passed through.
    """
    form = await request.form()
    # Honeypot — bots fill this field, humans leave it empty
    if form.get("email_confirm", ""):
        return signup_form_fragment(phone=phone, error="Registration failed. Please try again.")

    email = email.strip().lower()
    pin   = pin.strip()
    pin_confirm = pin_confirm.strip()

    if not is_email(email):
        return signup_form_fragment(phone=phone, email=email, error="Please enter a valid email address.")

    # Validate PIN
    if pin:
        err = validate_pin(pin)
        if err:
            return signup_form_fragment(phone=phone, email=email, error=err)
        if pin != pin_confirm:
            return signup_form_fragment(phone=phone, email=email, error="PINs do not match. Please try again.")

    # Check email not already taken
    existing = await get_user_by_identifier(email)
    if existing:
        return signup_form_fragment(
            phone=phone,
            error="That email is already linked to another account. Use a different email.",
        )

    client_ip = _get_client_ip(request)
    try:
        code = await create_otp(email, ip=client_ip)
        sent = await enqueue_send_otp(email, code)
        if not sent:
            return signup_form_fragment(phone=phone, error="Failed to send email. Please try again.")
    except ValueError as e:
        return signup_form_fragment(phone=phone, error=str(e))
    except Exception:
        logger.exception("register send error")
        return signup_form_fragment(phone=phone, error="Something went wrong. Please try again.")

    return otp_step(mask_email(email), email, _phone=phone, _pin=pin)


@rt("/resend-otp")
async def post(request: Request, email: str):
    """Re-send OTP to the same email."""
    client_ip = _get_client_ip(request)
    try:
        code = await create_otp(email, ip=client_ip)
        sent = await enqueue_send_otp(email, code)
        if not sent:
            return Div(Div("Failed to send email. Please try again.", cls="toast toast-error"))
    except ValueError as e:
        return Div(Div(str(e), cls="toast toast-error"))
    except Exception:
        logger.exception("resend-otp error")
        return Div(Div("Something went wrong. Please try again.", cls="toast toast-error"))
    return Div(Div("New code sent! Check your inbox.", cls="toast toast-success"))


@rt("/verify-otp")
async def post(request: Request, session):
    """Verify OTP, create/load user, set session."""
    form  = await request.form()
    email = form.get("email", "").strip()
    phone = form.get("phone", "").strip()
    # Assemble from named digit fields first (avoids JS autocomplete race on mobile)
    digits = "".join(form.get(f"otp-{i}", "") for i in range(6)).strip()
    clean_otp = digits if len(digits) == 6 else form.get("otp", "").strip()

    if not email:
        return Div(Div("Session error — please start over.", cls="toast toast-error"))
    if not clean_otp.isdigit() or len(clean_otp) != 6:
        return Div(Div("Please enter the 6-digit code from your email.", cls="toast toast-error"))

    client_ip = _get_client_ip(request)
    ok, error_msg = await check_otp(email, clean_otp, ip=client_ip)
    if not ok:
        return Div(Div(error_msg, cls="toast toast-error"))

    pin = form.get("pin", "").strip()

    try:
        user = await get_user_by_identifier(email)
        if user:
            # Existing user — log in directly
            user_id    = user["id"]
            user_phone = user["phone"]
            session.clear()
            set_session_user(session, user_id, user_phone)

            # Detect login from new IP and update last_login_ip
            old_ip = user.get("last_login_ip")
            supabase_u = await get_supabase_admin()
            await supabase_u.table("users").update({"last_login_ip": client_ip}).eq("id", user_id).execute()
            if old_ip and old_ip != client_ip:
                asyncio.create_task(notify_user(
                    user_id,
                    "New Login Location 🔐",
                    "A login from a new location was detected. If this wasn't you, secure your account.",
                    "/profile",
                ))
            asyncio.create_task(log_auth_event(
                "login", user_id=user_id, identifier=mask_email(email), ip=client_ip, success=True
            ))
        elif phone:
            if pin:
                # New user — create account directly with PIN collected in sign-up form
                hashed  = hash_pin(pin)
                user_id = await get_or_create_user(phone, email, pin_hash=hashed)
                session.clear()
                set_session_user(session, user_id, phone)
                logger.info("New user created user=%s", user_id)
                new_user_overlay = Div(
                    Div(cls="verify-success-overlay")(
                        Div(cls="vso-backdrop"),
                        Div(cls="vso-card")(
                            Div(cls="vso-icon-wrap")(
                                Div(cls="vso-ring"),
                                Div(cls="vso-ring vso-ring-2"),
                                Div(cls="vso-check")(
                                    NotStr(
                                        '<svg width="36" height="36" viewBox="0 0 24 24" fill="none"'
                                        ' stroke="white" stroke-width="3" stroke-linecap="round"'
                                        ' stroke-linejoin="round"'
                                        ' style="stroke-dasharray:40;stroke-dashoffset:0">'
                                        '<polyline points="20 6 9 17 4 12"/></svg>'
                                    ),
                                ),
                            ),
                            H2("Account Created!", cls="vso-title"),
                            P("Welcome to Teluka. Taking you to your dashboard…", cls="vso-sub"),
                            Div(cls="vso-bar-track")(Div(cls="vso-bar-fill")),
                        ),
                    ),
                    Script("setTimeout(() => { window.location.href = '/dashboard'; }, 2000);"),
                )
                return HTMLResponse(
                    content=to_xml(new_user_overlay),
                    headers={"HX-Retarget": "#vso-portal", "HX-Reswap": "innerHTML"},
                )
            else:
                # Old flow fallback — go to PIN creation step
                return pin_step(phone=phone, email=email)
        else:
            return Div(Div("Account error. Please start over.", cls="toast toast-error"))
    except Exception:
        logger.exception("verify-otp: session setup failed")
        return Div(Div("Account error. Please contact support.", cls="toast toast-error"))

    logger.info("User logged in user=%s", user_id)
    overlay = Div(
        Div(cls="verify-success-overlay")(
            Div(cls="vso-backdrop"),
            Div(cls="vso-card")(
                Div(cls="vso-icon-wrap")(
                    Div(cls="vso-ring"),
                    Div(cls="vso-ring vso-ring-2"),
                    Div(cls="vso-check")(
                        NotStr(
                            '<svg width="36" height="36" viewBox="0 0 24 24" fill="none"'
                            ' stroke="white" stroke-width="3" stroke-linecap="round"'
                            ' stroke-linejoin="round"'
                            ' style="stroke-dasharray:40;stroke-dashoffset:0">'
                            '<polyline points="20 6 9 17 4 12"/></svg>'
                        ),
                    ),
                ),
                H2("Verified!", cls="vso-title"),
                P("Taking you to your dashboard…", cls="vso-sub"),
                Div(cls="vso-bar-track")(Div(cls="vso-bar-fill")),
            ),
        ),
        Script("setTimeout(() => { window.location.href = '/dashboard'; }, 2000);"),
    )
    return HTMLResponse(
        content=to_xml(overlay),
        headers={"HX-Retarget": "#vso-portal", "HX-Reswap": "innerHTML"},
    )


@rt("/set-pin")
async def post(phone: str, email: str, pin: str, pin_confirm: str, session):
    """New user: hash PIN, create account, set session."""
    err = validate_pin(pin)
    if err:
        return Div(Div(err, cls="toast toast-error"))
    if pin != pin_confirm:
        return Div(Div("PINs do not match. Please try again.", cls="toast toast-error"))

    try:
        hashed    = hash_pin(pin)
        user_id   = await get_or_create_user(phone, email, pin_hash=hashed)
        # Regenerate session to prevent session fixation
        session.clear()
        set_session_user(session, user_id, phone)
    except Exception:
        logger.exception("set-pin: user creation failed")
        return Div(Div("Account error. Please contact support.", cls="toast toast-error"))

    logger.info("New user created with PIN user=%s", user_id)
    overlay = Div(
        Div(cls="verify-success-overlay")(
            Div(cls="vso-backdrop"),
            Div(cls="vso-card")(
                Div(cls="vso-icon-wrap")(
                    Div(cls="vso-ring"),
                    Div(cls="vso-ring vso-ring-2"),
                    Div(cls="vso-check")(
                        NotStr(
                            '<svg width="36" height="36" viewBox="0 0 24 24" fill="none"'
                            ' stroke="white" stroke-width="3" stroke-linecap="round"'
                            ' stroke-linejoin="round"'
                            ' style="stroke-dasharray:40;stroke-dashoffset:0">'
                            '<polyline points="20 6 9 17 4 12"/></svg>'
                        ),
                    ),
                ),
                H2("Account Created!", cls="vso-title"),
                P("Welcome to Teluka. Taking you to your dashboard…", cls="vso-sub"),
                Div(cls="vso-bar-track")(Div(cls="vso-bar-fill")),
            ),
        ),
        Script("setTimeout(() => { window.location.href = '/dashboard'; }, 2000);"),
    )
    return HTMLResponse(
        content=to_xml(overlay),
        headers={"HX-Retarget": "#vso-portal", "HX-Reswap": "innerHTML"},
    )


@rt("/logout")
def post(session):
    clear_session(session)
    return RedirectResponse("/", status_code=303)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@rt("/dashboard")
async def get(session):
    user_id = get_session_user(session)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    user_row, tx_rows = await asyncio.gather(
        _get_user(user_id),
        _get_tx_list(user_id),
    )
    if not user_row:
        session.clear()
        return RedirectResponse("/login", status_code=303)

    return dashboard_page(UserProfile(**user_row), [Transaction(**r) for r in tx_rows])


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@rt("/profile")
async def get(session):
    user_id = get_session_user(session)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    user_row, tx_rows = await asyncio.gather(
        _get_user(user_id),
        _get_tx_list(user_id),
    )
    if not user_row:
        session.clear()
        return RedirectResponse("/login", status_code=303)

    return profile_page(UserProfile(**user_row), [Transaction(**r) for r in tx_rows])


# ─── Profile edit ─────────────────────────────────────────────────────────────

@rt("/profile/edit")
async def post(request: Request, session):
    user_id = get_session_user(session)
    if not user_id:
        return Response(status_code=401)

    form  = await request.form()
    email = form.get("email", "").strip()

    supabase = await get_supabase_admin()
    await supabase.table("users").update({"email": email or None}).eq("id", user_id).execute()
    await _bust_user(user_id)
    return Response(status_code=204)


# ─── Wallet verification ──────────────────────────────────────────────────────

@rt("/profile/verify-gcash")
async def post(request: Request, session):
    user_id = get_session_user(session)
    if not user_id:
        return Response(status_code=401)
    form = await request.form()
    number = form.get("gcash_number", "").strip()
    # In production: call PayMongo / GCash API to send ₱1. For now: store pending number.
    supabase = await get_supabase_admin()
    await supabase.table("users").update({"gcash_pending_number": number}).eq("id", user_id).execute()
    await _bust_user(user_id)
    return verify_pending_html("gcash", "GCash", "💚")


@rt("/profile/verify-gcash-confirm")
async def post(request: Request, session):
    user_id = get_session_user(session)
    if not user_id:
        return Response(status_code=401)
    # In production: validate the ref against PayMongo. For now: mark as verified.
    supabase = await get_supabase_admin()
    await supabase.table("users").update({
        "gcash_verified": True,
        "kyc_status": "verified",
    }).eq("id", user_id).execute()
    await _bust_user(user_id)
    return verify_done_html("GCash", "💚")


@rt("/profile/verify-maya")
async def post(request: Request, session):
    user_id = get_session_user(session)
    if not user_id:
        return Response(status_code=401)
    form = await request.form()
    number = form.get("maya_number", "").strip()
    supabase = await get_supabase_admin()
    await supabase.table("users").update({"maya_pending_number": number}).eq("id", user_id).execute()
    await _bust_user(user_id)
    return verify_pending_html("maya", "Maya", "💜")


@rt("/profile/verify-maya-confirm")
async def post(request: Request, session):
    user_id = get_session_user(session)
    if not user_id:
        return Response(status_code=401)
    supabase = await get_supabase_admin()
    await supabase.table("users").update({
        "maya_verified": True,
        "kyc_status": "verified",
    }).eq("id", user_id).execute()
    await _bust_user(user_id)
    return verify_done_html("Maya", "💜")


# ─── Avatar upload ────────────────────────────────────────────────────────────

@rt("/profile/avatar")
async def post(request: Request, session):
    user_id = get_session_user(session)
    if not user_id:
        return Response(status_code=401)

    form = await request.form()
    photo = form.get("avatar")
    if not photo or not getattr(photo, "filename", None):
        return Div(Div("Please select an image file.", cls="toast toast-error"))

    file_bytes = await photo.read()
    img_err = _validate_image_file(file_bytes, photo.filename)
    if img_err:
        return Div(Div(img_err, cls="toast toast-error"))

    try:
        url = await upload_avatar(file_bytes, user_id)
    except ValueError as e:
        return Div(Div(str(e), cls="toast toast-error"))
    except Exception:
        logger.exception("Avatar upload failed user=%s", user_id)
        return Div(Div("Upload failed. Please try again.", cls="toast toast-error"))

    supabase = await get_supabase_admin()
    await supabase.table("users").update({"avatar_url": url}).eq("id", user_id).execute()
    await _bust_user(user_id)
    logger.info("Avatar saved user=%s", user_id)
    return Div(
        Div("Profile photo updated!", cls="toast toast-success"),
        # Update the avatar image in-place without page reload
        Script(f"""
(function(){{
  var img = document.getElementById('avatar-img');
  var init = document.getElementById('avatar-initials');
  var url = {repr(url)};
  if (img) {{ img.src = url + '?t=' + Date.now(); }}
  else if (init) {{
    var av = init.parentElement;
    init.remove();
    var el = document.createElement('img');
    el.id = 'avatar-img'; el.src = url; el.alt = 'Avatar';
    el.className = 'avatar-photo';
    av.prepend(el);
  }}
}})();
        """),
    )


# ─── Real-time trust photo ────────────────────────────────────────────────────

@rt("/profile/trust-photo")
async def post(request: Request, session):
    user_id = get_session_user(session)
    if not user_id:
        return Response(status_code=401)

    form = await request.form()
    photo = form.get("trust_photo")
    if not photo or not getattr(photo, "filename", None):
        return Div(Div("No photo received.", cls="toast toast-error"))

    file_bytes = await photo.read()
    img_err = _validate_image_file(file_bytes, photo.filename or "capture.jpg")
    if img_err:
        return Div(Div(img_err, cls="toast toast-error"))

    try:
        url = await upload_trust_photo(file_bytes, user_id)
    except ValueError as e:
        return Div(Div(str(e), cls="toast toast-error"))
    except Exception:
        logger.exception("Trust photo upload failed user=%s", user_id)
        return Div(Div("Upload failed. Please try again.", cls="toast toast-error"))

    from datetime import timezone
    taken_at = _dt.now(timezone.utc).isoformat()
    supabase = await get_supabase_admin()
    await supabase.table("users").update({
        "trust_photo_url": url,
        "trust_photo_taken_at": taken_at,
    }).eq("id", user_id).execute()
    await _bust_user(user_id)
    logger.info("Trust photo saved user=%s", user_id)
    return Div(
        Div("Trust photo saved! Your profile now shows extra verification.", cls="toast toast-success"),
        Script(f"""
(function(){{
  var card = document.getElementById('trust-photo-card');
  if (card) card.innerHTML = '<img src="{url}" class="trust-photo-result" alt="Trust photo">'
    + '<p class="trust-photo-taken">📸 Taken just now · Visible to deal counterparties</p>'
    + '<button class="tp-retake-btn" onclick="startTrustCamera()">Retake</button>';
}})();
        """),
    )


# ---------------------------------------------------------------------------
# Seller lookup (HTMX fragment)
# ---------------------------------------------------------------------------

@rt("/sellers/lookup")
async def post(phone: str, session):
    if not get_session_user(session):
        return Div(Div("Session expired. Please log in again.", cls="toast toast-error"))

    try:
        normalised = normalize_ph_phone(phone).e164
    except PhoneValidationError as e:
        return Div(Div(str(e), cls="toast toast-error"))

    current_user_id = get_session_user(session)
    supabase = await get_supabase_admin()
    self_row = (
        await supabase.table("users").select("phone")
        .eq("id", current_user_id).single().execute()
    ).data
    if self_row and self_row.get("phone") == normalised:
        return seller_blocked(normalised, "You cannot create a deal with yourself.")

    seller_key = f"seller:{normalised}"
    seller_row = cache.get(seller_key)
    if seller_row is None:
        seller_row = (
            await supabase.table("users").select("*").eq("phone", normalised).single().execute()
        ).data
        if seller_row:
            cache.set(seller_key, seller_row, TTL_SELLER)
    if not seller_row:
        return seller_not_found(normalised)

    seller = UserProfile(**seller_row)
    try:
        result = analyze_risk(
            phone=seller.phone,
            trust_score=seller.trust_score,
            scam_reports=seller.scam_reports,
        )
        return seller_found_card(seller, result.flags)
    except ScamDetected as e:
        return seller_blocked(normalised, str(e))


# ---------------------------------------------------------------------------
# New deal
# ---------------------------------------------------------------------------

@rt("/transactions/new")
def get(session):
    user_id = get_session_user(session)
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    return new_deal_page(user_id)


@rt("/transactions/create")
async def post(request: Request, session, item_description: str = "", amount_php: float = 0,
               seller_id: str = "", protection_plan: str = "basic"):
    buyer_id = get_session_user(session)
    if not buyer_id:
        return Div(Div("Session expired.", cls="toast toast-error"))

    form = await request.form()
    item_description = item_description or str(form.get("item_description", "")).strip()
    amount_php       = amount_php or float(form.get("amount_php", 0) or 0)
    seller_id        = seller_id  or str(form.get("seller_id", "")).strip()
    protection_plan  = str(form.get("protection_plan", protection_plan)).strip()
    lat, lon         = _parse_location(form)

    amount_centavos = int(amount_php * 100)
    plan = get_plan(protection_plan) if protection_plan in PLANS else get_tier(amount_centavos)
    fee  = plan.fee_centavos(amount_centavos)

    req = CreateTransactionRequest(
        buyer_id=buyer_id,
        seller_id=seller_id,
        item_description=item_description,
        amount_centavos=amount_centavos,
        protection_plan=plan.id,
        platform_fee_centavos=fee,
    )

    supabase = await get_supabase_admin()
    row = (
        await supabase.table("transactions").insert(req.model_dump()).execute()
    ).data[0]
    tx_id = row["id"]

    await log_event(tx_id, "deal_created",
        f'Deal for \"{item_description}\" created \u00b7 \u20b1{amount_centavos / 100:,.0f}',
        actor_id=buyer_id, lat=lat, lon=lon)
    await log_event(tx_id, "tier_upgraded",
        f"{plan.badge_icon} {plan.name} protection active \u00b7 {plan.min_photos} photos, {plan.review_hours}h review"
        + (f" \u00b7 Service fee: \u20b1{fee / 100:,.2f}" if fee else " \u00b7 No service fee"),
        icon=plan.badge_icon)

    await _bust_tx_lists(buyer_id, seller_id)
    # Notify seller of new deal
    asyncio.create_task(notify_user(seller_id, "New Deal Request 🤝",
        f"A buyer wants to create a protected deal for ₱{amount_centavos/100:,.0f}. Tap to review.",
        f"/transactions/{tx_id}"))
    logger.info("Transaction created tx=%s buyer=%s", tx_id, buyer_id)
    return Div(
        Div("Deal created!", cls="toast toast-success"),
        Script(f"setTimeout(() => {{ window.location.href = '/transactions/{tx_id}'; }}, 800);"),
    )


# ---------------------------------------------------------------------------
# Deal detail
# ---------------------------------------------------------------------------

@rt("/transactions/{tx_id}")
async def get(tx_id: str, session):
    user_id = get_session_user(session)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    supabase = await get_supabase_admin()
    row = (
        await supabase.table("transactions").select("*").eq("id", tx_id).single().execute()
    ).data
    if not row:
        return RedirectResponse("/dashboard", status_code=303)

    tx = Transaction(**row)

    buyer_row, seller_row = await asyncio.gather(
        _get_user(tx.buyer_id),
        _get_user(tx.seller_id),
    )
    buyer  = UserProfile(**buyer_row)  if buyer_row  else None
    seller = UserProfile(**seller_row) if seller_row else None

    return deal_detail_page(tx, buyer, seller, user_id)


# ---------------------------------------------------------------------------
# Escrow actions
# ---------------------------------------------------------------------------

@rt("/transactions/pay")
async def post(request: Request, session):
    user_id = get_session_user(session)
    if not user_id:
        return Div(Div("Session expired.", cls="toast toast-error"))
    form  = await request.form()
    tx_id = str(form.get("tx_id", "")).strip()
    lat, lon = _parse_location(form)
    supabase = await get_supabase_admin()
    row = (
        await supabase.table("transactions").select("*").eq("id", tx_id).single().execute()
    ).data
    if not row:
        return Div(Div("Deal not found.", cls="toast toast-error"))
    tx = Transaction(**row)
    try:
        await initiate_escrow(tx)
        await _bust_tx_lists(tx.buyer_id, tx.seller_id)
        await log_event(tx_id, "payment_held",
            f"₱{tx.amount_centavos / 100:,.0f} held securely — seller cannot access funds until you confirm",
            actor_id=user_id, lat=lat, lon=lon)
        asyncio.create_task(notify_user(tx.seller_id, "Payment Received 🔒",
            f"₱{tx.amount_centavos/100:,.0f} is now held in escrow. Upload your evidence photos to proceed.",
            f"/transactions/{tx_id}"))
        return Div(
            Div("Funds held securely!", cls="toast toast-success"),
            Script("setTimeout(() => location.reload(), 1200);"),
        )
    except Exception as e:
        logger.exception("initiate_escrow failed tx=%s", tx_id)
        return Div(Div(f"Payment failed: {e}", cls="toast toast-error"))


@rt("/transactions/evidence")
async def post(request: Request, session):
    """Accept real file uploads, validate EXIF, store to Supabase Storage."""
    if not get_session_user(session):
        return Div(Div("Session expired.", cls="toast toast-error"))

    form = await request.form()
    tx_id       = form.get("tx_id")
    photo_files = form.getlist("photos")

    if not tx_id:
        return Div(Div("Missing deal ID.", cls="toast toast-error"))

    valid_files = [f for f in photo_files if getattr(f, "filename", None)]
    if not valid_files:
        return Div(Div("Please select at least one photo.", cls="toast toast-error"))

    supabase = await get_supabase_admin()
    row = (
        await supabase.table("transactions").select("*").eq("id", tx_id).single().execute()
    ).data
    if not row:
        return Div(Div("Deal not found.", cls="toast toast-error"))
    tx = Transaction(**row)

    new_urls: list[str] = []
    for photo_file in valid_files:
        file_bytes = await photo_file.read()
        if len(file_bytes) > 10 * 1024 * 1024:
            return Div(Div(f"Photo '{photo_file.filename}' exceeds 10 MB limit.", cls="toast toast-error"))
        img_err = _validate_image_file(file_bytes, photo_file.filename)
        if img_err:
            return Div(Div(img_err, cls="toast toast-error"))
        if not cfg.mock_uploads:
            try:
                result = verify_photo_liveness(file_bytes, tx.created_at, tx.amount_centavos)
                logger.info("Liveness OK tx=%s file=%s score=%d", tx_id, photo_file.filename, result.score)
            except VerificationFailed as e:
                return Div(Div(f"Photo rejected: {e}", cls="toast toast-error"))
        try:
            url = await upload_evidence_photo(file_bytes, photo_file.filename, tx_id)
            new_urls.append(url)
        except ValueError as e:
            return Div(Div(str(e), cls="toast toast-error"))
        except Exception as e:
            logger.exception("Evidence upload failed tx=%s", tx_id)
            return Div(Div(f"Upload failed: {e}", cls="toast toast-error"))

    all_urls = tx.evidence_photo_urls + new_urls

    await supabase.table("transactions").update({
        "evidence_photo_urls": all_urls,
        "status": TransactionStatus.EVIDENCE_SUBMITTED,
        "updated_at": _dt.utcnow().isoformat(),
    }).eq("id", tx_id).execute()

    user_id = get_session_user(session)
    lat, lon = _parse_location(form)
    await log_event(tx_id, "evidence_submitted",
        f"{len(new_urls)} photo(s) uploaded · {len(all_urls)} total — liveness verified ✓",
        actor_id=user_id, lat=lat, lon=lon)
    await _bust_tx_lists(tx.buyer_id, tx.seller_id)
    asyncio.create_task(notify_user(tx.buyer_id, "Evidence Photos Uploaded 📸",
        "The seller submitted evidence photos. Review them and wait for shipment.",
        f"/transactions/{tx_id}"))
    logger.info("Evidence submitted tx=%s photos=%d", tx_id, len(all_urls))
    return Div(
        Div("Evidence submitted!", cls="toast toast-success"),
        Script("setTimeout(() => location.reload(), 1200);"),
    )


@rt("/transactions/unboxing")
async def post(request: Request, session):
    """Accept unboxing video upload, store to Supabase Storage."""
    if not get_session_user(session):
        return Div(Div("Session expired.", cls="toast toast-error"))

    form  = await request.form()
    tx_id = form.get("tx_id")
    video = form.get("video")

    if not tx_id:
        return Div(Div("Missing deal ID.", cls="toast toast-error"))
    if not video or not getattr(video, "filename", None):
        return Div(Div("Please select a video file.", cls="toast toast-error"))

    file_bytes = await video.read()
    if len(file_bytes) > 100 * 1024 * 1024:
        return Div(Div("Video exceeds 100 MB limit.", cls="toast toast-error"))
    vid_err = _validate_video_file(video.filename, video.content_type or "")
    if vid_err:
        return Div(Div(vid_err, cls="toast toast-error"))

    try:
        url = await upload_unboxing_video(file_bytes, video.filename, tx_id)
    except ValueError as e:
        return Div(Div(str(e), cls="toast toast-error"))
    except Exception as e:
        logger.exception("Unboxing upload failed tx=%s", tx_id)
        return Div(Div(f"Upload failed: {e}", cls="toast toast-error"))


    supabase = await get_supabase_admin()
    await supabase.table("transactions").update({
        "unboxing_video_url": url,
        "status": TransactionStatus.UNBOXING_UPLOADED,
        "updated_at": _dt.utcnow().isoformat(),
    }).eq("id", tx_id).execute()

    user_id = get_session_user(session)
    lat, lon = _parse_location(form)
    await log_event(tx_id, "unboxing_uploaded",
        "Unboxing video recorded — buyer can now release payment to seller",
        actor_id=user_id, lat=lat, lon=lon)
    await _bust_tx_lists(tx.buyer_id, tx.seller_id)
    # Need tx object for seller_id
    supabase2 = await get_supabase_admin()
    tx_row = (await supabase2.table("transactions").select("seller_id,amount_centavos").eq("id", tx_id).single().execute()).data
    if tx_row:
        asyncio.create_task(notify_user(tx_row["seller_id"], "Unboxing Video Uploaded 🎥",
            "The buyer recorded their unboxing. Payment release is pending.",
            f"/transactions/{tx_id}"))
    logger.info("Unboxing video uploaded tx=%s", tx_id)
    return Div(
        Div("Video uploaded! You can now release the payment.", cls="toast toast-success"),
        Script("setTimeout(() => location.reload(), 1200);"),
    )


@rt("/transactions/ship")
async def post(request: Request, session):
    user_id = get_session_user(session)
    if not user_id:
        return Div(Div("Session expired.", cls="toast toast-error"))
    form       = await request.form()
    tx_id      = str(form.get("tx_id", "")).strip()
    tracking_id = str(form.get("tracking_id", "")).strip()
    lat, lon   = _parse_location(form)
    supabase = await get_supabase_admin()
    tx_row = (await supabase.table("transactions").select("buyer_id,amount_centavos").eq("id", tx_id).single().execute()).data
    await supabase.table("transactions").update({
        "delivery_tracking_id": tracking_id,
        "status": TransactionStatus.IN_TRANSIT,
    }).eq("id", tx_id).execute()
    await log_event(tx_id, "item_shipped",
        f"Item shipped · Tracking: {tracking_id}",
        actor_id=user_id, lat=lat, lon=lon)
    await _bust_tx_lists(user_id)
    if tx_row:
        asyncio.create_task(notify_user(tx_row["buyer_id"], "Item Shipped 🚚",
            f"Your item is on the way! Tracking: {tracking_id}. Record your unboxing video on delivery.",
            f"/transactions/{tx_id}"))
    logger.info("Shipment added tx=%s tracking=%s", tx_id, tracking_id)
    return Div(
        Div("Marked as shipped!", cls="toast toast-success"),
        Script("setTimeout(() => location.reload(), 1200);"),
    )


@rt("/transactions/release")
async def post(request: Request, session):
    user_id = get_session_user(session)
    if not user_id:
        return Div(Div("Session expired.", cls="toast toast-error"))

    form  = await request.form()
    tx_id = form.get("tx_id", "").strip()
    # Collect PIN from named digit fields (primary) or single field (fallback)
    pin_digits = "".join(form.get(f"pin-{i}", "") for i in range(4)).strip()
    pin = pin_digits if len(pin_digits) == 4 else form.get("pin", "").strip()

    supabase = await get_supabase_admin()

    # Check PIN lockout before any DB query
    lockout_msg = _check_pin_lockout(user_id)
    if lockout_msg:
        return Div(Div(lockout_msg, cls="toast toast-error"))

    # Verify PIN if the user has one set
    user_row = (
        await supabase.table("users").select("pin_hash").eq("id", user_id).single().execute()
    ).data
    if user_row and user_row.get("pin_hash"):
        if not pin:
            return Div(Div("Please enter your PIN to confirm this action.", cls="toast toast-error"))
        valid, needs_rehash = verify_pin(pin, user_row["pin_hash"])
        if not valid:
            _record_pin_fail(user_id)
            lockout_msg = _check_pin_lockout(user_id)
            err = lockout_msg or "Incorrect PIN. Please try again."
            return Div(Div(err, cls="toast toast-error"))
        _clear_pin_lockout(user_id)
        if needs_rehash:
            async def _upgrade_pin():
                new_hash = hash_pin(pin)
                sb = await get_supabase_admin()
                await sb.table("users").update({"pin_hash": new_hash}).eq("id", user_id).execute()
            asyncio.create_task(_upgrade_pin())

    row = (
        await supabase.table("transactions").select("*").eq("id", tx_id).single().execute()
    ).data
    if not row:
        return Div(Div("Deal not found.", cls="toast toast-error"))
    tx = Transaction(**row)
    try:
        check_release_gate(
            tx.evidence_photo_urls,
            tx.unboxing_video_url,
            tx.delivery_tracking_id,
            tx.amount_centavos,
        )
    except VerificationFailed as e:
        return Div(Div(str(e), cls="toast toast-error"))
    lat, lon = _parse_location(form)
    try:
        await release_escrow(tx)
        await _bust_tx_lists(tx.buyer_id, tx.seller_id)
        await log_event(tx_id, "payment_released",
            f"₱{tx.amount_centavos / 100:,.0f} released to seller — deal complete",
            actor_id=user_id, lat=lat, lon=lon)
        asyncio.create_task(notify_user(tx.seller_id, "Payment Released ✅",
            f"₱{tx.amount_centavos/100:,.0f} has been released to you. Deal complete!",
            f"/transactions/{tx_id}"))
        return Div(
            Div("Payment released to seller!", cls="toast toast-success"),
            Script("setTimeout(() => location.reload(), 1200);"),
        )
    except Exception as e:
        logger.exception("release_escrow failed tx=%s", tx_id)
        return Div(Div(f"Release failed: {e}", cls="toast toast-error"))


@rt("/transactions/dispute")
async def post(request: Request, session):
    user_id = get_session_user(session)
    if not user_id:
        return Div(Div("Session expired.", cls="toast toast-error"))
    form   = await request.form()
    tx_id  = str(form.get("tx_id", "")).strip()
    reason = str(form.get("reason", "")).strip()[:500]
    lat, lon = _parse_location(form)
    if len(reason) < 10:
        return Div(Div("Please describe the dispute in at least 10 characters.", cls="toast toast-error"))
    supabase = await get_supabase_admin()
    await supabase.table("transactions").update({
        "status": TransactionStatus.DISPUTED,
    }).eq("id", tx_id).execute()
    tx_row = (await supabase.table("transactions").select("buyer_id,seller_id").eq("id", tx_id).single().execute()).data
    await log_event(tx_id, "dispute_raised",
        f'Dispute opened: \"{reason[:120]}\" — evidence under review',
        actor_id=user_id, lat=lat, lon=lon)
    await _bust_tx_lists(user_id)
    if tx_row:
        other_id = tx_row["seller_id"] if user_id == tx_row["buyer_id"] else tx_row["buyer_id"]
        asyncio.create_task(notify_user(other_id, "Dispute Raised ⚠️",
            "A dispute has been opened on your deal. Teluka will review the evidence.",
            f"/transactions/{tx_id}"))
    logger.info("Dispute raised tx=%s reason=%r", tx_id, reason[:100])
    return Div(
        Div("Dispute raised. Our team will review the evidence.", cls="toast toast-warn"),
        Script("setTimeout(() => location.reload(), 1500);"),
    )


@rt("/transactions/cancel")
async def post(tx_id: str, session):
    if not get_session_user(session):
        return Div(Div("Session expired.", cls="toast toast-error"))
    supabase = await get_supabase_admin()
    row = (
        await supabase.table("transactions").select("*").eq("id", tx_id).single().execute()
    ).data
    if not row:
        return Div(Div("Deal not found.", cls="toast toast-error"))
    tx = Transaction(**row)
    user_id = get_session_user(session)
    try:
        await cancel_escrow(tx)
        await _bust_tx_lists(tx.buyer_id, tx.seller_id)
        event_type = "deal_refunded" if tx.payment_intent_id else "deal_cancelled"
        desc = "Funds refunded to buyer" if tx.payment_intent_id else "Deal cancelled before payment"
        await log_event(tx_id, event_type, desc, actor_id=user_id)
        return Div(
            Div("Deal cancelled.", cls="toast toast-warn"),
            Script("setTimeout(() => { window.location.href = '/dashboard'; }, 1200);"),
        )
    except Exception as e:
        logger.exception("cancel_escrow failed tx=%s", tx_id)
        return Div(Div(f"Cancellation failed: {e}", cls="toast toast-error"))


# ---------------------------------------------------------------------------
# Activity feed (HTMX polling)
# ---------------------------------------------------------------------------

@rt("/transactions/{tx_id}/activity")
async def get(tx_id: str, session):
    """Returns the activity timeline fragment — polled every 4s by HTMX."""
    user_id = get_session_user(session)
    if not user_id:
        return Div()

    act_key = f"activity:{tx_id}"
    cached  = cache.get(act_key)
    if cached is None:
        supabase = await get_supabase_admin()
        row = (
            await supabase.table("transactions")
            .select("buyer_id,seller_id")
            .eq("id", tx_id)
            .single()
            .execute()
        ).data
        events = await get_events(tx_id) if row else []
        cached = {"row": row, "events": events}
        cache.set(act_key, cached, TTL_ACTIVITY)

    row    = cached["row"]
    events = cached["events"]

    if not row or user_id not in (row["buyer_id"], row["seller_id"]):
        return Div()
    if not events:
        return Div(cls="activity-empty")("No activity yet.")

    items = []
    for ev in events:
        rel = format_relative_time(ev["created_at"])
        items.append(
            Div(cls="activity-item")(
                Div(cls="activity-dot")(ev["icon"]),
                Div(cls="activity-body")(
                    Div(cls="activity-title")(ev["title"]),
                    Div(cls="activity-desc")(ev["description"]),
                    Div(cls="activity-time")(rel),
                ),
            )
        )
    return Div(cls="activity-list")(*items)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Apply middleware last — after all routes are registered on fapp.
# Wrapping earlier replaces `app` with a plain ASGI object that has no
# .get() / .post() methods, breaking every route decorator above.
# ---------------------------------------------------------------------------
app = apply_middleware(fapp, is_production=cfg.is_production)


if __name__ == "__main__":
    serve()

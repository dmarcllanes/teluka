import logging
import logging.config

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
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles
from fasthtml.common import *

from components.pages.landing import landing_page
from components.pages.login import (
    login_page, otp_step, pin_step, identifier_form_fragment, signup_form_fragment,
)
from components.pages.dashboard import dashboard_page
from components.pages.profile import profile_page
from components.pages.new_deal import (
    new_deal_page, seller_found_card, seller_not_found, seller_blocked,
)
from components.pages.deal_detail import deal_detail_page
from lib.otp_store import (
    create_otp, get_or_create_user, verify_otp as check_otp,
    get_user_by_identifier, is_email,
)
from lib.pin import hash_pin, verify_pin, validate_pin
from lib.email_sender import send_otp_email, mask_email
from lib.storage import upload_evidence_photo, upload_unboxing_video
from core.escrow import cancel_escrow, initiate_escrow, release_escrow
from core.exceptions import ScamDetected, VerificationFailed
from core.forensics import analyze_risk
from core.verification import verify_photo_liveness, check_evidence_complete, check_release_gate
from core.tiers import get_tier, get_plan, PLANS
from lib.phone import normalize_ph_phone, PhoneValidationError
from lib.session import get_session_user, set_session_user, clear_session
from lib.middleware import apply_middleware
from lib.supabase_client import get_supabase_admin
from lib.activity import log_event, get_events, format_relative_time
from schemas.transaction import CreateTransactionRequest, Transaction, TransactionStatus
from schemas.user import UserProfile

fapp, rt = fast_app(secret_key=cfg.session_secret)
fapp.mount("/static", StaticFiles(directory="static"), name="static")

logger.info("Teluka starting — env=%s", cfg.env)


# ---------------------------------------------------------------------------
# Health check (used by deployment platforms)
# ---------------------------------------------------------------------------

@fapp.get("/health")
async def health():
    return JSONResponse({"status": "ok", "env": cfg.env})


# ---------------------------------------------------------------------------
# Landing
# ---------------------------------------------------------------------------

@rt("/")
def get():
    return landing_page()


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
async def post(identifier: str):
    """
    Step 1: user enters phone or email.
    - Phone + existing user  → send OTP to their email → otp_step
    - Phone + new user       → ask for email → register_email_step
    - Email + existing user  → send OTP to that email → otp_step
    - Email + not found      → error
    """
    identifier = identifier.strip()

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
            code = await create_otp(email)
            sent = await send_otp_email(email, code)
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
        # New user — pre-fill phone in signup form and switch to signup tab
        return signup_form_fragment(phone=normalised)

    email = user.get("email")
    if not email:
        return identifier_form_fragment(
            error="Account has no email on file. Please contact support."
        )

    try:
        code = await create_otp(email)
        sent = await send_otp_email(email, code)
        if not sent:
            return identifier_form_fragment(error="Failed to send email. Please try again.")
    except ValueError as e:
        return identifier_form_fragment(error=str(e))
    except Exception:
        logger.exception("check-identifier phone send error")
        return identifier_form_fragment(error="Something went wrong. Please try again.")

    return otp_step(mask_email(email), email)


@rt("/register")
async def post(phone: str, email: str):
    """
    Step 2 for new users: phone (already normalised) + email.
    Creates OTP keyed on email, sends it, returns otp_step.
    """
    email = email.strip().lower()

    if not is_email(email):
        return signup_form_fragment(phone=phone, error="Please enter a valid email address.")

    # Check email not already taken
    existing = await get_user_by_identifier(email)
    if existing:
        return signup_form_fragment(
            phone=phone,
            error="That email is already linked to another account. Use a different email.",
        )

    try:
        code = await create_otp(email)
        sent = await send_otp_email(email, code)
        if not sent:
            return signup_form_fragment(phone=phone, error="Failed to send email. Please try again.")
    except ValueError as e:
        return signup_form_fragment(phone=phone, error=str(e))
    except Exception:
        logger.exception("register send error")
        return signup_form_fragment(phone=phone, error="Something went wrong. Please try again.")

    # Store phone in hidden field via otp_step so verify-otp can create the user
    # We pass phone encoded into the email field's companion hidden input
    return otp_step(mask_email(email), email, _phone=phone)


@rt("/resend-otp")
async def post(email: str):
    """Re-send OTP to the same email."""
    try:
        code = await create_otp(email)
        sent = await send_otp_email(email, code)
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

    ok, error_msg = await check_otp(email, clean_otp)
    if not ok:
        return Div(Div(error_msg, cls="toast toast-error"))

    try:
        user = await get_user_by_identifier(email)
        if user:
            # Existing user — log in directly
            user_id    = user["id"]
            user_phone = user["phone"]
            set_session_user(session, user_id, user_phone)
        elif phone:
            # New user — go to PIN creation step before creating account
            return pin_step(phone=phone, email=email)
        else:
            return Div(Div("Account error. Please start over.", cls="toast toast-error"))
    except Exception:
        logger.exception("verify-otp: session setup failed")
        return Div(Div("Account error. Please contact support.", cls="toast toast-error"))

    logger.info("User logged in user=%s", user_id)
    return Div(
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
        set_session_user(session, user_id, phone)
    except Exception:
        logger.exception("set-pin: user creation failed")
        return Div(Div("Account error. Please contact support.", cls="toast toast-error"))

    logger.info("New user created with PIN user=%s", user_id)
    return Div(
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

    supabase = await get_supabase_admin()

    user_row = (
        await supabase.table("users").select("*").eq("id", user_id).single().execute()
    ).data
    if not user_row:
        session.clear()
        return RedirectResponse("/login", status_code=303)

    user = UserProfile(**user_row)

    tx_rows = (
        await supabase.table("transactions")
        .select("*")
        .or_(f"buyer_id.eq.{user_id},seller_id.eq.{user_id}")
        .order("created_at", desc=True)
        .execute()
    ).data or []

    transactions = [Transaction(**r) for r in tx_rows]
    return dashboard_page(user, transactions)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@rt("/profile")
async def get(session):
    user_id = get_session_user(session)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    supabase = await get_supabase_admin()

    user_row = (
        await supabase.table("users").select("*").eq("id", user_id).single().execute()
    ).data
    if not user_row:
        session.clear()
        return RedirectResponse("/login", status_code=303)

    user = UserProfile(**user_row)

    tx_rows = (
        await supabase.table("transactions")
        .select("*")
        .or_(f"buyer_id.eq.{user_id},seller_id.eq.{user_id}")
        .execute()
    ).data or []

    transactions = [Transaction(**r) for r in tx_rows]
    return profile_page(user, transactions)


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

    seller_row = (
        await supabase.table("users").select("*").eq("phone", normalised).single().execute()
    ).data
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
async def post(item_description: str, amount_php: float, seller_id: str, session,
               protection_plan: str = "basic"):
    buyer_id = get_session_user(session)
    if not buyer_id:
        return Div(Div("Session expired.", cls="toast toast-error"))

    amount_centavos = int(float(amount_php) * 100)
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
        actor_id=buyer_id)
    await log_event(tx_id, "tier_upgraded",
        f"{plan.badge_icon} {plan.name} protection active \u00b7 {plan.min_photos} photos, {plan.review_hours}h review"
        + (f" \u00b7 Service fee: \u20b1{fee / 100:,.2f}" if fee else " \u00b7 No service fee"),
        icon=plan.badge_icon)

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

    buyer_row  = (await supabase.table("users").select("*").eq("id", tx.buyer_id).single().execute()).data
    seller_row = (await supabase.table("users").select("*").eq("id", tx.seller_id).single().execute()).data
    buyer  = UserProfile(**buyer_row)  if buyer_row  else None
    seller = UserProfile(**seller_row) if seller_row else None

    return deal_detail_page(tx, buyer, seller, user_id)


# ---------------------------------------------------------------------------
# Escrow actions
# ---------------------------------------------------------------------------

@rt("/transactions/pay")
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
        await initiate_escrow(tx)
        await log_event(tx_id, "payment_held",
            f"₱{tx.amount_centavos / 100:,.0f} held securely — seller cannot access funds until you confirm",
            actor_id=user_id)
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
    await log_event(tx_id, "evidence_submitted",
        f"{len(new_urls)} photo(s) uploaded · {len(all_urls)} total — liveness verified ✓",
        actor_id=user_id)
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
    await log_event(tx_id, "unboxing_uploaded",
        "Unboxing video recorded — buyer can now release payment to seller",
        actor_id=user_id)
    logger.info("Unboxing video uploaded tx=%s", tx_id)
    return Div(
        Div("Video uploaded! You can now release the payment.", cls="toast toast-success"),
        Script("setTimeout(() => location.reload(), 1200);"),
    )


@rt("/transactions/ship")
async def post(tx_id: str, tracking_id: str, session):
    if not get_session_user(session):
        return Div(Div("Session expired.", cls="toast toast-error"))
    supabase = await get_supabase_admin()
    await supabase.table("transactions").update({
        "delivery_tracking_id": tracking_id,
        "status": TransactionStatus.IN_TRANSIT,
    }).eq("id", tx_id).execute()
    user_id = get_session_user(session)
    await log_event(tx_id, "item_shipped",
        f"Item shipped · Tracking: {tracking_id}",
        actor_id=user_id)
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

    # Verify PIN if the user has one set
    user_row = (
        await supabase.table("users").select("pin_hash").eq("id", user_id).single().execute()
    ).data
    if user_row and user_row.get("pin_hash"):
        if not pin:
            return Div(Div("Please enter your PIN to confirm this action.", cls="toast toast-error"))
        if not verify_pin(pin, user_row["pin_hash"]):
            return Div(Div("Incorrect PIN. Please try again.", cls="toast toast-error"))

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
    try:
        await release_escrow(tx)
        await log_event(tx_id, "payment_released",
            f"₱{tx.amount_centavos / 100:,.0f} released to seller — deal complete",
            actor_id=user_id)
        return Div(
            Div("Payment released to seller!", cls="toast toast-success"),
            Script("setTimeout(() => location.reload(), 1200);"),
        )
    except Exception as e:
        logger.exception("release_escrow failed tx=%s", tx_id)
        return Div(Div(f"Release failed: {e}", cls="toast toast-error"))


@rt("/transactions/dispute")
async def post(tx_id: str, reason: str, session):
    if not get_session_user(session):
        return Div(Div("Session expired.", cls="toast toast-error"))
    supabase = await get_supabase_admin()
    await supabase.table("transactions").update({
        "status": TransactionStatus.DISPUTED,
    }).eq("id", tx_id).execute()
    user_id = get_session_user(session)
    await log_event(tx_id, "dispute_raised",
        f'Dispute opened: \"{reason[:120]}\" — evidence under review',
        actor_id=user_id)
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

    # Security: only buyer/seller may view
    supabase = await get_supabase_admin()
    row = (
        await supabase.table("transactions")
        .select("buyer_id,seller_id")
        .eq("id", tx_id)
        .single()
        .execute()
    ).data
    if not row or user_id not in (row["buyer_id"], row["seller_id"]):
        return Div()

    events = await get_events(tx_id)
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

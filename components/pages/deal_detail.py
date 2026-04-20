from fasthtml.common import *

from core.tiers import get_tier, get_plan
from schemas.transaction import Transaction, TransactionStatus
from schemas.user import UserProfile


# Ordered steps for the progress stepper
_STEPS = [
    (TransactionStatus.PENDING,            "Agreed",    "Waiting for payment"),
    (TransactionStatus.ESCROWED,           "Paid",      "Money held safely"),
    (TransactionStatus.EVIDENCE_SUBMITTED, "Photos",    "Real photos sent"),
    (TransactionStatus.IN_TRANSIT,         "Shipped",   "On the way"),
    (TransactionStatus.DELIVERED,          "Received",  "Item arrived"),
    (TransactionStatus.COMPLETED,          "Done ✓",    "Seller paid"),
]

_ACTIVE_STATUSES = {
    TransactionStatus.PENDING,
    TransactionStatus.ESCROWED,
    TransactionStatus.EVIDENCE_SUBMITTED,
    TransactionStatus.IN_TRANSIT,
    TransactionStatus.DELIVERED,
    TransactionStatus.UNBOXING_UPLOADED,
}

_STATUS_ICON = {
    TransactionStatus.PENDING:            "⏳",
    TransactionStatus.ESCROWED:           "🔒",
    TransactionStatus.EVIDENCE_SUBMITTED: "📸",
    TransactionStatus.IN_TRANSIT:         "🚚",
    TransactionStatus.DELIVERED:          "📦",
    TransactionStatus.UNBOXING_UPLOADED:  "🎥",
    TransactionStatus.COMPLETED:          "✅",
    TransactionStatus.DISPUTED:           "⚠️",
    TransactionStatus.CANCELLED:          "❌",
    TransactionStatus.REFUNDED:           "↩️",
}


def deal_detail_page(
    tx: Transaction,
    buyer: UserProfile | None,
    seller: UserProfile | None,
    current_user_id: str,
) -> FT:
    is_buyer  = tx.buyer_id  == current_user_id
    is_seller = tx.seller_id == current_user_id

    return Html(
        _head(tx.item_description),
        Body(
            Div(cls="app-layout")(
                _sidebar(),
                Div(cls="dash-body")(
                    _app_header(tx),
                    Main(cls="app-main")(
                        Div(cls="app-content")(
                            _deal_content(tx, buyer, seller, is_buyer, is_seller),
                        ),
                    ),
                    _bottom_nav(),
                ),
            ),
            Div(id="flash"),
            _scripts(),
        ),
    )


# ─── Main content ─────────────────────────────────────────────────────────

def _deal_content(
    tx: Transaction,
    buyer: UserProfile | None,
    seller: UserProfile | None,
    is_buyer: bool,
    is_seller: bool,
) -> FT:
    plan = get_plan(getattr(tx, "protection_plan", "basic")) if hasattr(tx, "protection_plan") else get_tier(tx.amount_centavos)
    return (
        _status_stepper(tx),
        _deal_info_card(tx, buyer, seller, plan),
        _action_area(tx, is_buyer, is_seller, plan),
        _activity_feed(tx.id),
    )


def _status_stepper(tx: Transaction) -> FT:
    # Map status to step index
    status_order = [s for s, _, _ in _STEPS]
    if tx.status in (TransactionStatus.DISPUTED, TransactionStatus.CANCELLED, TransactionStatus.REFUNDED):
        current_idx = -1  # terminal non-success states
    else:
        try:
            current_idx = status_order.index(tx.status)
        except ValueError:
            current_idx = 0

    steps_html = []
    for i, (status, label, sublabel) in enumerate(_STEPS):
        if current_idx == -1:
            state = "done" if i < len(_STEPS) else ""
        elif i < current_idx:
            state = "done"
        elif i == current_idx:
            state = "active"
        else:
            state = ""

        steps_html.append(
            Div(cls=f"stepper-step {state}")(
                Div(cls="stepper-dot")(
                    Span("✓") if state == "done" else Span(str(i + 1))
                ),
                Div(cls="stepper-label")(label),
            )
        )
        if i < len(_STEPS) - 1:
            steps_html.append(
                Div(cls=f"stepper-line {'done' if i < current_idx else ''}")
            )

    # Disputed / cancelled banner
    terminal_banner = None
    if tx.status == TransactionStatus.DISPUTED:
        terminal_banner = Div(cls="deal-banner banner-disputed")(
            "⚠️ This deal is under dispute. Evidence is being reviewed."
        )
    elif tx.status == TransactionStatus.CANCELLED:
        terminal_banner = Div(cls="deal-banner banner-cancelled")(
            "❌ This deal was cancelled."
        )
    elif tx.status == TransactionStatus.REFUNDED:
        terminal_banner = Div(cls="deal-banner banner-cancelled")(
            "↩️ Funds have been refunded to the buyer."
        )
    elif tx.status == TransactionStatus.COMPLETED:
        terminal_banner = Div(cls="deal-banner banner-completed")(
            "✅ Deal complete! Funds have been released to the seller."
        )

    return Div(cls="deal-stepper-wrap")(
        Div(cls="deal-stepper")(*steps_html),
        terminal_banner,
    )


def _deal_info_card(
    tx: Transaction,
    buyer: UserProfile | None,
    seller: UserProfile | None,
    tier=None,
) -> FT:
    amount = f"₱{tx.amount_centavos / 100:,.2f}"
    date   = tx.created_at.strftime("%-d %b %Y · %-I:%M %p") if tx.created_at else ""
    if tier is None:
        tier = get_tier(tx.amount_centavos)

    def _party(label: str, user: UserProfile | None) -> FT:
        if not user:
            return Div(cls="deal-party")(
                Div(cls="deal-party-label")(label),
                Div("—", cls="deal-party-phone"),
            )
        phone   = user.phone
        masked  = phone
        initial = phone[-4:]
        return Div(cls="deal-party")(
            Div(cls="deal-party-label")(label),
            Div(cls="deal-party-row")(
                Div(initial, cls="deal-mini-avatar"),
                Div(masked, cls="deal-party-phone"),
            ),
        )

    fee = tx.platform_fee_centavos if hasattr(tx, "platform_fee_centavos") else 0
    total = f"\u20b1{(tx.amount_centavos + fee) / 100:,.2f}"
    return Div(cls="deal-info-card")(
        Div(cls="deal-info-header")(
            Div(cls="deal-item-icon")(_STATUS_ICON.get(tx.status, "📋")),
            Div(
                Div(tx.item_description, cls="deal-item-name"),
                Div(date, style="font-size:0.75rem;color:var(--muted)"),
            ),
        ),
        Div(cls="deal-amount")(total),
        Div(cls=tier.badge_cls)(
            Span(tier.badge_icon), " ", Span(f"{tier.label} Protection"),
            Span(f" \u00b7 {tier.tagline}", cls="tier-badge-desc"),
        ),
        Div(cls="deal-fee-breakdown")(
            Div(cls="deal-fee-row")(
                Span("Item amount", cls="deal-fee-label"),
                Span(amount, cls="deal-fee-val"),
            ),
            Div(cls="deal-fee-row")(
                Span("Teluka fee", cls="deal-fee-label"),
                Span(f"\u20b1{fee / 100:,.2f}", cls="deal-fee-val deal-fee-service"),
            ),
        ),
        Div(cls="deal-parties")(
            _party("Buyer",  buyer),
            Div(cls="deal-parties-arrow")("→"),
            _party("Seller", seller),
        ),
        Div(cls="deal-id-row")(
            Div(f"Deal ID: {tx.id[:8]}…", cls="deal-id", id="deal-id-text"),
            Button(
                NotStr('<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>'),
                Span("Copy", id="copy-label"),
                cls="deal-id-copy", id="copy-btn", type="button",
                onclick=f"copyDealId('{tx.id}')",
            ),
        ),
    )


# ─── Action area ──────────────────────────────────────────────────────────

def _countdown_card(tx: Transaction, review_hours: int = 48) -> FT | None:
    """Review window countdown — hours depend on security tier."""
    if tx.status != TransactionStatus.EVIDENCE_SUBMITTED:
        return None
    deadline_attr = tx.updated_at.isoformat() if tx.updated_at else tx.created_at.isoformat() if tx.created_at else ""
    return Div(cls="countdown-card")(
        Div(cls="countdown-icon")("⏱️"),
        Div(cls="countdown-body")(
            Div("Buyer review window", cls="countdown-label"),
            Div(id="countdown-display", cls="countdown-time")("Calculating…"),
            Div(f"{review_hours} hours to inspect — then funds auto-release", cls="countdown-sub"),
        ),
        Script(f"""
(function() {{
  var deadline = new Date('{deadline_attr}');
  deadline.setHours(deadline.getHours() + {review_hours});
  function update() {{
    var now = new Date();
    var diff = deadline - now;
    if (diff <= 0) {{ document.getElementById('countdown-display').textContent = 'Expired'; return; }}
    var h = Math.floor(diff / 3600000);
    var m = Math.floor((diff % 3600000) / 60000);
    var s = Math.floor((diff % 60000) / 1000);
    document.getElementById('countdown-display').textContent =
      String(h).padStart(2,'0') + ':' + String(m).padStart(2,'0') + ':' + String(s).padStart(2,'0');
    setTimeout(update, 1000);
  }}
  update();
}})();
        """),
    )


def _action_area(tx: Transaction, is_buyer: bool, is_seller: bool, tier=None) -> FT:
    if tier is None:
        tier = get_tier(tx.amount_centavos)
    actions = []

    # Countdown timer for buyer review window
    countdown = _countdown_card(tx, review_hours=tier.review_hours)
    if countdown:
        actions.append(countdown)

    # ── Tier 3: high-value deal warning (shown to buyer before paying) ─────
    if tier.id == "premium" and tx.status == TransactionStatus.PENDING and is_buyer:
        actions.append(
            Div(cls="action-card action-card-tier3")(
                Div(cls="action-card-title")("🏦 High-Value Deal — Extra Protection Active"),
                P(
                    f"This deal (₱{tx.amount_centavos / 100:,.0f}) requires {tier.min_photos} evidence photos, "
                    f"a courier tracking number, and a {tier.review_hours}-hour inspection window. "
                    "Only proceed if the seller is KYC-verified (GCash/Maya).",
                    cls="action-card-desc",
                ),
            )
        )

    # ── Buyer: pay ────────────────────────────────────────────────────────
    if is_buyer and tx.status == TransactionStatus.PENDING:
        actions.append(
            Div(cls="action-card")(
                Div(cls="action-card-title")("💳 Your turn to pay"),
                P("Your money will be held safely — the seller won't receive it until you confirm everything is correct.",
                  cls="action-card-desc"),
                Form(
                    Input(type="hidden", name="tx_id", value=tx.id),
                    Button(
                        Span("Pay & Hold Funds"),
                        Span(cls="htmx-indicator"),
                        type="submit", cls="btn btn-primary btn-block",
                    ),
                    hx_post="/transactions/pay",
                    hx_target="#flash",
                    hx_swap="innerHTML",
                    hx_indicator="find .htmx-indicator",
                ),
            )
        )

    # ── Seller: upload evidence ────────────────────────────────────────────
    if is_seller and tx.status == TransactionStatus.ESCROWED:
        already = len(tx.evidence_photo_urls)
        needed  = max(0, tier.min_photos - already)
        photo_sub = (
            f"{already}/{tier.min_photos} photos uploaded — {needed} more needed"
            if already > 0
            else f"{tier.min_photos} photos required ({tier.label} deal)"
        )
        actions.append(
            Div(cls="action-card")(
                Div(cls="action-card-title")("📸 Upload real photos of the item"),
                P(f"Take photos right now — must be fresh. {photo_sub}.",
                  cls="action-card-desc"),
                Form(
                    Input(type="hidden", name="tx_id", value=tx.id),
                    Div(cls="form-group")(
                        Div(cls="file-drop-zone", id="photo-drop", onclick="document.getElementById('photo-input').click()")(
                            Input(
                                name="photos", type="file",
                                accept="image/jpeg,image/png,image/webp",
                                multiple=True, required=True,
                                id="photo-input",
                                onchange="showFilePreviews(this,'photo-preview','📸')",
                                style="display:none",
                            ),
                            Div(cls="file-drop-icon")("📷"),
                            Div(cls="file-drop-text")(
                                Span("Tap to choose photos"), " or drag them here"
                            ),
                            Div(f"JPEG / PNG / WebP · Max 10 MB each · Min {tier.min_photos} photos", cls="file-drop-hint"),
                        ),
                        Div(cls="file-preview-list", id="photo-preview"),
                    ),
                    Button(
                        Span("Submit Photos"),
                        Span(cls="htmx-indicator"),
                        type="submit", cls="btn btn-primary btn-block",
                    ),
                    hx_post="/transactions/evidence",
                    hx_target="#flash",
                    hx_swap="innerHTML",
                    hx_indicator="find .htmx-indicator",
                    hx_encoding="multipart/form-data",
                ),
            )
        )

    # ── Seller: add tracking ───────────────────────────────────────────────
    if is_seller and tx.status == TransactionStatus.EVIDENCE_SUBMITTED:
        actions.append(
            Div(cls="action-card")(
                Div(cls="action-card-title")("🚚 Ship the item"),
                P("Ship it via Lalamove, J&T, or any courier — then paste the tracking number here.",
                  cls="action-card-desc"),
                Form(
                    Input(type="hidden", name="tx_id", value=tx.id),
                    Div(cls="form-group")(
                        Label("Tracking ID", cls="form-label"),
                        Input(name="tracking_id", cls="form-input",
                              placeholder="e.g. JT1234567890PH", required=True),
                    ),
                    Button(
                        Span("Mark as Shipped"),
                        Span(cls="htmx-indicator"),
                        type="submit", cls="btn btn-primary btn-block",
                    ),
                    hx_post="/transactions/ship",
                    hx_target="#flash",
                    hx_swap="innerHTML",
                    hx_indicator="find .htmx-indicator",
                ),
            )
        )

    # ── Buyer: upload unboxing video ──────────────────────────────────────
    if is_buyer and tx.status == TransactionStatus.DELIVERED:
        actions.append(
            Div(cls="action-card")(
                Div(cls="action-card-title")("🎥 Record yourself opening the package"),
                P("Just a short video of you opening the box. This protects you if something's wrong inside.",
                  cls="action-card-desc"),
                Form(
                    Input(type="hidden", name="tx_id", value=tx.id),
                    Div(cls="form-group")(
                        Div(cls="file-drop-zone", id="video-drop", onclick="document.getElementById('video-input').click()")(
                            Input(
                                name="video", type="file",
                                accept="video/mp4,video/quicktime,video/webm",
                                required=True, id="video-input",
                                onchange="showFilePreviews(this,'video-preview','🎥')",
                                style="display:none",
                            ),
                            Div(cls="file-drop-icon")("🎬"),
                            Div(cls="file-drop-text")(
                                Span("Tap to choose video"), " or drag here"
                            ),
                            Div("MP4 / MOV / WebM · Max 100 MB", cls="file-drop-hint"),
                        ),
                        Div(cls="file-preview-list", id="video-preview"),
                    ),
                    Button(
                        Span("Upload Video"),
                        Span(cls="htmx-indicator"),
                        type="submit", cls="btn btn-primary btn-block",
                    ),
                    hx_post="/transactions/unboxing",
                    hx_target="#flash",
                    hx_swap="innerHTML",
                    hx_indicator="find .htmx-indicator",
                    hx_encoding="multipart/form-data",
                ),
            )
        )

    # ── Buyer: confirm delivery ────────────────────────────────────────────
    if is_buyer and tx.status in (
        TransactionStatus.UNBOXING_UPLOADED,
        TransactionStatus.IN_TRANSIT,
    ):
        actions.append(
            Div(cls="action-card")(
                Div(cls="action-card-title")("📦 Happy with it? Release payment"),
                P("Got exactly what you paid for? Enter your PIN and the seller receives their money.",
                  cls="action-card-desc"),
                Form(
                    id="release-form",
                    hx_post="/transactions/release",
                    hx_target="#flash",
                    hx_swap="innerHTML",
                    hx_indicator="find .htmx-indicator",
                )(
                    Input(type="hidden", name="tx_id", value=tx.id),
                    Div(cls="form-group", style="margin-bottom:16px;")(
                        Label("Enter your 4-digit PIN to confirm",
                              cls="form-label", style="text-align:center;display:block;"),
                        Div(cls="otp-wrap", id="release-pin-boxes")(
                            *[
                                Input(
                                    type="tel", maxlength="1",
                                    cls="otp-input release-pin-input",
                                    id=f"rpin-{i}",
                                    name=f"pin-{i}",
                                    inputmode="numeric",
                                    autocomplete="off",
                                    pattern="[0-9]",
                                )
                                for i in range(4)
                            ]
                        ),
                    ),
                    Button(
                        Span("Confirm & Release Payment"),
                        Span(cls="htmx-indicator"),
                        type="submit", id="release-submit",
                        cls="btn btn-primary btn-block",
                        disabled=True,
                    ),
                ),
                Script("""
(function(){
  var pins = document.querySelectorAll('.release-pin-input');
  var btn  = document.getElementById('release-submit');
  pins.forEach(function(inp, idx){
    inp.addEventListener('input', function(){
      inp.value = inp.value.replace(/\\D/g,'').slice(-1);
      if(inp.value && idx < pins.length-1) pins[idx+1].focus();
      if(btn) btn.disabled = !Array.from(pins).every(function(p){ return p.value.length===1; });
    });
    inp.addEventListener('keydown', function(e){
      if(e.key==='Backspace' && !inp.value && idx > 0) pins[idx-1].focus();
    });
  });
})();
                """),
            )
        )

    # ── Raise dispute (buyer OR seller, any active status) ─────────────────
    if tx.status in _ACTIVE_STATUSES and (is_buyer or is_seller):
        actions.append(
            Div(cls="action-card action-card-warn")(
                Div(cls="action-card-title")("⚠️ Something wrong?"),
                P("If the item is not as described or the seller is unresponsive, raise a dispute.",
                  cls="action-card-desc"),
                Form(
                    Input(type="hidden", name="tx_id", value=tx.id),
                    Div(cls="form-group")(
                        Label("Reason", cls="form-label"),
                        Input(name="reason", cls="form-input",
                              placeholder="Describe the issue briefly", required=True),
                    ),
                    Button(
                        Span("Raise Dispute"),
                        Span(cls="htmx-indicator"),
                        type="submit",
                        cls="btn btn-block",
                        style="background:rgba(251,113,133,0.15);color:#FB7185;border:1px solid rgba(251,113,133,0.3);border-radius:999px;padding:12px 24px;font-weight:700;cursor:pointer;font-family:inherit;font-size:0.95rem;",
                    ),
                    hx_post="/transactions/dispute",
                    hx_target="#flash",
                    hx_swap="innerHTML",
                    hx_indicator="find .htmx-indicator",
                ),
            )
        )

    # ── Cancel (buyer OR seller, only when PENDING — no payment yet) ─────────
    if (is_buyer or is_seller) and tx.status == TransactionStatus.PENDING:
        role = "buyer" if is_buyer else "seller"
        actions.append(
            Div(cls="action-card action-card-cancel")(
                Div(cls="action-card-title")("❌ Cancel this deal"),
                P(
                    "No payment has been made yet — you can cancel safely. "
                    "Both parties will be notified." if role == "buyer" else
                    "No payment has been made yet — you can cancel safely. "
                    "The buyer will be notified.",
                    cls="action-card-desc",
                ),
                Form(
                    Input(type="hidden", name="tx_id", value=tx.id),
                    Button(
                        "Cancel Deal",
                        type="submit",
                        cls="btn btn-ghost btn-block",
                        style="color:var(--muted);border-color:var(--border);",
                    ),
                    hx_post="/transactions/cancel",
                    hx_target="#flash",
                    hx_swap="innerHTML",
                ),
            )
        )

    # ── Request Admin Review (buyer OR seller, after payment) ─────────────
    _paid_statuses = {
        TransactionStatus.ESCROWED,
        TransactionStatus.EVIDENCE_SUBMITTED,
        TransactionStatus.IN_TRANSIT,
        TransactionStatus.DELIVERED,
        TransactionStatus.UNBOXING_UPLOADED,
    }
    if (is_buyer or is_seller) and tx.status in _paid_statuses:
        actions.append(
            Div(cls="action-card action-card-admin")(
                Div(cls="action-card-title")("🛡️ Need admin help?"),
                P(
                    "If you want to cancel this deal or something has gone wrong, "
                    "describe the issue and our team will review within 24 hours.",
                    cls="action-card-desc",
                ),
                Form(
                    Input(type="hidden", name="tx_id", value=tx.id),
                    Div(cls="form-group")(
                        Label("Describe the issue", cls="form-label"),
                        Input(
                            name="reason", cls="form-input",
                            placeholder="e.g. Item not as described, want to cancel…",
                            required=True,
                        ),
                    ),
                    Button(
                        Span("Request Admin Review"),
                        Span(cls="htmx-indicator"),
                        type="submit",
                        cls="btn btn-block",
                        style="background:rgba(59,130,246,0.12);color:#60A5FA;border:1px solid rgba(59,130,246,0.3);border-radius:999px;padding:12px 24px;font-weight:700;cursor:pointer;font-family:inherit;font-size:0.95rem;",
                    ),
                    hx_post="/transactions/admin-review",
                    hx_target="#flash",
                    hx_swap="innerHTML",
                    hx_indicator="find .htmx-indicator",
                ),
            )
        )

    if not actions:
        return Div()

    return Div(cls="action-area")(*actions)


# ─── Activity feed ────────────────────────────────────────────────────────

def _activity_feed(tx_id: str) -> FT:
    """Live activity timeline — HTMX polls every 4 seconds."""
    return Div(cls="activity-section")(
        Div(cls="activity-header")(
            Div(cls="activity-header-left")(
                Div(cls="activity-pulse-dot"),
                Span("Live Activity", cls="activity-header-title"),
            ),
            Span("Auto-updating", cls="activity-header-sub"),
        ),
        Div(
            id="activity-feed",
            cls="activity-feed",
            hx_get=f"/transactions/{tx_id}/activity",
            hx_trigger="load, every 4s",
            hx_swap="innerHTML",
        )(
            Div(cls="activity-skeleton")(
                *[Div(cls="activity-skeleton-row") for _ in range(3)]
            )
        ),
    )


# ─── Shared shell ─────────────────────────────────────────────────────────

def _sidebar() -> FT:
    return Aside(cls="dash-sidebar")(
        Div("Teluka", cls="sidebar-logo"),
        Nav(cls="sidebar-nav")(
            A(cls="sidebar-item active", href="/dashboard")(_icon_home(), "Home"),
            A(cls="sidebar-item sidebar-cta", href="/transactions/new")(_icon_plus(), "New Protected Deal"),
            A(cls="sidebar-item", href="/profile")(_icon_user(), "Profile"),
        ),
        Div(cls="sidebar-footer")(
            Button(_icon_sun(), _icon_moon(), "Appearance",
                cls="sidebar-item theme-toggle", onclick="toggleTheme()",
                style="width:100%;background:none;border:none;cursor:pointer;text-align:left;"),
            Form(action="/logout", method="post")(
                Button(_icon_logout(), "Sign out", cls="sidebar-item",
                    style="width:100%;background:none;border:none;cursor:pointer;text-align:left;"),
            ),
        ),
    )


def _app_header(tx: Transaction) -> FT:
    label = tx.item_description[:28] + "…" if len(tx.item_description) > 28 else tx.item_description
    return Header(cls="app-header")(
        Div(style="display:flex;align-items:center;gap:10px")(
            A("←", href="/dashboard",
              style="color:var(--muted);font-size:1.1rem;text-decoration:none;padding:4px 8px;border-radius:8px;"),
            Div(label, cls="app-header-logo"),
        ),
        Div(cls="app-header-actions")(
            Button(_icon_sun(), _icon_moon(), cls="icon-btn theme-toggle", onclick="toggleTheme()"),
        ),
    )


def _bottom_nav() -> FT:
    return Nav(cls="bottom-nav")(
        A(cls="nav-item active", href="/dashboard")(_icon_home_nav(), Span("Home")),
        A(cls="nav-item nav-cta", href="/transactions/new")(_icon_plus_nav(), Span("New")),
        A(cls="nav-item", href="/profile")(_icon_user_nav(), Span("Profile")),
    )


# ─── Icons ────────────────────────────────────────────────────────────────

def _icon_home() -> FT:
    return Svg(NotStr('<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>'), xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round")
def _icon_plus() -> FT:
    return Svg(NotStr('<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>'), xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2.5", stroke_linecap="round")
def _icon_user() -> FT:
    return Svg(NotStr('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'), xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round")
def _icon_logout() -> FT:
    return Svg(NotStr('<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>'), xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round")
def _icon_sun() -> FT:
    return Svg(NotStr('<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>'), xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round", cls="icon-sun")
def _icon_moon() -> FT:
    return Svg(NotStr('<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>'), xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round", cls="icon-moon")
def _icon_home_nav() -> FT:
    return Svg(NotStr('<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>'), xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round")
def _icon_plus_nav() -> FT:
    return Svg(NotStr('<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>'), xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2.5", stroke_linecap="round")
def _icon_user_nav() -> FT:
    return Svg(NotStr('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'), xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round")


# ─── Head / scripts ───────────────────────────────────────────────────────

def _head(title: str) -> FT:
    short = (title[:24] + "…") if len(title) > 24 else title
    return Head(
        Meta(charset="UTF-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Meta(name="theme-color", content="#0D9488"),
        Title(f"{short} — Teluka"),
        Link(rel="manifest", href="/static/manifest.json"),
        Link(rel="preconnect", href="https://fonts.googleapis.com"),
        Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        Link(href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap", rel="stylesheet"),
        Link(rel="stylesheet", href="/static/css/app.css"),
        Link(rel="stylesheet", href="/static/css/dashboard.css"),
        Link(rel="stylesheet", href="/static/css/deal.css"),
        Script(src="https://unpkg.com/htmx.org@1.9.12"),
        Script(src="/static/js/app.js"),
        Script("(function(){var t=localStorage.getItem('teluka-theme')||(window.matchMedia('(prefers-color-scheme:light)').matches?'light':'dark');document.documentElement.setAttribute('data-theme',t);})();"),
    )


def _scripts() -> FT:
    return Script("""
function toggleTheme() {
  var h = document.documentElement;
  var n = h.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  h.setAttribute('data-theme', n); localStorage.setItem('teluka-theme', n);
}

/* ── Copy deal ID ── */
function copyDealId(fullId) {
  var btn   = document.getElementById('copy-btn');
  var label = document.getElementById('copy-label');
  navigator.clipboard.writeText(fullId).then(function() {
    btn.classList.add('copied');
    label.textContent = 'Copied!';
    setTimeout(function() {
      btn.classList.remove('copied');
      label.textContent = 'Copy';
    }, 2000);
  }).catch(function() {
    label.textContent = 'Failed';
    setTimeout(function() { label.textContent = 'Copy'; }, 1500);
  });
}

/* ── File preview list ── */
function showFilePreviews(input, listId, emoji) {
  var list = document.getElementById(listId);
  if (!list) return;
  list.innerHTML = '';
  var files = Array.from(input.files);
  files.forEach(function(f) {
    var kb = f.size / 1024;
    var sizeStr = kb > 1024 ? (kb/1024).toFixed(1)+' MB' : Math.round(kb)+' KB';
    var item = document.createElement('div');
    item.className = 'file-preview-item';
    item.innerHTML = '<span class="file-preview-icon">'+emoji+'</span>'
      + '<span class="file-preview-name">'+f.name+'</span>'
      + '<span class="file-preview-size">'+sizeStr+'</span>';
    list.appendChild(item);
  });
}

/* ── Drag-and-drop on file zones ── */
document.querySelectorAll('.file-drop-zone').forEach(function(zone) {
  zone.addEventListener('dragover', function(e) {
    e.preventDefault(); zone.classList.add('drag-over');
  });
  zone.addEventListener('dragleave', function() { zone.classList.remove('drag-over'); });
  zone.addEventListener('drop', function(e) {
    e.preventDefault(); zone.classList.remove('drag-over');
    var inp = zone.querySelector('input[type="file"]');
    if (!inp) return;
    var dt = new DataTransfer();
    Array.from(e.dataTransfer.files).forEach(function(f) { dt.items.add(f); });
    inp.files = dt.files;
    inp.dispatchEvent(new Event('change'));
  });
});

/* ── Scroll-hide header/nav ── */
(function () {
  var header = document.querySelector('.app-header');
  var bottomNav = document.querySelector('.bottom-nav');
  var mainEl = document.querySelector('.app-main');
  var lastY = 0, ticking = false, THRESHOLD = 8;
  function update(y) {
    var delta = y - lastY;
    if (Math.abs(delta) >= THRESHOLD) {
      var hiding = delta > 0 && y > 60;
      if (header) header.classList.toggle('header-hidden', hiding);
      if (bottomNav) bottomNav.classList.toggle('nav-hidden', hiding);
      lastY = y;
    }
    ticking = false;
  }
  if (mainEl) mainEl.addEventListener('scroll', function(){ if(!ticking){requestAnimationFrame(function(){update(mainEl.scrollTop);});ticking=true;}}, {passive:true});
  window.addEventListener('scroll', function(){ if(!ticking){requestAnimationFrame(function(){update(window.scrollY||document.documentElement.scrollTop);});ticking=true;}}, {passive:true});
})();
""")

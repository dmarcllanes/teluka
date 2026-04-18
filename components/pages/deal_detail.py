from fasthtml.common import *

from schemas.transaction import Transaction, TransactionStatus
from schemas.user import UserProfile


# Ordered steps for the progress stepper
_STEPS = [
    (TransactionStatus.PENDING,            "Pending",   "Payment awaited"),
    (TransactionStatus.ESCROWED,           "Escrowed",  "Funds held safely"),
    (TransactionStatus.EVIDENCE_SUBMITTED, "Evidence",  "Photos verified"),
    (TransactionStatus.IN_TRANSIT,         "Shipping",  "On the way"),
    (TransactionStatus.DELIVERED,          "Delivered", "Item arrived"),
    (TransactionStatus.COMPLETED,          "Released",  "Funds released"),
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
    return (
        _status_stepper(tx),
        _deal_info_card(tx, buyer, seller),
        _action_area(tx, is_buyer, is_seller),
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
) -> FT:
    amount = f"₱{tx.amount_centavos / 100:,.2f}"
    date   = tx.created_at.strftime("%-d %b %Y · %-I:%M %p") if tx.created_at else ""

    def _party(label: str, user: UserProfile | None) -> FT:
        if not user:
            return Div(cls="deal-party")(
                Div(cls="deal-party-label")(label),
                Div("—", cls="deal-party-phone"),
            )
        phone   = user.phone
        masked  = phone[:3] + "•" * (len(phone) - 7) + phone[-4:] if len(phone) > 7 else phone
        initial = phone[-4:]
        return Div(cls="deal-party")(
            Div(cls="deal-party-label")(label),
            Div(cls="deal-party-row")(
                Div(initial, cls="deal-mini-avatar"),
                Div(masked, cls="deal-party-phone"),
            ),
        )

    return Div(cls="deal-info-card")(
        Div(cls="deal-info-header")(
            Div(cls="deal-item-icon")(_STATUS_ICON.get(tx.status, "📋")),
            Div(
                Div(tx.item_description, cls="deal-item-name"),
                Div(date, style="font-size:0.75rem;color:var(--muted)"),
            ),
        ),
        Div(cls="deal-amount")(amount),
        Div(cls="deal-parties")(
            _party("Buyer",  buyer),
            Div(cls="deal-parties-arrow")("→"),
            _party("Seller", seller),
        ),
        Div(cls="deal-id")(f"Deal ID: {tx.id[:8]}…"),
    )


# ─── Action area ──────────────────────────────────────────────────────────

def _action_area(tx: Transaction, is_buyer: bool, is_seller: bool) -> FT:
    actions = []

    # ── Buyer: pay ────────────────────────────────────────────────────────
    if is_buyer and tx.status == TransactionStatus.PENDING:
        actions.append(
            Div(cls="action-card")(
                Div(cls="action-card-title")("💳 Your turn to pay"),
                P("Funds will be held securely by Teluka until you confirm delivery.",
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
        actions.append(
            Div(cls="action-card")(
                Div(cls="action-card-title")("📸 Upload item photos"),
                P("Take live photos of the item right now. EXIF metadata will be verified — "
                  "screenshots or downloaded images will be rejected.",
                  cls="action-card-desc"),
                Form(
                    Input(type="hidden", name="tx_id", value=tx.id),
                    Div(cls="form-group")(
                        Label("Photos (min 3, max 10 MB each)", cls="form-label"),
                        Input(
                            name="photos", type="file",
                            accept="image/jpeg,image/png,image/webp",
                            multiple=True, required=True,
                            cls="form-input",
                            style="padding:8px;",
                        ),
                        P("JPEG / PNG / WebP only. Must be taken within 24 h of this deal.", cls="form-hint"),
                    ),
                    Button(
                        Span("Submit Evidence"),
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
                Div(cls="action-card-title")("🚚 Add tracking number"),
                P("Ship the item and enter the tracking ID from Lalamove, J&T, or any courier.",
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
                Div(cls="action-card-title")("🎥 Upload unboxing video"),
                P("Record yourself opening the package on camera. This protects you if "
                  "the item does not match the listing.",
                  cls="action-card-desc"),
                Form(
                    Input(type="hidden", name="tx_id", value=tx.id),
                    Div(cls="form-group")(
                        Label("Unboxing video (MP4 / MOV, max 100 MB)", cls="form-label"),
                        Input(
                            name="video", type="file",
                            accept="video/mp4,video/quicktime,video/webm",
                            required=True,
                            cls="form-input",
                            style="padding:8px;",
                        ),
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
                Div(cls="action-card-title")("📦 Confirm & release"),
                P("Item received and matches the description? Release funds to the seller.",
                  cls="action-card-desc"),
                Form(
                    Input(type="hidden", name="tx_id", value=tx.id),
                    Button(
                        Span("Confirm & Release Payment"),
                        Span(cls="htmx-indicator"),
                        type="submit", cls="btn btn-primary btn-block",
                    ),
                    hx_post="/transactions/release",
                    hx_target="#flash",
                    hx_swap="innerHTML",
                    hx_indicator="find .htmx-indicator",
                ),
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

    # ── Cancel (buyer only, pending) ───────────────────────────────────────
    if is_buyer and tx.status == TransactionStatus.PENDING:
        actions.append(
            Form(
                Input(type="hidden", name="tx_id", value=tx.id),
                Button(
                    "Cancel Deal",
                    type="submit",
                    cls="btn btn-ghost btn-block",
                    style="margin-top:8px;color:var(--muted);",
                ),
                hx_post="/transactions/cancel",
                hx_target="#flash",
                hx_swap="innerHTML",
            )
        )

    if not actions:
        return Div()

    return Div(cls="action-area")(*actions)


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
        Script("(function(){var t=localStorage.getItem('teluka-theme')||(window.matchMedia('(prefers-color-scheme:light)').matches?'light':'dark');document.documentElement.setAttribute('data-theme',t);})();"),
    )


def _scripts() -> FT:
    return Script("""
function toggleTheme() {
  var h = document.documentElement;
  var n = h.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  h.setAttribute('data-theme', n); localStorage.setItem('teluka-theme', n);
}
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

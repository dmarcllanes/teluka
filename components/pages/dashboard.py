from fasthtml.common import *

from schemas.transaction import Transaction, TransactionStatus
from schemas.user import UserProfile


# ─── Status config ────────────────────────────────────────────────────────────

_BADGE_CLS = {
    TransactionStatus.PENDING:            "badge-pending",
    TransactionStatus.ESCROWED:           "badge-escrowed",
    TransactionStatus.EVIDENCE_SUBMITTED: "badge-escrowed",
    TransactionStatus.IN_TRANSIT:         "badge-escrowed",
    TransactionStatus.DELIVERED:          "badge-escrowed",
    TransactionStatus.UNBOXING_UPLOADED:  "badge-escrowed",
    TransactionStatus.COMPLETED:          "badge-completed",
    TransactionStatus.DISPUTED:           "badge-disputed",
    TransactionStatus.CANCELLED:          "badge-default",
    TransactionStatus.REFUNDED:           "badge-default",
}

# Human-readable status labels (no underscores, no jargon)
_STATUS_LABEL = {
    TransactionStatus.PENDING:            "Waiting for Payment",
    TransactionStatus.ESCROWED:           "Money Held Safely",
    TransactionStatus.EVIDENCE_SUBMITTED: "Photos Submitted",
    TransactionStatus.IN_TRANSIT:         "On the Way",
    TransactionStatus.DELIVERED:          "Delivered",
    TransactionStatus.UNBOXING_UPLOADED:  "Video Uploaded",
    TransactionStatus.COMPLETED:          "Deal Complete ✓",
    TransactionStatus.DISPUTED:           "Under Review",
    TransactionStatus.CANCELLED:          "Cancelled",
    TransactionStatus.REFUNDED:           "Refunded",
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

# 5-step progress: which step index (0–4) each status maps to
_STATUS_STEP = {
    TransactionStatus.PENDING:            0,
    TransactionStatus.ESCROWED:           1,
    TransactionStatus.EVIDENCE_SUBMITTED: 2,
    TransactionStatus.UNBOXING_UPLOADED:  3,
    TransactionStatus.IN_TRANSIT:         3,
    TransactionStatus.DELIVERED:          3,
    TransactionStatus.COMPLETED:          4,
    TransactionStatus.DISPUTED:           2,
    TransactionStatus.CANCELLED:          0,
    TransactionStatus.REFUNDED:           0,
}

# What the user should do next, keyed by (status, role)
_NEXT_ACTION: dict[tuple, str] = {
    (TransactionStatus.PENDING,            "buyer"):  "Pay to hold your money safely →",
    (TransactionStatus.PENDING,            "seller"): "Waiting for buyer to pay",
    (TransactionStatus.ESCROWED,           "seller"): "Upload real photos of the item →",
    (TransactionStatus.ESCROWED,           "buyer"):  "Waiting for seller to send photos",
    (TransactionStatus.EVIDENCE_SUBMITTED, "buyer"):  "Review photos — confirm or dispute →",
    (TransactionStatus.EVIDENCE_SUBMITTED, "seller"): "Waiting for buyer to review",
    (TransactionStatus.UNBOXING_UPLOADED,  "buyer"):  "Release payment to seller →",
    (TransactionStatus.UNBOXING_UPLOADED,  "seller"): "Waiting for buyer to release payment",
    (TransactionStatus.DISPUTED,           "buyer"):  "Dispute under review — we'll contact you",
    (TransactionStatus.DISPUTED,           "seller"): "Dispute under review — we'll contact you",
}

_ACTIVE_STATUSES = {
    TransactionStatus.PENDING,
    TransactionStatus.ESCROWED,
    TransactionStatus.EVIDENCE_SUBMITTED,
    TransactionStatus.IN_TRANSIT,
    TransactionStatus.DELIVERED,
    TransactionStatus.UNBOXING_UPLOADED,
}
_DONE_STATUSES = {
    TransactionStatus.COMPLETED,
    TransactionStatus.CANCELLED,
    TransactionStatus.REFUNDED,
}


# ─── Page shell ───────────────────────────────────────────────────────────────

def dashboard_page(user: UserProfile, transactions: list[Transaction]) -> FT:
    return Html(
        _head(),
        Body(
            Div(cls="app-layout")(
                _sidebar(active="home"),
                Div(cls="dash-body")(
                    _app_header(),
                    Main(cls="app-main")(
                        Div(cls="app-content")(
                            _dash_content(user, transactions),
                        ),
                    ),
                    _bottom_nav(active="home"),
                ),
            ),
            Div(id="flash"),
            _scripts(),
        ),
    )


# ─── Sidebar (desktop) ────────────────────────────────────────────────────────

def _sidebar(active: str = "home") -> FT:
    def si(page, href, icon, label):
        cls = "sidebar-item active" if active == page else "sidebar-item"
        return A(cls=cls, href=href)(icon, label)

    return Aside(cls="dash-sidebar")(
        Div("Teluka", cls="sidebar-logo"),
        Nav(cls="sidebar-nav")(
            si("home",    "/dashboard",        _icon_home(),  "Home"),
            A(cls="sidebar-item sidebar-cta", href="/transactions/new")(
                _icon_plus(), "Start a Safe Deal"
            ),
            si("profile", "/profile",          _icon_user(),  "My Profile"),
        ),
        Div(cls="sidebar-footer")(
            Button(
                _icon_sun(), _icon_moon(), "Appearance",
                cls="sidebar-item theme-toggle",
                onclick="toggleTheme()",
                style="width:100%;background:none;border:none;cursor:pointer;text-align:left;",
            ),
            Form(action="/logout", method="post")(
                Button(
                    _icon_logout(), "Sign out",
                    cls="sidebar-item",
                    style="width:100%;background:none;border:none;cursor:pointer;text-align:left;",
                ),
            ),
        ),
    )


# ─── Top app bar ──────────────────────────────────────────────────────────────

def _app_header() -> FT:
    return Header(cls="app-header")(
        Div("Teluka", cls="app-header-logo"),
        Div(cls="app-header-actions")(
            Button(
                _icon_sun(), _icon_moon(),
                cls="icon-btn theme-toggle",
                id="theme-toggle",
                title="Toggle theme",
                onclick="toggleTheme()",
            ),
            Form(
                Button(_icon_logout(), cls="icon-btn", title="Sign out"),
                action="/logout", method="post",
            ),
        ),
    )


# ─── Main content ─────────────────────────────────────────────────────────────

def _dash_content(user: UserProfile, transactions: list[Transaction]) -> FT:
    active    = [t for t in transactions if t.status in _ACTIVE_STATUSES]
    completed = [t for t in transactions if t.status == TransactionStatus.COMPLETED]
    disputed  = [t for t in transactions if t.status == TransactionStatus.DISPUTED]

    # Amount protected: sum of all non-cancelled transactions
    protected = sum(
        t.amount_centavos for t in transactions
        if t.status not in (TransactionStatus.CANCELLED,)
    ) / 100

    return (
        _greeting_row(user),
        _trust_card(user),
        _stats_row(len(active), len(completed), protected),
        _alert_banner(active, user),
        _new_deal_btn(),
        _transactions_section(transactions, user),
    )


# ─── Greeting ─────────────────────────────────────────────────────────────────

def _greeting_row(user: UserProfile) -> FT:
    phone = user.phone or ""
    display = phone[-4:] if len(phone) >= 4 else phone
    return Div(cls="dash-greeting")(
        Div(cls="dash-greeting-text")(
            Div(id="greeting-msg", cls="dash-greeting-hi")("Welcome back 👋"),
            Div(f"···{display}", cls="dash-greeting-name"),
        ),
        A(cls="dash-new-pill", href="/transactions/new")(
            _icon_plus_sm(), "New Deal",
        ),
    )


# ─── Trust card with animated ring ────────────────────────────────────────────

def _trust_card(user: UserProfile) -> FT:
    score     = int(user.trust_score)
    level     = user.trust_level.value.title()
    kyc       = "GCash" if user.gcash_verified else ("Maya" if user.maya_verified else None)

    # SVG ring: circumference = 2π × 36 ≈ 226
    circ      = 226
    offset    = circ - int(circ * score / 100)
    ring_cls  = "trust-ring-high" if score >= 70 else ("trust-ring-mid" if score >= 40 else "trust-ring-low")

    level_msgs = {
        "excellent": "People trust you a lot! Keep it up.",
        "good":      "You're building a solid reputation.",
        "fair":      "Complete more deals to grow your trust.",
        "low":       "New here — your trust grows with every deal.",
    }
    msg = level_msgs.get(level.lower(), "Complete deals to grow your trust.")

    return Div(cls="trust-card")(
        Div(cls="trust-card-inner")(
            # Animated ring
            Div(cls="trust-ring-wrap")(
                NotStr(f"""
                <svg width="96" height="96" viewBox="0 0 96 96" class="trust-svg">
                  <circle cx="48" cy="48" r="36"
                    fill="none" stroke="rgba(255,255,255,0.06)"
                    stroke-width="8"/>
                  <circle cx="48" cy="48" r="36"
                    fill="none" stroke-width="8"
                    stroke-linecap="round"
                    class="trust-ring-arc {ring_cls}"
                    stroke-dasharray="{circ}"
                    stroke-dashoffset="{circ}"
                    data-offset="{offset}"
                    transform="rotate(-90 48 48)"/>
                </svg>
                """),
                Div(cls="trust-ring-score")(
                    Span(str(score), cls="trust-score-num"),
                    Span("/100", cls="trust-score-denom"),
                ),
            ),
            # Info
            Div(cls="trust-card-info")(
                Div(cls="trust-level-row")(
                    Div(f"⭐ {level}", cls="trust-level-badge"),
                    Div(kyc, cls="trust-kyc-chip") if kyc else None,
                ),
                P(msg, cls="trust-msg"),
                Div(cls="trust-bar-wrap")(
                    Div(cls="trust-bar-track")(
                        Div(cls=f"trust-bar-fill {ring_cls}", style=f"width:{score}%",
                            id="trust-bar-fill"),
                    ),
                    Span(f"{score}%", cls="trust-bar-pct"),
                ),
            ),
        ),
    )


# ─── Stats row ────────────────────────────────────────────────────────────────

def _stats_row(active: int, completed: int, protected_php: float) -> FT:
    protected_str = (
        f"₱{protected_php/1000:.1f}k" if protected_php >= 1000
        else f"₱{protected_php:,.0f}"
    )
    return Div(cls="dash-stats")(
        _stat_card("🔄", str(active),       "Active Deals",      "stat-active"),
        _stat_card("✅", str(completed),    "Completed",         "stat-done"),
        _stat_card("🛡️", protected_str,     "Kept Safe",         "stat-safe"),
    )


def _stat_card(icon: str, val: str, lbl: str, cls_mod: str) -> FT:
    return Div(cls=f"dash-stat-card {cls_mod}")(
        Div(icon, cls="dash-stat-icon"),
        Div(cls="dash-stat-body")(
            Div(val, cls="dash-stat-val"),
            Div(lbl, cls="dash-stat-lbl"),
        ),
    )


# ─── Alert banner — next action needed ────────────────────────────────────────

def _alert_banner(active: list[Transaction], user: UserProfile) -> FT | None:
    """Show the most urgent deal that needs the user's action."""
    needs_action = []
    for tx in active:
        role = "buyer" if tx.buyer_id == user.id else "seller"
        action = _NEXT_ACTION.get((tx.status, role))
        if action and not action.startswith("Waiting"):
            needs_action.append((tx, action))

    if not needs_action:
        return None

    tx, action = needs_action[0]
    amount = f"₱{tx.amount_centavos / 100:,.0f}"
    return A(cls="alert-banner", href=f"/transactions/{tx.id}")(
        Div(cls="alert-banner-left")(
            Div("⚡ Action needed", cls="alert-banner-eye"),
            Div(tx.item_description, cls="alert-banner-title"),
            Div(amount, cls="alert-banner-amount"),
        ),
        Div(cls="alert-banner-right")(
            Div(action, cls="alert-banner-action"),
            NotStr('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>'),
        ),
    )


# ─── New deal button ──────────────────────────────────────────────────────────

def _new_deal_btn() -> FT:
    return A(
        _icon_plus(),
        "Start a Protected Deal",
        href="/transactions/new",
        cls="btn-new-deal",
    )


# ─── Transactions section ─────────────────────────────────────────────────────

def _transactions_section(transactions: list[Transaction], user: UserProfile) -> FT:
    active   = [t for t in transactions if t.status in _ACTIVE_STATUSES]
    done     = [t for t in transactions if t.status in _DONE_STATUSES]
    disputed = [t for t in transactions if t.status == TransactionStatus.DISPUTED]

    counts = {
        "all":      len(transactions),
        "active":   len(active),
        "done":     len(done),
        "disputed": len(disputed),
    }

    return Div(id="deals-section")(
        Div("My Deals", cls="section-heading"),
        Div(cls="deals-tabs")(
            _tab("all",      f"All ({counts['all']})",              active_tab="all"),
            _tab("active",   f"In Progress ({counts['active']})",   active_tab="all"),
            _tab("done",     f"Done ({counts['done']})",            active_tab="all"),
            _tab("disputed", f"⚠ Issues ({counts['disputed']})",    active_tab="all"),
        ),
        _tx_panel("all",      transactions, user),
        _tx_panel("active",   active,       user),
        _tx_panel("done",     done,         user),
        _tx_panel("disputed", disputed,     user),
    )


def _tab(key: str, label: str, active_tab: str) -> FT:
    cls = "deals-tab active" if key == active_tab else "deals-tab"
    return Button(label, cls=cls, data_tab=key, onclick="switchTab(this)")


def _tx_panel(key: str, transactions: list[Transaction], user: UserProfile) -> FT:
    hidden = "" if key == "all" else "none"
    return Div(id=f"panel-{key}", style=f"display:{hidden}")(
        Div(cls="tx-list")(
            *[_tx_card(t, user) for t in transactions]
        ) if transactions else _empty_state(),
    )


def _tx_card(tx: Transaction, user: UserProfile) -> FT:
    icon      = _STATUS_ICON.get(tx.status, "📋")
    badge_cls = _BADGE_CLS.get(tx.status, "badge-default")
    label     = _STATUS_LABEL.get(tx.status, tx.status.value.replace("_", " ").title())
    amount    = f"₱{tx.amount_centavos / 100:,.0f}"
    date_str  = tx.created_at.strftime("%-d %b") if tx.created_at else ""
    role      = "Buyer" if tx.buyer_id == user.id else "Seller"
    role_cls  = "role-buyer" if role == "Buyer" else "role-seller"
    step      = _STATUS_STEP.get(tx.status, 0)
    next_act  = _NEXT_ACTION.get((tx.status, role.lower()))
    show_act  = next_act and not next_act.startswith("Waiting")

    return A(cls="tx-card", href=f"/transactions/{tx.id}")(
        Div(cls="tx-card-top")(
            Div(icon, cls="tx-icon"),
            Div(cls="tx-info")(
                Div(cls="tx-name-row")(
                    Div(tx.item_description, cls="tx-name"),
                    Span(role, cls=f"tx-role-chip {role_cls}"),
                ),
                Div(cls="tx-meta-row")(
                    Span(date_str, cls="tx-date"),
                    Span("·", cls="tx-dot"),
                    Span(label, cls=f"tx-badge {badge_cls}"),
                ),
            ),
            Div(amount, cls="tx-amount"),
        ),
        # 5-step progress dots
        Div(cls="tx-progress")(
            *[
                Div(cls=f"tx-step {'tx-step-done' if i <= step and tx.status not in (TransactionStatus.CANCELLED, TransactionStatus.REFUNDED) else 'tx-step-todo'}")
                for i in range(5)
            ],
            Div(cls="tx-progress-bar")(
                Div(
                    cls="tx-progress-fill",
                    style=f"width:{min(step * 25, 100) if tx.status not in (TransactionStatus.CANCELLED, TransactionStatus.REFUNDED) else 0}%",
                ),
            ),
        ) if tx.status not in (TransactionStatus.COMPLETED, TransactionStatus.CANCELLED, TransactionStatus.REFUNDED) else None,
        # Next action prompt
        Div(cls="tx-next-action")(
            NotStr('<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>'),
            Span(next_act),
        ) if show_act else None,
    )


def _empty_state() -> FT:
    return Div(cls="empty-state")(
        Div(cls="empty-state-visual")(
            Div("🛡️", cls="empty-state-icon"),
            Div(cls="empty-state-ring"),
        ),
        Div("No deals here yet", cls="empty-state-title"),
        Div(
            "When you buy or sell something, it shows up here. "
            "Your money is always protected until you're happy.",
            cls="empty-state-desc",
        ),
        A("Start my first safe deal →", href="/transactions/new", cls="empty-state-cta"),
    )


# ─── Bottom nav (mobile) ──────────────────────────────────────────────────────

def _bottom_nav(active: str = "home") -> FT:
    def ni(page, href, icon, label):
        cls = "nav-item active" if active == page else "nav-item"
        return A(cls=cls, href=href)(icon, Span(label))

    return Nav(cls="bottom-nav")(
        ni("home",    "/dashboard",        _icon_home_nav(), "Home"),
        A(cls="nav-item nav-cta", href="/transactions/new")(
            _icon_plus_nav(), Span("New"),
        ),
        ni("profile", "/profile",          _icon_user_nav(), "Profile"),
    )


# ─── SVG icons ────────────────────────────────────────────────────────────────

def _icon_home() -> FT:
    return Svg(NotStr('<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>'), xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round")

def _icon_plus() -> FT:
    return Svg(NotStr('<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>'), xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2.5", stroke_linecap="round")

def _icon_plus_sm() -> FT:
    return Svg(NotStr('<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>'), xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2.5", stroke_linecap="round", width="14", height="14")

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


# ─── Head ─────────────────────────────────────────────────────────────────────

def _head() -> FT:
    return Head(
        Meta(charset="UTF-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Meta(name="theme-color", content="#0D9488"),
        Meta(name="apple-mobile-web-app-capable", content="yes"),
        Meta(name="apple-mobile-web-app-status-bar-style", content="black-translucent"),
        Title("My Deals — Teluka"),
        Link(rel="manifest", href="/static/manifest.json"),
        Link(rel="apple-touch-icon", href="/static/icons/icon-192.png"),
        Link(rel="preconnect", href="https://fonts.googleapis.com"),
        Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        Link(href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap", rel="stylesheet"),
        Link(rel="stylesheet", href="/static/css/app.css"),
        Link(rel="stylesheet", href="/static/css/dashboard.css"),
        Script(src="https://unpkg.com/htmx.org@1.9.12"),
        Script("(function(){var t=localStorage.getItem('teluka-theme')||(window.matchMedia('(prefers-color-scheme:light)').matches?'light':'dark');document.documentElement.setAttribute('data-theme',t);})();"),
    )


# ─── Scripts ──────────────────────────────────────────────────────────────────

def _scripts() -> FT:
    return Script("""
/* ── Time-based greeting ── */
(function() {
  var h = new Date().getHours();
  var greet = h < 12 ? 'Good morning 👋' : h < 18 ? 'Good afternoon 👋' : 'Good evening 👋';
  var el = document.getElementById('greeting-msg');
  if (el) el.textContent = greet;
})();

/* ── Animate trust ring ── */
(function() {
  var arc = document.querySelector('.trust-ring-arc');
  var bar = document.getElementById('trust-bar-fill');
  if (arc) {
    var target = parseInt(arc.getAttribute('data-offset') || '226');
    setTimeout(function() {
      arc.style.transition = 'stroke-dashoffset 1.2s cubic-bezier(0.16,1,0.3,1)';
      arc.style.strokeDashoffset = target;
    }, 300);
  }
})();

/* ── Theme toggle ── */
function toggleTheme() {
  var html = document.documentElement;
  var next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  localStorage.setItem('teluka-theme', next);
}

/* ── Deal filter tabs ── */
function switchTab(btn) {
  var key = btn.getAttribute('data-tab');
  document.querySelectorAll('.deals-tab').forEach(function(t) {
    t.classList.toggle('active', t === btn);
  });
  ['all','active','done','disputed'].forEach(function(k) {
    var panel = document.getElementById('panel-' + k);
    if (panel) panel.style.display = k === key ? '' : 'none';
  });
}

/* ── Scroll-hide header/bottom-nav ── */
(function() {
  var header = document.querySelector('.app-header');
  var nav    = document.querySelector('.bottom-nav');
  var main   = document.querySelector('.app-main');
  var lastY  = 0, ticking = false;

  function update(y) {
    var hiding = y - lastY > 8 && y > 60;
    var showing = lastY - y > 8;
    if (hiding)  { if (header) header.classList.add('header-hidden');    if (nav) nav.classList.add('nav-hidden'); }
    if (showing) { if (header) header.classList.remove('header-hidden'); if (nav) nav.classList.remove('nav-hidden'); }
    if (Math.abs(y - lastY) > 8) lastY = y;
    ticking = false;
  }
  function onScroll(y) { if (!ticking) { requestAnimationFrame(function(){ update(y); }); ticking = true; } }

  if (main) main.addEventListener('scroll', function(){ onScroll(main.scrollTop); }, { passive: true });
  window.addEventListener('scroll', function(){ onScroll(window.scrollY); }, { passive: true });
})();

/* ── PWA service worker ── */
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() { navigator.serviceWorker.register('/static/sw.js'); });
}
""")

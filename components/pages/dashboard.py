from fasthtml.common import *

from schemas.transaction import Transaction, TransactionStatus
from schemas.user import UserProfile


# ─── Status badge mapping ─────────────────────────────────────────────────
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


# ─── Sidebar (desktop) ───────────────────────────────────────────────────

def _sidebar(active: str = "home") -> FT:
    def si(page, href, icon, label):
        cls = "sidebar-item active" if active == page else "sidebar-item"
        return A(cls=cls, href=href)(icon, label)

    return Aside(cls="dash-sidebar")(
        Div("Teluka", cls="sidebar-logo"),
        Nav(cls="sidebar-nav")(
            si("home",    "/dashboard",        _icon_home(),  "Home"),
            A(cls="sidebar-item sidebar-cta", href="/transactions/new")(
                _icon_plus(), "New Protected Deal"
            ),
            si("profile", "/profile",          _icon_user(),  "Profile"),
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


# ─── Top app bar ─────────────────────────────────────────────────────────

def _app_header() -> FT:
    return Header(cls="app-header")(
        Div("Teluka", cls="app-header-logo"),
        Div(cls="app-header-actions")(
            Button(
                _icon_sun(),
                _icon_moon(),
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


# ─── Main content ─────────────────────────────────────────────────────────

def _dash_content(user: UserProfile, transactions: list[Transaction]) -> FT:
    completed = sum(1 for t in transactions if t.status == TransactionStatus.COMPLETED)
    active = sum(1 for t in transactions if t.status not in (
        TransactionStatus.COMPLETED, TransactionStatus.CANCELLED, TransactionStatus.REFUNDED
    ))

    return (
        Div("Dashboard", cls="dash-page-title"),
        _user_card(user),
        _stats_row(len(transactions), active, completed),
        # Mobile/tablet CTA button (hidden on desktop via CSS)
        _new_deal_btn(),
        _transactions_section(transactions),
    )


def _user_card(user: UserProfile) -> FT:
    phone = user.phone
    if len(phone) > 7:
        visible = phone[-4:]
        masked = phone[:3] + "•" * (len(phone) - 7) + phone[-4:] if phone.startswith("+") else "•" * (len(phone) - 4) + visible
    else:
        masked = phone

    trust_pct = int(user.trust_score)
    trust_lbl = user.trust_level.value.title()
    kyc_icon  = "✓ GCash" if user.gcash_verified else ("✓ Maya" if user.maya_verified else "Unverified")

    return Div(cls="user-card")(
        Div(cls="user-card-inner")(
            Div(cls="user-card-left")(
                Div("Welcome back", cls="user-greeting"),
                Div(masked, cls="user-phone"),
                Div(cls="trust-row")(
                    Div(f"Trust · {trust_lbl}", cls="trust-label"),
                    Div(cls="trust-bar")(
                        Div(cls="trust-fill", style=f"width:{trust_pct}%"),
                    ),
                    Div(f"{trust_pct}/100", cls="trust-score"),
                ),
            ),
            Div(kyc_icon, cls="user-kyc-badge"),
        ),
    )


def _stats_row(total: int, active: int, completed: int) -> FT:
    return Div(cls="stats-row")(
        _stat_chip(str(total),     "Total"),
        _stat_chip(str(active),    "Active"),
        _stat_chip(str(completed), "Done"),
    )


def _stat_chip(val: str, lbl: str) -> FT:
    return Div(cls="stat-chip")(
        Div(val, cls="stat-chip-val"),
        Div(lbl, cls="stat-chip-lbl"),
    )


def _new_deal_btn() -> FT:
    return A(
        Svg(
            NotStr('<line x1="12" y1="5" x2="12" y2="19"/>'
                   '<line x1="5" y1="12" x2="19" y2="12"/>'),
            xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24",
            fill="none", stroke="currentColor",
            stroke_width="2.5", stroke_linecap="round",
            width="20", height="20",
        ),
        "Start a Protected Deal",
        href="/transactions/new",
        cls="btn-new-deal",
    )


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


def _transactions_section(transactions: list[Transaction]) -> FT:
    active    = [t for t in transactions if t.status in _ACTIVE_STATUSES]
    done      = [t for t in transactions if t.status in _DONE_STATUSES]
    disputed  = [t for t in transactions if t.status == TransactionStatus.DISPUTED]

    counts = {
        "all":      len(transactions),
        "active":   len(active),
        "done":     len(done),
        "disputed": len(disputed),
    }

    return Div(id="deals-section")(
        Div("My Deals", cls="section-heading"),
        # Tab bar
        Div(cls="deals-tabs")(
            _tab("all",      f"All ({counts['all']})",        active_tab="all"),
            _tab("active",   f"Active ({counts['active']})",  active_tab="all"),
            _tab("done",     f"Done ({counts['done']})",      active_tab="all"),
            _tab("disputed", f"⚠ Disputed ({counts['disputed']})", active_tab="all"),
        ),
        # All panels — JS toggles visibility
        _tx_panel("all",      transactions),
        _tx_panel("active",   active),
        _tx_panel("done",     done),
        _tx_panel("disputed", disputed),
    )


def _tab(key: str, label: str, active_tab: str) -> FT:
    cls = "deals-tab active" if key == active_tab else "deals-tab"
    return Button(label, cls=cls, data_tab=key, onclick="switchTab(this)")


def _tx_panel(key: str, transactions: list[Transaction]) -> FT:
    hidden = "" if key == "all" else "none"
    return Div(
        id=f"panel-{key}",
        style=f"display:{hidden}",
    )(
        Div(cls="tx-list")(
            *[_tx_card(t) for t in transactions]
        ) if transactions else _empty_state(),
    )


def _tx_list(transactions: list[Transaction]) -> FT:
    return Div(cls="tx-list")(
        *[_tx_card(t) for t in transactions]
    )


def _tx_card(tx: Transaction) -> FT:
    icon      = _STATUS_ICON.get(tx.status, "📋")
    badge_cls = _BADGE_CLS.get(tx.status, "badge-default")
    label     = tx.status.value.replace("_", " ").title()
    amount    = f"₱{tx.amount_centavos / 100:,.2f}"
    date_str  = tx.created_at.strftime("%-d %b %Y") if tx.created_at else ""

    return A(cls="tx-card", href=f"/transactions/{tx.id}")(
        Div(icon, cls="tx-icon"),
        Div(cls="tx-info")(
            Div(tx.item_description, cls="tx-name"),
            Div(date_str, cls="tx-meta"),
        ),
        Div(cls="tx-right")(
            Div(amount, cls="tx-amount"),
            Span(label, cls=f"tx-badge {badge_cls}"),
        ),
    )


def _empty_state() -> FT:
    return Div(cls="empty-state")(
        Div("🛡️", cls="empty-state-icon"),
        Div("No deals yet", cls="empty-state-title"),
        Div(
            "Start your first protected transaction to keep your money safe from scams.",
            cls="empty-state-desc",
        ),
    )



# ─── Bottom nav (mobile/tablet) ────────────────────────────────────────────

def _bottom_nav(active: str = "home") -> FT:
    def ni(page, href, icon, label):
        cls = f"nav-item active" if active == page else "nav-item"
        return A(cls=cls, href=href)(icon, Span(label))

    return Nav(cls="bottom-nav")(
        ni("home",    "/dashboard",        _icon_home_nav(), "Home"),
        A(cls="nav-item nav-cta", href="/transactions/new")(
            _icon_plus_nav(), Span("New"),
        ),
        ni("profile", "/profile",          _icon_user_nav(), "Profile"),
    )


# ─── SVG icons ────────────────────────────────────────────────────────────

def _icon_home() -> FT:
    return Svg(
        NotStr('<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
               '<polyline points="9 22 9 12 15 12 15 22"/>'),
        xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24",
        fill="none", stroke="currentColor",
        stroke_width="2", stroke_linecap="round", stroke_linejoin="round",
    )

def _icon_plus() -> FT:
    return Svg(
        NotStr('<line x1="12" y1="5" x2="12" y2="19"/>'
               '<line x1="5" y1="12" x2="19" y2="12"/>'),
        xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24",
        fill="none", stroke="currentColor",
        stroke_width="2.5", stroke_linecap="round",
    )

def _icon_list() -> FT:
    return Svg(
        NotStr('<line x1="8" y1="6" x2="21" y2="6"/>'
               '<line x1="8" y1="12" x2="21" y2="12"/>'
               '<line x1="8" y1="18" x2="21" y2="18"/>'
               '<line x1="3" y1="6" x2="3.01" y2="6"/>'
               '<line x1="3" y1="12" x2="3.01" y2="12"/>'
               '<line x1="3" y1="18" x2="3.01" y2="18"/>'),
        xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24",
        fill="none", stroke="currentColor",
        stroke_width="2", stroke_linecap="round",
    )

def _icon_user() -> FT:
    return Svg(
        NotStr('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>'
               '<circle cx="12" cy="7" r="4"/>'),
        xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24",
        fill="none", stroke="currentColor",
        stroke_width="2", stroke_linecap="round", stroke_linejoin="round",
    )

def _icon_logout() -> FT:
    return Svg(
        NotStr('<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>'
               '<polyline points="16 17 21 12 16 7"/>'
               '<line x1="21" y1="12" x2="9" y2="12"/>'),
        xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24",
        fill="none", stroke="currentColor",
        stroke_width="2", stroke_linecap="round", stroke_linejoin="round",
    )

def _icon_sun() -> FT:
    return Svg(
        NotStr('<circle cx="12" cy="12" r="5"/>'
               '<line x1="12" y1="1" x2="12" y2="3"/>'
               '<line x1="12" y1="21" x2="12" y2="23"/>'
               '<line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>'
               '<line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>'
               '<line x1="1" y1="12" x2="3" y2="12"/>'
               '<line x1="21" y1="12" x2="23" y2="12"/>'
               '<line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>'
               '<line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>'),
        xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24",
        fill="none", stroke="currentColor",
        stroke_width="2", stroke_linecap="round", stroke_linejoin="round",
        cls="icon-sun",
    )

def _icon_moon() -> FT:
    return Svg(
        NotStr('<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>'),
        xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24",
        fill="none", stroke="currentColor",
        stroke_width="2", stroke_linecap="round", stroke_linejoin="round",
        cls="icon-moon",
    )

# Nav bar variants (slightly larger stroke)
def _icon_home_nav() -> FT:
    return Svg(
        NotStr('<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
               '<polyline points="9 22 9 12 15 12 15 22"/>'),
        xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24",
        fill="none", stroke="currentColor",
        stroke_width="2", stroke_linecap="round", stroke_linejoin="round",
    )

def _icon_plus_nav() -> FT:
    return Svg(
        NotStr('<line x1="12" y1="5" x2="12" y2="19"/>'
               '<line x1="5" y1="12" x2="19" y2="12"/>'),
        xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24",
        fill="none", stroke="currentColor",
        stroke_width="2.5", stroke_linecap="round",
    )

def _icon_user_nav() -> FT:
    return Svg(
        NotStr('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>'
               '<circle cx="12" cy="7" r="4"/>'),
        xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24",
        fill="none", stroke="currentColor",
        stroke_width="2", stroke_linecap="round", stroke_linejoin="round",
    )


# ─── Head / scripts ───────────────────────────────────────────────────────

def _head() -> FT:
    return Head(
        Meta(charset="UTF-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Meta(name="theme-color", content="#0D9488"),
        Meta(name="apple-mobile-web-app-capable", content="yes"),
        Meta(name="apple-mobile-web-app-status-bar-style", content="black-translucent"),
        Title("Dashboard — Teluka"),
        Link(rel="manifest", href="/static/manifest.json"),
        Link(rel="apple-touch-icon", href="/static/icons/icon-192.png"),
        Link(rel="preconnect", href="https://fonts.googleapis.com"),
        Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        Link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap",
            rel="stylesheet",
        ),
        Link(rel="stylesheet", href="/static/css/app.css"),
        Link(rel="stylesheet", href="/static/css/dashboard.css"),
        Script(src="https://unpkg.com/htmx.org@1.9.12"),
        # Anti-FOUC theme init
        Script(
            "(function(){"
            "var t=localStorage.getItem('teluka-theme')||"
            "(window.matchMedia('(prefers-color-scheme:light)').matches?'light':'dark');"
            "document.documentElement.setAttribute('data-theme',t);"
            "})();"
        ),
    )


def _scripts() -> FT:
    return Script("""
/* ── Theme toggle ─────────────────────────────────────── */
function toggleTheme() {
  var html = document.documentElement;
  var next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  localStorage.setItem('teluka-theme', next);
}

/* ── Deal filter tabs ─────────────────────────────────── */
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

/* ── Scroll-hide navbar (LinkedIn style) ─────────────── */
(function () {
  var header    = document.querySelector('.app-header');
  var bottomNav = document.querySelector('.bottom-nav');
  var mainEl    = document.querySelector('.app-main');
  var lastY = 0, ticking = false, THRESHOLD = 8;

  function update(y) {
    var delta = y - lastY;
    if (Math.abs(delta) >= THRESHOLD) {
      var hiding = delta > 0 && y > 60;
      if (header)    header.classList.toggle('header-hidden', hiding);
      if (bottomNav) bottomNav.classList.toggle('nav-hidden', hiding);
      lastY = y;
    }
    ticking = false;
  }

  function onMainScroll() {
    if (!ticking) { requestAnimationFrame(function(){ update(mainEl.scrollTop); }); ticking = true; }
  }
  function onWindowScroll() {
    if (!ticking) { requestAnimationFrame(function(){ update(window.scrollY||document.documentElement.scrollTop); }); ticking = true; }
  }

  /* Desktop: .app-main scrolls internally. Mobile: window scrolls. */
  if (mainEl) mainEl.addEventListener('scroll', onMainScroll, { passive: true });
  window.addEventListener('scroll', onWindowScroll, { passive: true });
})();

/* ── PWA service worker ───────────────────────────────── */
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('/static/sw.js');
  });
}
""")

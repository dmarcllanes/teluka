from fasthtml.common import *

from schemas.transaction import Transaction, TransactionStatus
from schemas.user import UserProfile, KYCStatus, TrustLevel


def profile_page(user: UserProfile, transactions: list[Transaction]) -> FT:
    return Html(
        _head(),
        Body(
            Div(cls="app-layout")(
                _sidebar(active="profile"),
                Div(cls="dash-body")(
                    _app_header(),
                    Main(cls="app-main")(
                        Div(cls="app-content")(
                            _profile_content(user, transactions),
                        ),
                    ),
                    _bottom_nav(active="profile"),
                ),
            ),
            Div(id="flash"),
            _scripts(),
        ),
    )


# ─── Content ──────────────────────────────────────────────────────────────

def _profile_content(user: UserProfile, transactions: list[Transaction]) -> FT:
    completed = sum(1 for t in transactions if t.status == TransactionStatus.COMPLETED)
    disputed  = sum(1 for t in transactions if t.status == TransactionStatus.DISPUTED)

    return (
        Div("Profile", cls="dash-page-title"),
        _profile_hero(user),
        _trust_card(user),
        _stats_card(len(transactions), completed, user.scam_reports),
        _verification_card(user),
        _settings_card(),
    )


def _profile_hero(user: UserProfile) -> FT:
    # initials from last 4 digits of phone
    initials = user.phone[-4:] if len(user.phone) >= 4 else "??"

    # Mask phone
    phone = user.phone
    if len(phone) > 7:
        masked = phone[:3] + "•" * (len(phone) - 7) + phone[-4:]
    else:
        masked = phone

    trust_cls = {
        TrustLevel.NEW:         "badge-trust-new",
        TrustLevel.LOW:         "badge-trust-low",
        TrustLevel.MEDIUM:      "badge-trust-medium",
        TrustLevel.HIGH:        "badge-trust-high",
        TrustLevel.BLACKLISTED: "badge-trust-blacklisted",
    }.get(user.trust_level, "badge-trust-new")

    kyc_label = "KYC Verified" if user.kyc_status == KYCStatus.VERIFIED else "Unverified"
    kyc_cls   = "badge-kyc-verified" if user.kyc_status == KYCStatus.VERIFIED else "badge-kyc-unverified"

    return Div(cls="profile-hero")(
        Div(cls="avatar")(
            Span(initials),
            Div(cls="avatar-ring"),
        ),
        Div(masked, cls="profile-name"),
        Div(cls="profile-badges")(
            Span(
                _dot_icon(), user.trust_level.value.title() + " Trust",
                cls=f"profile-badge {trust_cls}",
            ),
            Span(
                ("✓ " if user.kyc_status == KYCStatus.VERIFIED else "○ ") + kyc_label,
                cls=f"profile-badge {kyc_cls}",
            ),
        ),
    )


def _trust_card(user: UserProfile) -> FT:
    pct = int(user.trust_score)
    return Div(cls="profile-card")(
        Div("Trust Score", cls="profile-card-title"),
        Div(cls="profile-trust-row")(
            Div(f"{pct}", cls="profile-trust-val"),
            Div(cls="profile-trust-meta")(
                Div(f"out of 100 · {user.trust_level.value.title()} level", cls="profile-trust-label"),
                Div(cls="profile-trust-bar")(
                    Div(cls="profile-trust-fill", style=f"width:{pct}%"),
                ),
            ),
        ),
        P(
            _trust_hint(pct),
            style="font-size:0.8rem;color:var(--muted);margin-top:10px;line-height:1.5",
        ),
    )


def _trust_hint(pct: int) -> str:
    if pct == 0:
        return "Complete your first deal to start building your trust score."
    elif pct < 30:
        return "Your score grows with every completed deal and verified account."
    elif pct < 60:
        return "Good progress! Verify GCash or Maya to unlock higher trust levels."
    elif pct < 80:
        return "Strong trust score. You're a reliable member of the community."
    else:
        return "Excellent score! You're among Teluka's most trusted sellers."


def _stats_card(total: int, completed: int, scam_reports: int) -> FT:
    return Div(cls="profile-card")(
        Div("Activity", cls="profile-card-title"),
        Div(cls="stats-row")(
            _stat_chip(str(total),        "Deals"),
            _stat_chip(str(completed),    "Completed"),
            _stat_chip(str(scam_reports), "Reports"),
        ),
    )


def _stat_chip(val: str, lbl: str) -> FT:
    return Div(cls="stat-chip")(
        Div(val, cls="stat-chip-val"),
        Div(lbl, cls="stat-chip-lbl"),
    )


def _verification_card(user: UserProfile) -> FT:
    return Div(cls="profile-card")(
        Div("Payment Verification", cls="profile-card-title"),
        Div(cls="verify-grid")(
            _verify_item("GCash",  "💚", user.gcash_verified),
            _verify_item("Maya",   "💜", user.maya_verified),
        ),
    )


def _verify_item(label: str, emoji: str, verified: bool) -> FT:
    return Div(cls="verify-item")(
        Div(emoji, cls=f"verify-icon {'verified' if verified else 'unverified'}"),
        Div(
            Div(label, cls="verify-label"),
            Div(
                "Connected" if verified else "Not connected",
                cls=f"verify-status {'ok' if verified else 'no'}",
            ),
        ),
    )


def _settings_card() -> FT:
    return Div(cls="profile-card")(
        Div("Settings", cls="profile-card-title"),
        Div(cls="settings-list")(
            # Theme toggle
            Button(
                Div("◐", cls="settings-item-icon"),
                Div("Appearance", cls="settings-item-label"),
                Div(id="theme-label", style="font-size:0.78rem;color:var(--muted);margin-right:8px"),
                Span("›", cls="settings-item-arrow"),
                cls="settings-item",
                onclick="toggleTheme(); updateThemeLabel();",
            ),
            # Help
            A(
                Div("?", cls="settings-item-icon"),
                Div("Help & Support", cls="settings-item-label"),
                Span("›", cls="settings-item-arrow"),
                cls="settings-item",
                href="#",
            ),
            # About
            A(
                Div("ℹ", cls="settings-item-icon"),
                Div("About Teluka", cls="settings-item-label"),
                Span("›", cls="settings-item-arrow"),
                cls="settings-item",
                href="#",
            ),
            # Sign out
            Form(action="/logout", method="post", style="display:contents")(
                Button(
                    Div("↩", cls="settings-item-icon"),
                    Div("Sign Out", cls="settings-item-label"),
                    cls="settings-item danger",
                    type="submit",
                ),
            ),
        ),
    )


# ─── Shared shell components ───────────────────────────────────────────────

def _sidebar(active: str = "profile") -> FT:
    def si(page, href, icon, label):
        cls = "sidebar-item active" if active == page else "sidebar-item"
        return A(cls=cls, href=href)(icon, label)

    return Aside(cls="dash-sidebar")(
        Div("Teluka", cls="sidebar-logo"),
        Nav(cls="sidebar-nav")(
            si("home",    "/dashboard",    _icon_home(),  "Home"),
            A(cls="sidebar-item sidebar-cta", href="/transactions/new")(
                _icon_plus(), "New Protected Deal"
            ),
            si("profile", "/profile",      _icon_user(),  "Profile"),
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


def _bottom_nav(active: str = "profile") -> FT:
    def ni(page, href, icon, label):
        cls = "nav-item active" if active == page else "nav-item"
        return A(cls=cls, href=href)(icon, Span(label))

    return Nav(cls="bottom-nav")(
        ni("home",    "/dashboard",  _icon_home_nav(), "Home"),
        A(cls="nav-item nav-cta", href="/transactions/new")(
            _icon_plus_nav(), Span("New"),
        ),
        ni("profile", "/profile",    _icon_user_nav(), "Profile"),
    )


# ─── SVG icons ────────────────────────────────────────────────────────────

def _dot_icon() -> FT:
    return Svg(
        NotStr('<circle cx="12" cy="12" r="4" fill="currentColor"/>'),
        xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24",
        width="8", height="8", style="flex-shrink:0",
    )

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
        Title("Profile — Teluka"),
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
/* ── Theme toggle ─────────────────────────────────── */
function toggleTheme() {
  var html = document.documentElement;
  var next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  localStorage.setItem('teluka-theme', next);
  updateThemeLabel();
}
function updateThemeLabel() {
  var el = document.getElementById('theme-label');
  if (el) el.textContent = document.documentElement.getAttribute('data-theme') === 'dark'
    ? 'Dark' : 'Light';
}
document.addEventListener('DOMContentLoaded', updateThemeLabel);

/* ── Scroll-hide navbar ───────────────────────────── */
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

  if (mainEl) mainEl.addEventListener('scroll', onMainScroll, { passive: true });
  window.addEventListener('scroll', onWindowScroll, { passive: true });
})();

/* ── PWA ──────────────────────────────────────────── */
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('/static/sw.js');
  });
}
""")

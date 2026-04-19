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


# ─── Content ───────────────────────────────────────────────────────────────────

def _profile_content(user: UserProfile, transactions: list[Transaction]) -> FT:
    completed = sum(1 for t in transactions if t.status == TransactionStatus.COMPLETED)

    return (
        Div("Profile", cls="dash-page-title"),
        _profile_hero(user),
        _edit_panel(user),
        _trust_card(user),
        _stats_card(len(transactions), completed, user.scam_reports),
        _verification_card(user),
        _settings_card(),
    )


# ─── Profile hero ───────────────────────────────────────────────────────────────

def _profile_hero(user: UserProfile) -> FT:
    initials = user.phone[-4:] if len(user.phone) >= 4 else "??"
    phone = user.phone
    masked = (phone[:3] + "•" * (len(phone) - 7) + phone[-4:]) if len(phone) > 7 else phone

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
        Div(user.email or "No email set", cls="profile-email"),
        Div(cls="profile-badges")(
            Span(_dot_icon(), user.trust_level.value.title() + " Trust", cls=f"profile-badge {trust_cls}"),
            Span(("✓ " if user.kyc_status == KYCStatus.VERIFIED else "○ ") + kyc_label, cls=f"profile-badge {kyc_cls}"),
        ),
        Button(
            _icon_edit(), "Edit Profile",
            cls="pf-edit-btn",
            onclick="toggleEditPanel()",
        ),
    )


# ─── Edit panel (inline, toggled via JS) ────────────────────────────────────────

def _edit_panel(user: UserProfile) -> FT:
    return Div(cls="pf-edit-panel", id="edit-panel")(
        Div(cls="profile-card")(
            Div("Edit Profile", cls="profile-card-title"),

            # Email field
            Form(
                hx_post="/profile/edit",
                hx_swap="none",
                hx_on__htmx_after_request="onEditSaved(event)",
            )(
                Div(cls="pf-field")(
                    Label("Email address", cls="pf-label", for_="pf-email"),
                    Div(cls="pf-input-wrap")(
                        Span("✉️", cls="pf-input-icon"),
                        Input(
                            id="pf-email",
                            name="email",
                            type="email",
                            value=user.email or "",
                            placeholder="you@example.com",
                            cls="pf-input",
                            autocomplete="email",
                        ),
                    ),
                    P("Used for OTP codes. We never share your email.", cls="pf-hint"),
                ),

                # Phone (read-only)
                Div(cls="pf-field")(
                    Label("Phone number", cls="pf-label"),
                    Div(cls="pf-input-wrap pf-readonly")(
                        Span("📱", cls="pf-input-icon"),
                        Input(
                            value=user.phone,
                            type="tel",
                            cls="pf-input",
                            disabled=True,
                        ),
                    ),
                    P("Your phone is your identity and cannot be changed.", cls="pf-hint"),
                ),

                Div(cls="pf-actions")(
                    Button("Cancel", type="button", cls="pf-cancel-btn", onclick="toggleEditPanel()"),
                    Button("Save Changes", type="submit", cls="pf-save-btn", id="pf-save-btn"),
                ),
            ),

            # Change PIN
            Div(cls="pf-pin-row")(
                Div(cls="pf-pin-info")(
                    Div("Security PIN", cls="pf-pin-title"),
                    Div(
                        "PIN is set ✓" if user.pin_hash else "No PIN set — required to release payments",
                        cls="pf-pin-sub " + ("pf-pin-ok" if user.pin_hash else "pf-pin-warn"),
                    ),
                ),
                A("Change PIN →" if user.pin_hash else "Set PIN →", href="/profile/change-pin", cls="pf-pin-link"),
            ),
        ),
    )


# ─── Trust score ────────────────────────────────────────────────────────────────

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
        P(_trust_hint(pct), style="font-size:0.8rem;color:var(--muted);margin-top:10px;line-height:1.5"),
    )


def _trust_hint(pct: int) -> str:
    if pct == 0:   return "Complete your first deal to start building your trust score."
    if pct < 30:   return "Your score grows with every completed deal and verified wallet."
    if pct < 60:   return "Good progress! Verify GCash or Maya to unlock higher trust."
    if pct < 80:   return "Strong trust score. You're a reliable member of the community."
    return "Excellent score! You're among Teluka's most trusted members."


# ─── Activity stats ─────────────────────────────────────────────────────────────

def _stats_card(total: int, completed: int, scam_reports: int) -> FT:
    return Div(cls="profile-card")(
        Div("Activity", cls="profile-card-title"),
        Div(cls="stats-row")(
            _stat_chip(total,        "Deals"),
            _stat_chip(completed,    "Completed"),
            _stat_chip(scam_reports, "Reports"),
        ),
    )


def _stat_chip(val: int, lbl: str) -> FT:
    return Div(cls="stat-chip")(
        Div(str(val), cls="stat-chip-val", **{"data-count": str(val)}),
        Div(lbl, cls="stat-chip-lbl"),
    )


# ─── Verification card ──────────────────────────────────────────────────────────

def _verification_card(user: UserProfile) -> FT:
    return Div(cls="profile-card")(
        # Header
        Div(cls="vc-header")(
            Div(cls="vc-title-row")(
                Div("🛡️", cls="vc-shield"),
                Div(cls="vc-title-block")(
                    Div("Get Verified", cls="profile-card-title", style="margin:0"),
                    Div(
                        "Verified ✓" if (user.gcash_verified or user.maya_verified)
                        else "Unverified — verify to unlock all features",
                        cls="vc-status " + ("vc-status-ok" if (user.gcash_verified or user.maya_verified) else "vc-status-no"),
                    ),
                ),
            ),
        ),

        # Benefits section
        Div(cls="vc-benefits")(
            Div("Verification unlocks:", cls="vc-benefits-title"),
            Div(cls="vc-benefits-grid")(
                _benefit("⭐", "Verified Badge",    "Buyers & sellers see you're legit on every deal"),
                _benefit("📈", "+20 Trust Points",  "Instant boost to your Trust Score"),
                _benefit("💰", "Higher Deal Limit", "Protect deals up to ₱50,000 vs ₱5,000 unverified"),
                _benefit("⚡", "Priority Support",  "Disputes resolved first — 24h vs 72h"),
            ),
        ),

        # Divider
        Div(cls="vc-divider"),

        # How to verify — steps
        Div(cls="vc-how")(
            Div("How verification works:", cls="vc-benefits-title"),
            Div(cls="vc-steps")(
                _step("1", "Link your GCash or Maya number below"),
                _step("2", "Teluka sends a ₱1 test deposit to confirm ownership"),
                _step("3", "Enter the reference number you receive — done!"),
            ),
        ),

        Div(cls="vc-divider"),

        # Wallet items
        Div(cls="vc-wallets")(
            Div("Your wallets:", cls="vc-benefits-title"),
            Div(cls="verify-grid")(
                _verify_item_new("GCash",  "💚", "#06B", user.gcash_verified, "gcash"),
                _verify_item_new("Maya",   "💜", "#7C3AED", user.maya_verified,  "maya"),
            ),
        ),
    )


def _benefit(icon: str, title: str, desc: str) -> FT:
    return Div(cls="vb-item")(
        Div(icon, cls="vb-icon"),
        Div(cls="vb-text")(
            Div(title, cls="vb-title"),
            Div(desc,  cls="vb-desc"),
        ),
    )


def _step(num: str, text: str) -> FT:
    return Div(cls="vc-step")(
        Div(num, cls="vc-step-num"),
        Div(text, cls="vc-step-text"),
    )


def _verify_item_new(label: str, emoji: str, color: str, verified: bool, key: str) -> FT:
    if verified:
        return Div(cls="verify-item verify-item-done")(
            Div(emoji, cls="verify-icon verified"),
            Div(
                Div(label, cls="verify-label"),
                Div("✓ Verified", cls="verify-status ok"),
            ),
            Div("✓", cls="vi-check"),
        )

    return Div(
        cls="verify-item verify-unverified-pulse",
        id=f"vi-{key}",
    )(
        Div(emoji, cls="verify-icon unverified"),
        Div(
            Div(label, cls="verify-label"),
            Div("Not connected", cls="verify-status no"),
        ),
        Button(
            "Verify →",
            cls="vi-start-btn",
            onclick=f"startVerify('{key}')",
        ),
    )


# ─── Verify modal (inline) ──────────────────────────────────────────────────────

def verify_modal_html(key: str, label: str, emoji: str) -> FT:
    """Returned by HTMX to replace the wallet item with a verification form."""
    return Div(cls="verify-item vi-form-wrap", id=f"vi-{key}")(
        Div(emoji, cls="verify-icon unverified"),
        Div(cls="vi-form")(
            Input(
                name=f"{key}_number",
                id=f"{key}-num",
                type="tel",
                placeholder=f"Your {label} number (09xxxxxxxxx)",
                cls="vi-input",
                inputmode="numeric",
                maxlength="11",
            ),
            Div(cls="vi-form-row")(
                Button("Cancel", type="button", cls="vi-cancel", onclick=f"cancelVerify('{key}')"),
                Button(
                    "Send ₱1 →",
                    cls="vi-submit",
                    hx_post=f"/profile/verify-{key}",
                    hx_target=f"#vi-{key}",
                    hx_swap="outerHTML",
                    hx_include=f"#{key}-num",
                ),
            ),
        ),
    )


def verify_pending_html(key: str, label: str, emoji: str) -> FT:
    """Shown after the ₱1 is sent — user must enter the ref number."""
    return Div(cls="verify-item vi-form-wrap", id=f"vi-{key}")(
        Div(emoji, cls="verify-icon unverified"),
        Div(cls="vi-form")(
            P(f"We sent ₱1 to your {label}. Check for the reference number.", cls="vi-sent-msg"),
            Input(
                name="ref",
                id=f"{key}-ref",
                type="text",
                placeholder="Reference number (e.g. ABC123456789)",
                cls="vi-input",
                autocomplete="off",
            ),
            Div(cls="vi-form-row")(
                Button("Cancel", type="button", cls="vi-cancel", onclick=f"cancelVerify('{key}')"),
                Button(
                    "Confirm →",
                    cls="vi-submit",
                    hx_post=f"/profile/verify-{key}-confirm",
                    hx_target=f"#vi-{key}",
                    hx_swap="outerHTML",
                    hx_include=f"#{key}-ref",
                ),
            ),
        ),
    )


def verify_done_html(label: str, emoji: str) -> FT:
    """Final state after successful verification."""
    return Div(cls="verify-item verify-item-done")(
        Div(emoji, cls="verify-icon verified"),
        Div(
            Div(label, cls="verify-label"),
            Div("✓ Verified", cls="verify-status ok"),
        ),
        Div("✓", cls="vi-check"),
    )


# ─── Settings ───────────────────────────────────────────────────────────────────

def _settings_card() -> FT:
    return Div(cls="profile-card")(
        Div("Settings", cls="profile-card-title"),
        Div(cls="settings-list")(
            Button(
                Div("◐", cls="settings-item-icon"),
                Div("Appearance", cls="settings-item-label"),
                Div(id="theme-label", style="font-size:0.78rem;color:var(--muted);margin-right:8px"),
                Span("›", cls="settings-item-arrow"),
                cls="settings-item",
                onclick="toggleTheme(); updateThemeLabel();",
            ),
            A(
                Div("?", cls="settings-item-icon"),
                Div("Help & Support", cls="settings-item-label"),
                Span("›", cls="settings-item-arrow"),
                cls="settings-item", href="#",
            ),
            A(
                Div("ℹ", cls="settings-item-icon"),
                Div("About Teluka", cls="settings-item-label"),
                Span("›", cls="settings-item-arrow"),
                cls="settings-item", href="#",
            ),
            Form(action="/logout", method="post", style="display:contents")(
                Button(
                    Div("↩", cls="settings-item-icon"),
                    Div("Sign Out", cls="settings-item-label"),
                    cls="settings-item danger", type="submit",
                ),
            ),
        ),
    )


# ─── Shell components ────────────────────────────────────────────────────────────

def _sidebar(active: str = "profile") -> FT:
    def si(page, href, icon, label):
        cls = "sidebar-item active" if active == page else "sidebar-item"
        return A(cls=cls, href=href)(icon, label)

    return Aside(cls="dash-sidebar")(
        Div("Teluka", cls="sidebar-logo"),
        Nav(cls="sidebar-nav")(
            si("home",    "/dashboard",    _icon_home(),  "Home"),
            A(cls="sidebar-item sidebar-cta", href="/transactions/new")(_icon_plus(), "New Protected Deal"),
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
                Button(_icon_logout(), "Sign out", cls="sidebar-item",
                       style="width:100%;background:none;border:none;cursor:pointer;text-align:left;"),
            ),
        ),
    )


def _app_header() -> FT:
    return Header(cls="app-header")(
        Div("Teluka", cls="app-header-logo"),
        Div(cls="app-header-actions")(
            Button(_icon_sun(), _icon_moon(), cls="icon-btn theme-toggle", id="theme-toggle",
                   title="Toggle theme", onclick="toggleTheme()"),
            Form(Button(_icon_logout(), cls="icon-btn", title="Sign out"), action="/logout", method="post"),
        ),
    )


def _bottom_nav(active: str = "profile") -> FT:
    def ni(page, href, icon, label):
        cls = "nav-item active" if active == page else "nav-item"
        return A(cls=cls, href=href)(icon, Span(label))

    return Nav(cls="bottom-nav")(
        ni("home",    "/dashboard",  _icon_home_nav(), "Home"),
        A(cls="nav-item nav-cta", href="/transactions/new")(_icon_plus_nav(), Span("New")),
        ni("profile", "/profile",    _icon_user_nav(), "Profile"),
    )


# ─── SVG icons ──────────────────────────────────────────────────────────────────

def _dot_icon() -> FT:
    return Svg(NotStr('<circle cx="12" cy="12" r="4" fill="currentColor"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", width="8", height="8", style="flex-shrink:0")

def _icon_edit() -> FT:
    return Svg(NotStr('<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>'
                      '<path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24",
               fill="none", stroke="currentColor", stroke_width="2",
               stroke_linecap="round", stroke_linejoin="round", width="14", height="14")

def _icon_home() -> FT:
    return Svg(NotStr('<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round")

def _icon_plus() -> FT:
    return Svg(NotStr('<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2.5", stroke_linecap="round")

def _icon_user() -> FT:
    return Svg(NotStr('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round")

def _icon_logout() -> FT:
    return Svg(NotStr('<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round")

def _icon_sun() -> FT:
    return Svg(NotStr('<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round", cls="icon-sun")

def _icon_moon() -> FT:
    return Svg(NotStr('<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round", cls="icon-moon")

def _icon_home_nav() -> FT:
    return Svg(NotStr('<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round")

def _icon_plus_nav() -> FT:
    return Svg(NotStr('<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2.5", stroke_linecap="round")

def _icon_user_nav() -> FT:
    return Svg(NotStr('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round")


# ─── Head / scripts ─────────────────────────────────────────────────────────────

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
        Link(href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap", rel="stylesheet"),
        Link(rel="stylesheet", href="/static/css/app.css"),
        Link(rel="stylesheet", href="/static/css/dashboard.css"),
        Script(src="https://unpkg.com/htmx.org@1.9.12"),
        Script("(function(){var t=localStorage.getItem('teluka-theme')||(window.matchMedia('(prefers-color-scheme:light)').matches?'light':'dark');document.documentElement.setAttribute('data-theme',t);})();"),
    )


def _scripts() -> FT:
    return Script("""
/* ── Theme ── */
function toggleTheme() {
  var html = document.documentElement;
  var next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  localStorage.setItem('teluka-theme', next);
  updateThemeLabel();
}
function updateThemeLabel() {
  var el = document.getElementById('theme-label');
  if (el) el.textContent = document.documentElement.getAttribute('data-theme') === 'dark' ? 'Dark' : 'Light';
}
document.addEventListener('DOMContentLoaded', updateThemeLabel);

/* ── Edit panel toggle ── */
var _editOpen = false;
function toggleEditPanel() {
  _editOpen = !_editOpen;
  var panel = document.getElementById('edit-panel');
  if (panel) {
    panel.classList.toggle('pf-edit-open', _editOpen);
    if (_editOpen) setTimeout(function(){ panel.querySelector('input:not(:disabled)')?.focus(); }, 280);
  }
}

/* ── Edit saved feedback ── */
function onEditSaved(event) {
  var ok = event.detail.successful;
  _showToast(ok ? '✓ Profile saved' : '✗ Save failed — try again', ok ? 'success' : 'error');
  if (ok) setTimeout(toggleEditPanel, 800);
}

/* ── Verify wallet inline expansion ── */
var _verifyOriginals = {};
function startVerify(key) {
  var wrap = document.getElementById('vi-' + key);
  if (!wrap) return;
  _verifyOriginals[key] = wrap.outerHTML;
  var label = key === 'gcash' ? 'GCash' : 'Maya';
  var emoji = key === 'gcash' ? '💚' : '💜';
  wrap.outerHTML = _verifyFormHTML(key, label, emoji);
}
function cancelVerify(key) {
  var wrap = document.getElementById('vi-' + key);
  if (wrap && _verifyOriginals[key]) wrap.outerHTML = _verifyOriginals[key];
}
function _verifyFormHTML(key, label, emoji) {
  return '<div class="verify-item vi-form-wrap" id="vi-' + key + '">'
    + '<div class="verify-icon unverified">' + emoji + '</div>'
    + '<div class="vi-form">'
    + '<input class="vi-input" type="tel" inputmode="numeric" maxlength="11" '
    +   'id="' + key + '-num" name="' + key + '_number" placeholder="' + label + ' number (09xxxxxxxxx)">'
    + '<div class="vi-form-row">'
    + '<button class="vi-cancel" onclick="cancelVerify(\'' + key + '\')" type="button">Cancel</button>'
    + '<button class="vi-submit" type="button" onclick="submitVerify(\'' + key + '\', \'' + label + '\', \'' + emoji + '\')">Send ₱1 →</button>'
    + '</div></div></div>';
}
function submitVerify(key, label, emoji) {
  var numEl = document.getElementById(key + '-num');
  var num = numEl ? numEl.value.trim() : '';
  if (!num || num.length < 10) { _showToast('Enter a valid 11-digit number', 'error'); return; }
  // POST to backend
  fetch('/profile/verify-' + key, {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: key + '_number=' + encodeURIComponent(num),
  }).then(function(r){ return r.text(); }).then(function(html){
    var wrap = document.getElementById('vi-' + key);
    if (wrap) wrap.outerHTML = html;
    _showToast('₱1 sent! Check your ' + label + ' for the reference number.', 'success');
  }).catch(function(){ _showToast('Network error — try again', 'error'); });
}

/* ── Toast ── */
function _showToast(msg, type) {
  var el = document.getElementById('flash');
  if (!el) return;
  el.innerHTML = '<div class="toast toast-' + type + '">' + msg + '</div>';
  setTimeout(function(){ el.innerHTML = ''; }, 3200);
}

/* ── Entrance animation ── */
(function() {
  var items = document.querySelectorAll('.profile-card, .profile-hero, .pf-edit-panel');
  items.forEach(function(el, i) {
    el.style.opacity = '0';
    el.style.transform = 'translateY(16px)';
    el.style.transition = 'opacity 0.4s cubic-bezier(0.16,1,0.3,1), transform 0.4s cubic-bezier(0.16,1,0.3,1)';
    setTimeout(function(){ el.style.opacity = '1'; el.style.transform = 'none'; }, 50 + i * 65);
  });
})();

/* ── Count-up ── */
(function() {
  var obs = new IntersectionObserver(function(entries) {
    entries.forEach(function(e) {
      if (!e.isIntersecting) return;
      var el = e.target, target = parseInt(el.getAttribute('data-count') || '0', 10);
      if (!target) return;
      var s = performance.now(), dur = 900;
      (function tick(now) {
        var p = Math.min((now - s) / dur, 1);
        el.textContent = Math.floor((1 - Math.pow(1 - p, 3)) * target);
        if (p < 1) requestAnimationFrame(tick); else el.textContent = target;
      })(s);
      obs.unobserve(el);
    });
  }, {threshold: 0.5});
  document.querySelectorAll('[data-count]').forEach(function(el){ obs.observe(el); });
})();

/* ── Trust bar animation ── */
(function() {
  var fill = document.querySelector('.profile-trust-fill');
  if (fill) {
    var target = fill.style.width; fill.style.width = '0%';
    setTimeout(function(){ fill.style.transition = 'width 1.2s cubic-bezier(0.16,1,0.3,1)'; fill.style.width = target; }, 400);
  }
})();

/* ── Scroll-hide nav ── */
(function() {
  var header = document.querySelector('.app-header');
  var nav = document.querySelector('.bottom-nav');
  var main = document.querySelector('.app-main');
  var lastY = 0, ticking = false;
  function update(y) {
    var hiding = y - lastY > 8 && y > 60;
    var showing = lastY - y > 8;
    if (hiding)  { if (header) header.classList.add('header-hidden');    if (nav) nav.classList.add('nav-hidden'); }
    if (showing) { if (header) header.classList.remove('header-hidden'); if (nav) nav.classList.remove('nav-hidden'); }
    if (Math.abs(y - lastY) > 8) lastY = y;
    ticking = false;
  }
  if (main) main.addEventListener('scroll', function(){ if (!ticking){ requestAnimationFrame(function(){ update(main.scrollTop); }); ticking=true; } }, {passive:true});
  window.addEventListener('scroll', function(){ if (!ticking){ requestAnimationFrame(function(){ update(window.scrollY); }); ticking=true; } }, {passive:true});
})();

/* ── PWA ── */
if ('serviceWorker' in navigator) window.addEventListener('load', function(){ navigator.serviceWorker.register('/static/sw.js'); });
""")

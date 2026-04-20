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
        _avatar_card(user),
        _trust_photo_card(user),
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

    avatar_inner = (
        Img(id="avatar-img", src=user.avatar_url, alt="Avatar", cls="avatar-photo")
        if user.avatar_url else
        Span(initials, id="avatar-initials")
    )

    return Div(cls="profile-hero")(
        Div(cls="avatar")(
            avatar_inner,
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


# ─── Avatar upload card ─────────────────────────────────────────────────────────

def _avatar_card(user: UserProfile) -> FT:
    return Div(cls="profile-card")(
        Div(cls="pf-photo-header")(
            Div(cls="pf-photo-title-row")(
                Div("🖼️", cls="pf-photo-icon"),
                Div(cls="pf-photo-title-block")(
                    Div("Profile Photo", cls="profile-card-title", style="margin:0"),
                    Div(
                        "Photo set ✓" if user.avatar_url else "No photo — add one to build trust",
                        cls="pf-photo-status " + ("pf-photo-ok" if user.avatar_url else "pf-photo-none"),
                    ),
                ),
            ),
        ),
        P(
            "Your profile photo is shown to deal counterparties. "
            "Any file you upload is automatically re-encoded — no malicious content can pass through.",
            cls="pf-photo-hint",
        ),
        Form(
            id="avatar-form",
            hx_post="/profile/avatar",
            hx_target="#flash",
            hx_swap="innerHTML",
            hx_encoding="multipart/form-data",
        )(
            Div(cls="avatar-upload-area", id="avatar-drop-area")(
                Div(cls="avatar-preview-wrap")(
                    Img(
                        src=user.avatar_url, alt="Current avatar",
                        cls="avatar-preview-img",
                    ) if user.avatar_url else Div(cls="avatar-preview-placeholder")("📷"),
                ),
                Div(cls="avatar-upload-text")(
                    Label(
                        "Choose photo" if not user.avatar_url else "Replace photo",
                        for_="avatar-file-input",
                        cls="avatar-choose-btn",
                    ),
                    P("JPEG or PNG · max 2 MB", cls="avatar-type-hint"),
                ),
                Input(
                    id="avatar-file-input",
                    type="file",
                    name="avatar",
                    accept="image/jpeg,image/png,image/webp",
                    style="display:none",
                    onchange="previewAvatar(this)",
                ),
            ),
            Button(
                Span(cls="htmx-indicator"),
                "Upload Photo",
                type="submit",
                id="avatar-submit-btn",
                cls="pf-save-btn",
                style="margin-top:12px;display:none",
            ),
        ),
    )


# ─── Real-time trust photo card ─────────────────────────────────────────────────

def _trust_photo_card(user: UserProfile) -> FT:
    taken_label = ""
    if user.trust_photo_taken_at:
        try:
            from datetime import timezone
            dt = user.trust_photo_taken_at
            taken_label = dt.strftime("%-d %b %Y")
        except Exception:
            taken_label = "previously"

    existing = Div(id="trust-photo-card")(
        Img(src=user.trust_photo_url, cls="trust-photo-result", alt="Trust photo"),
        P(f"📸 Taken {taken_label} · Visible to deal counterparties", cls="trust-photo-taken"),
        Button("Retake", cls="tp-retake-btn", onclick="startTrustCamera()"),
    ) if user.trust_photo_url else Div(id="trust-photo-card")(
        Div(cls="tp-empty")(
            Div("📸", cls="tp-empty-icon"),
            P("No trust photo yet", cls="tp-empty-label"),
        ),
    )

    return Div(cls="profile-card")(
        Div(cls="pf-photo-header")(
            Div(cls="pf-photo-title-row")(
                Div("🤳", cls="pf-photo-icon"),
                Div(cls="pf-photo-title-block")(
                    Div("Real-Time Trust Photo", cls="profile-card-title", style="margin:0"),
                    Div(
                        "Trust photo on file ✓" if user.trust_photo_url else "Optional · boosts buyer confidence",
                        cls="pf-photo-status " + ("pf-photo-ok" if user.trust_photo_url else "pf-photo-none"),
                    ),
                ),
            ),
        ),
        P(
            "Take a live selfie using your device camera — this is NOT a file upload. "
            "It shows deal partners you're a real, present person. "
            "This is extra trust info only, not required for verification.",
            cls="pf-photo-hint",
        ),

        # Camera UI (hidden until activated)
        Div(id="trust-camera-wrap", style="display:none")(
            # Status badge
            Div(id="trust-status", cls="trust-status trust-status-detecting")(
                "🔍 Position your face in the oval…"
            ),
            # Video + canvas overlay stacked
            Div(cls="trust-video-wrap")(
                Video(id="trust-video", autoplay=True, playsinline=True, muted=True, cls="trust-camera-feed"),
                Canvas(id="trust-overlay", cls="trust-overlay"),
            ),
            # Liveness progress bar
            Div(cls="trust-live-bar-track")(
                Div(id="trust-live-bar", cls="trust-live-bar", style="width:0%"),
            ),
            Div(id="trust-bar-label", cls="trust-bar-label")("Liveness scan starting…"),
            # Challenge prompt (hidden until needed)
            Div(id="trust-challenge", cls="trust-challenge", style="visibility:hidden"),
            # Offscreen pixel-analysis canvas (never shown)
            Canvas(id="trust-canvas", style="position:absolute;left:-9999px;top:-9999px;width:1px;height:1px"),
            Div(cls="trust-camera-controls")(
                Button("Cancel", cls="tp-cancel-btn", onclick="cancelTrustCamera()", type="button"),
            ),
        ),

        existing,

        Button(
            "📷 Take Live Photo",
            cls="pf-save-btn",
            id="tp-open-btn",
            style="margin-top:12px",
            type="button",
            onclick="startTrustCamera()",
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
                Div("🔔", cls="settings-item-icon"),
                Div("Notifications", cls="settings-item-label"),
                Div(id="notif-toggle-label",
                    style="font-size:0.78rem;color:var(--muted);margin-right:8px"),
                Span("›", cls="settings-item-arrow"),
                cls="settings-item",
                id="notif-toggle-btn",
                onclick="handleNotifToggle()",
                type="button",
            ),
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
        Script(src="/static/js/app.js"),
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

/* ── Avatar preview before upload ── */
function previewAvatar(input) {
  var file = input.files[0];
  if (!file) return;
  var reader = new FileReader();
  reader.onload = function(e) {
    var wrap = document.querySelector('.avatar-preview-wrap');
    if (!wrap) return;
    wrap.innerHTML = '<img src="' + e.target.result + '" class="avatar-preview-img" alt="Preview">';
    var btn = document.getElementById('avatar-submit-btn');
    if (btn) btn.style.display = '';
  };
  reader.readAsDataURL(file);
}

/* ── Real-time trust photo — liveness detection ─────────────────────────────
   Three-layer anti-spoofing:
   1. Motion analysis   — frame pixel differences prove live video (not a photo)
   2. Face presence     — FaceDetector API (Chrome/Edge) with skin-tone fallback
   3. Random challenge  — user must perform a head gesture to spike motion
   ── */
var _trustStream    = null;
var _trustInterval  = null;
var _manualTimer    = null;
var _trustState     = 'idle';   // idle | detecting | challenging | captured
var _prevFrameData  = null;
var _motionHistory  = [];
var _livenessScore  = 0;
var _faceDetector   = null;
var _challenges     = ['Blink slowly', 'Nod your head', 'Look left', 'Look right'];
var _MOTION_MICRO   = 1.2;   // avg pixel diff for natural micro-movement
var _MOTION_ACTION  = 7;     // avg pixel diff for deliberate gesture
var _SCORE_THRESH   = 45;    // liveness score before challenge is issued

function startTrustCamera() {
  var wrap    = document.getElementById('trust-camera-wrap');
  var openBtn = document.getElementById('tp-open-btn');
  var card    = document.getElementById('trust-photo-card');
  if (!wrap) return;

  _trustState = 'idle'; _livenessScore = 0;
  _prevFrameData = null; _motionHistory = [];

  navigator.mediaDevices.getUserMedia({
    video: { facingMode: { ideal: 'user' }, width: { ideal: 640 }, height: { ideal: 640 } }
  }).then(function(stream) {
    _trustStream = stream;
    var video = document.getElementById('trust-video');
    video.srcObject = stream;
    wrap.style.display = '';
    if (openBtn) openBtn.style.display = 'none';
    if (card)    card.style.display    = 'none';
    _resetLivenessUI();

    // FaceDetector API — Chrome/Edge only; graceful fallback to skin-tone heuristic
    if ('FaceDetector' in window) {
      try { _faceDetector = new FaceDetector({ maxDetectedFaces: 1, fastMode: true }); }
      catch(e) { _faceDetector = null; }
    }

    video.addEventListener('loadeddata', function() {
      _syncOverlay();
      _trustState   = 'detecting';
      _trustInterval = setInterval(_liveLoop, 150);
      // Fallback: show manual capture button if liveness stalls > 25 s
      _manualTimer = setTimeout(_showFallbackBtn, 25000);
    }, { once: true });

  }).catch(function() {
    _showToast('Camera access denied — allow camera permission and try again.', 'error');
  });
}

function _syncOverlay() {
  var video   = document.getElementById('trust-video');
  var overlay = document.getElementById('trust-overlay');
  if (!video || !overlay) return;
  overlay.width  = video.videoWidth  || 640;
  overlay.height = video.videoHeight || 640;
}

async function _liveLoop() {
  var video = document.getElementById('trust-video');
  if (!video || video.readyState < 2 || _trustState === 'captured') return;
  var w = video.videoWidth, h = video.videoHeight;
  if (!w || !h) return;

  // ── 1. Sample frame at ¼ resolution (speed) ───────────────────────────────
  var canvas = document.getElementById('trust-canvas');
  var scale  = 0.25;
  var sw = Math.floor(w * scale), sh = Math.floor(h * scale);
  canvas.width = sw; canvas.height = sh;
  var ctx = canvas.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(video, 0, 0, sw, sh);
  var px = ctx.getImageData(0, 0, sw, sh).data;

  // ── 2. Motion score (avg RGB diff per pixel vs previous frame) ────────────
  var motion = 0;
  if (_prevFrameData && _prevFrameData.length === px.length) {
    for (var i = 0; i < px.length; i += 4) {
      motion += (Math.abs(px[i]   - _prevFrameData[i])
               + Math.abs(px[i+1] - _prevFrameData[i+1])
               + Math.abs(px[i+2] - _prevFrameData[i+2])) / 3;
    }
    motion /= px.length / 4;
  }
  _prevFrameData = new Uint8ClampedArray(px);
  _motionHistory.push(motion);
  if (_motionHistory.length > 20) _motionHistory.shift();

  // ── 3. Face detection ─────────────────────────────────────────────────────
  var hasFace = false;
  if (_faceDetector) {
    try { var faces = await _faceDetector.detect(video); hasFace = faces.length > 0; }
    catch(e) {}
  }
  if (!hasFace) hasFace = _skinToneCheck(px, sw, sh);

  // ── 4. Draw oval guide ───────────────────────────────────────────────────
  _drawOval(hasFace);

  // ── 5. Averages ──────────────────────────────────────────────────────────
  var avgAll    = _motionHistory.reduce(function(a,b){return a+b;},0) / (_motionHistory.length||1);
  var recent5   = _motionHistory.slice(-5).reduce(function(a,b){return a+b;},0) / 5;

  // ── 6. State machine ─────────────────────────────────────────────────────
  if (_trustState === 'detecting') {
    // Natural micro-motion (breathing, eye movement) accumulates score
    if (hasFace && avgAll > _MOTION_MICRO)  _livenessScore = Math.min(_livenessScore + 3, 100);
    else if (hasFace)                        _livenessScore = Math.min(_livenessScore + 1, 100);
    else                                     _livenessScore = Math.max(_livenessScore - 1, 0);

    _setStatus(hasFace ? '✓ Face detected — hold still…' : '🔍 Looking for face…', hasFace);
    _setBarLabel(hasFace ? 'Analyzing liveness…' : 'Position your face in the oval');
    _setBar(_livenessScore);

    if (_livenessScore >= _SCORE_THRESH && hasFace) {
      _trustState = 'challenging';
      var ch = _challenges[Math.floor(Math.random() * _challenges.length)];
      _showChallenge('👉 ' + ch);
      _setStatus('Challenge: ' + ch, true);
      _setBarLabel('Perform the action to confirm you\'re live');
    }

  } else if (_trustState === 'challenging') {
    // Need a motion spike — deliberate head/face action
    if (recent5 > _MOTION_ACTION) {
      _trustState = 'captured';
      clearInterval(_trustInterval); clearTimeout(_manualTimer);
      _setBar(100); _setBarLabel('✓ Liveness confirmed!');
      _setStatus('✓ Live person confirmed — capturing…', true);
      _hideChallenge();
      setTimeout(captureTrustPhoto, 700);
    }
  }
}

function _skinToneCheck(px, w, h) {
  // Sample center 50% of the quarter-resolution frame for skin-tone pixels
  var x0 = Math.floor(w*0.25), y0 = Math.floor(h*0.25);
  var x1 = Math.floor(w*0.75), y1 = Math.floor(h*0.75);
  var skin = 0, total = 0;
  for (var y = y0; y < y1; y++) {
    for (var x = x0; x < x1; x++) {
      var i = (y * w + x) * 4;
      var r = px[i], g = px[i+1], b = px[i+2];
      // Inclusive range: fair → dark brown (Filipino skin tones)
      if (r > 60 && g > 25 && b > 10 && r > b && r > g * 0.75 && r - b > 10) skin++;
      total++;
    }
  }
  return total > 0 && skin / total > 0.04;
}

function _drawOval(hasFace) {
  var ov = document.getElementById('trust-overlay');
  if (!ov) return;
  var ctx = ov.getContext('2d');
  var ow = ov.width, oh = ov.height;
  ctx.clearRect(0, 0, ow, oh);
  var cx = ow/2, cy = oh/2, rx = ow*0.32, ry = oh*0.42;

  // Darken area outside oval
  ctx.save();
  ctx.fillStyle = 'rgba(0,0,0,0.38)';
  ctx.fillRect(0, 0, ow, oh);
  ctx.globalCompositeOperation = 'destination-out';
  ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI*2); ctx.fill();
  ctx.restore();

  // Oval border
  ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI*2);
  ctx.strokeStyle = hasFace ? '#34D399' : 'rgba(255,255,255,0.55)';
  ctx.lineWidth   = hasFace ? 3.5 : 2;
  ctx.stroke();

  // Corner brackets when face found
  if (hasFace) {
    var x = cx-rx, y = cy-ry, x2 = cx+rx, y2 = cy+ry, cs = 18;
    ctx.strokeStyle = '#34D399'; ctx.lineWidth = 3;
    [[x,y+cs,x,y,x+cs,y],[x2-cs,y,x2,y,x2,y+cs],
     [x,y2-cs,x,y2,x+cs,y2],[x2-cs,y2,x2,y2,x2,y2-cs]].forEach(function(p){
      ctx.beginPath(); ctx.moveTo(p[0],p[1]); ctx.lineTo(p[2],p[3]); ctx.lineTo(p[4],p[5]); ctx.stroke();
    });
  }
}

function _setStatus(txt, ok) {
  var el = document.getElementById('trust-status');
  if (!el) return;
  el.textContent = txt;
  el.className = 'trust-status ' + (ok ? 'trust-status-ok' : 'trust-status-detecting');
}
function _setBar(pct) {
  var el = document.getElementById('trust-live-bar');
  if (el) el.style.width = Math.min(pct, 100) + '%';
}
function _setBarLabel(txt) {
  var el = document.getElementById('trust-bar-label');
  if (el) el.textContent = txt;
}
function _showChallenge(txt) {
  var el = document.getElementById('trust-challenge');
  if (!el) return;
  el.textContent = txt; el.style.visibility = '';
  el.classList.add('trust-challenge-pulse');
}
function _hideChallenge() {
  var el = document.getElementById('trust-challenge');
  if (el) { el.style.visibility = 'hidden'; el.classList.remove('trust-challenge-pulse'); }
}
function _resetLivenessUI() {
  _setStatus('🔍 Position your face in the oval…', false);
  _setBar(0); _setBarLabel('Liveness scan starting…'); _hideChallenge();
}
function _showFallbackBtn() {
  if (_trustState === 'captured') return;
  var ctrl = document.querySelector('.trust-camera-controls');
  if (!ctrl) return;
  var btn = document.createElement('button');
  btn.type='button'; btn.className='tp-capture-btn';
  btn.textContent='📷 Capture Manually';
  btn.onclick = function(){
    _trustState = 'captured';
    clearInterval(_trustInterval);
    captureTrustPhoto();
  };
  ctrl.prepend(btn);
}

function captureTrustPhoto() {
  var video  = document.getElementById('trust-video');
  var canvas = document.getElementById('trust-canvas');
  if (!video || !canvas) return;
  // Capture at full native resolution
  canvas.width = video.videoWidth; canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);

  canvas.toBlob(function(blob) {
    if (_trustStream) { _trustStream.getTracks().forEach(function(t){t.stop();}); _trustStream=null; }
    var fd = new FormData();
    fd.append('trust_photo', blob, 'capture.jpg');
    var m = document.cookie.match(/(?:^|;[ ]*)csrf_token=([^;]*)/);
    var hdrs = m ? {'X-CSRF-Token': decodeURIComponent(m[1])} : {};

    fetch('/profile/trust-photo', {method:'POST', headers:hdrs, body:fd})
      .then(function(r){return r.text();})
      .then(function(html){
        var flash = document.getElementById('flash');
        if (flash) { flash.innerHTML = html; setTimeout(function(){flash.innerHTML='';}, 3500); }
        document.getElementById('trust-camera-wrap').style.display = 'none';
        var ob = document.getElementById('tp-open-btn');   if (ob) ob.style.display = '';
        var cd = document.getElementById('trust-photo-card'); if (cd) cd.style.display = '';
      })
      .catch(function(){ _showToast('Upload failed — please try again', 'error'); });
  }, 'image/jpeg', 0.92);
}

function cancelTrustCamera() {
  clearInterval(_trustInterval); clearTimeout(_manualTimer);
  if (_trustStream) { _trustStream.getTracks().forEach(function(t){t.stop();}); _trustStream=null; }
  _trustState = 'idle';
  document.getElementById('trust-camera-wrap').style.display = 'none';
  var ob = document.getElementById('tp-open-btn');    if (ob) ob.style.display = '';
  var cd = document.getElementById('trust-photo-card'); if (cd) cd.style.display = '';
}

/* ── Notification toggle ── */
(function() {
  var lbl = document.getElementById('notif-toggle-label');
  if (!lbl || !('Notification' in window)) return;
  if (Notification.permission === 'granted') {
    lbl.textContent = 'On ✓';
  } else if (Notification.permission === 'denied') {
    lbl.textContent = 'Blocked';
  } else {
    lbl.textContent = 'Off';
  }
})();

async function handleNotifToggle() {
  if (!('Notification' in window) || !('PushManager' in window)) {
    _showToast('Push notifications are not supported in this browser.', 'error'); return;
  }
  var lbl = document.getElementById('notif-toggle-label');
  if (Notification.permission === 'granted') {
    // Currently on — unsubscribe
    await telukaPushUnsubscribe();
    if (lbl) lbl.textContent = 'Off';
    _showToast('Notifications turned off.', 'success');
  } else if (Notification.permission === 'denied') {
    _showToast('Notifications are blocked — enable them in your browser settings.', 'error');
  } else {
    // Ask permission
    var perm = await Notification.requestPermission();
    if (perm === 'granted') {
      var ok = await telukaPushSubscribe();
      if (lbl) lbl.textContent = ok ? 'On ✓' : 'Off';
      _showToast(ok ? 'Notifications enabled!' : 'Could not subscribe — try again.', ok ? 'success' : 'error');
    } else {
      if (lbl) lbl.textContent = 'Blocked';
    }
  }
}

/* ── PWA ── */
if ('serviceWorker' in navigator) window.addEventListener('load', function(){ navigator.serviceWorker.register('/static/sw.js'); });
""")

from fasthtml.common import *

from schemas.transaction import Transaction, TransactionStatus
from schemas.user import UserProfile, KYCStatus, TrustLevel


def change_pin_page(has_pin: bool) -> FT:
    title = "Change PIN" if has_pin else "Set Security PIN"
    back_href = "/profile"
    return Html(
        Head(
            Meta(charset="UTF-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Title(f"{title} — Teluka"),
            Link(rel="preconnect", href="https://fonts.googleapis.com"),
            Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
            Link(href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap", rel="stylesheet"),
            Link(rel="stylesheet", href="/static/css/app.css"),
            Link(rel="stylesheet", href="/static/css/dashboard.css"),
            Script(src="https://unpkg.com/htmx.org@1.9.12"),
            Script(src="/static/js/app.js"),
            Script("(function(){var t=localStorage.getItem('teluka-theme')||(window.matchMedia('(prefers-color-scheme:light)').matches?'light':'dark');document.documentElement.setAttribute('data-theme',t);})();"),
        ),
        Body(
            Div(cls="app-layout")(
                Div(cls="dash-body")(
                    Header(cls="app-header")(
                        A("← Back", href=back_href, cls="app-header-back"),
                        Div(title, cls="app-header-logo"),
                        Div(cls="app-header-actions"),
                    ),
                    Main(cls="app-main")(
                        Div(cls="app-content", style="max-width:480px;margin:0 auto;padding:20px 16px")(
                            Div(cls="profile-card")(
                                Div(cls="pf-card-header")(
                                    Div(cls="pf-card-icon-wrap")(_icon_lock()),
                                    Div(cls="pf-card-header-text")(
                                        Div(title, cls="profile-card-title"),
                                        Div(
                                            "Enter your current PIN and a new 4-digit PIN." if has_pin
                                            else "Set a 4-digit PIN required to release payments.",
                                            cls="pf-card-sub",
                                        ),
                                    ),
                                ),
                                Div(id="pin-feedback"),
                                Form(
                                    hx_post="/profile/change-pin",
                                    hx_target="#pin-feedback",
                                    hx_swap="innerHTML",
                                    hx_on__htmx_after_request="onPinSaved(event)",
                                    cls="pf-form",
                                )(
                                    *(
                                        [
                                            Div(cls="pf-field")(
                                                Label("Current PIN", cls="pf-label", for_="pin-current"),
                                                Div(cls="pf-input-wrap")(
                                                    Span("🔒", cls="pf-input-icon"),
                                                    Input(
                                                        id="pin-current", name="current_pin", type="password",
                                                        inputmode="numeric", maxlength="4", placeholder="••••",
                                                        cls="pf-input", autocomplete="current-password",
                                                    ),
                                                ),
                                            ),
                                        ] if has_pin else []
                                    ),
                                    Div(cls="pf-field")(
                                        Label("New PIN", cls="pf-label", for_="pin-new"),
                                        Div(cls="pf-input-wrap")(
                                            Span("🔑", cls="pf-input-icon"),
                                            Input(
                                                id="pin-new", name="new_pin", type="password",
                                                inputmode="numeric", maxlength="4", placeholder="••••",
                                                cls="pf-input", autocomplete="new-password",
                                            ),
                                        ),
                                    ),
                                    Div(cls="pf-field")(
                                        Label("Confirm New PIN", cls="pf-label", for_="pin-confirm"),
                                        Div(cls="pf-input-wrap")(
                                            Span("🔑", cls="pf-input-icon"),
                                            Input(
                                                id="pin-confirm", name="confirm_pin", type="password",
                                                inputmode="numeric", maxlength="4", placeholder="••••",
                                                cls="pf-input", autocomplete="new-password",
                                            ),
                                        ),
                                    ),
                                    Button(
                                        "Set PIN" if not has_pin else "Change PIN",
                                        type="submit", cls="pf-save-btn",
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            Script("""
function onPinSaved(event) {
  if (event.detail.successful && event.detail.xhr.status === 200) {
    var resp = event.detail.xhr.responseText;
    if (resp && resp.indexOf('toast-success') !== -1) {
      setTimeout(function(){ window.location.href = '/profile'; }, 1500);
    }
  }
}
"""),
        ),
    )


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
        _profile_hero(user),
        _stats_strip(len(transactions), completed, user.trust_score),
        _tab_bar(),
        Div(cls="pf-tabs-body")(
            _tab_overview(user),
            _tab_photos(user),
            _tab_verify(user),
            _tab_settings(),
        ),
    )


# ─── Hero ──────────────────────────────────────────────────────────────────────

def _profile_hero(user: UserProfile) -> FT:
    initials = user.phone[-4:] if len(user.phone) >= 4 else "??"
    phone     = user.phone
    masked    = (phone[:3] + "•" * (len(phone) - 7) + phone[-4:]) if len(phone) > 7 else phone

    trust_cls = {
        TrustLevel.NEW:         "badge-trust-new",
        TrustLevel.LOW:         "badge-trust-low",
        TrustLevel.MEDIUM:      "badge-trust-medium",
        TrustLevel.HIGH:        "badge-trust-high",
        TrustLevel.BLACKLISTED: "badge-trust-blacklisted",
    }.get(user.trust_level, "badge-trust-new")

    kyc_ok  = user.kyc_status == KYCStatus.VERIFIED
    verified = user.gcash_verified or user.maya_verified

    avatar_inner = (
        Img(id="avatar-img", src=user.avatar_url, alt="Avatar", cls="avatar-photo")
        if user.avatar_url else
        Span(initials, id="avatar-initials")
    )

    return Div(cls="pf-hero")(
        # Avatar — tapping it switches to photos tab
        Button(
            Div(cls="avatar avatar-lg")(avatar_inner, Div(cls="avatar-ring")),
            Div("✏️", cls="pf-avatar-edit-badge"),
            cls="pf-avatar-btn",
            **{"data-tab": "photos"},
            type="button",
            title="Update photo",
        ),
        Div(cls="pf-hero-info")(
            Div(masked, cls="pf-hero-name"),
            Div(user.email or "No email set", cls="pf-hero-email"),
            Div(cls="pf-hero-badges")(
                Span(
                    ("✓ " if kyc_ok else ""),
                    user.trust_level.value.title() + " Trust",
                    cls=f"profile-badge {trust_cls}",
                ),
                Span("✓ Verified" if verified else "Not verified",
                     cls="profile-badge " + ("badge-kyc-verified" if verified else "badge-kyc-unverified")),
            ),
        ),
        Button(
            _icon_edit(), " Edit",
            cls="pf-hero-edit-btn",
            onclick="focusEditForm()",
            type="button",
        ),
    )


# ─── Stats strip ───────────────────────────────────────────────────────────────

def _stats_strip(total: int, completed: int, trust_score: float) -> FT:
    pct = int(trust_score)
    return Div(cls="pf-stats-strip")(
        _stat_pill(str(total),     "Deals"),
        _stat_divider(),
        _stat_pill(str(completed), "Done"),
        _stat_divider(),
        Div(cls="pf-stat-pill")(
            Div(cls="pf-stat-score-wrap")(
                Div(f"{pct}", cls="pf-stat-val"),
                Div(cls="pf-trust-mini-bar")(
                    Div(cls="pf-trust-mini-fill", style=f"width:{pct}%"),
                ),
            ),
            Div("Trust", cls="pf-stat-lbl"),
        ),
    )


def _stat_pill(val: str, lbl: str) -> FT:
    return Div(cls="pf-stat-pill")(
        Div(val, cls="pf-stat-val", **{"data-count": val}),
        Div(lbl, cls="pf-stat-lbl"),
    )


def _stat_divider() -> FT:
    return Div(cls="pf-stat-divider")


# ─── Tab bar ───────────────────────────────────────────────────────────────────

def _tab_bar() -> FT:
    tabs = [
        ("overview", "Overview", _tab_icon_overview()),
        ("photos",   "Photos",   _tab_icon_photos()),
        ("verify",   "Verify",   _tab_icon_verify()),
        ("settings", "Settings", _tab_icon_settings()),
    ]
    return Div(cls="pf-tab-bar", id="pf-tab-bar")(
        *[
            Button(
                icon,
                Span(label, cls="pf-tab-label"),
                cls="pf-tab-btn" + (" pf-tab-active" if i == 0 else ""),
                **{"data-tab": key},
                type="button",
            )
            for i, (key, label, icon) in enumerate(tabs)
        ]
    )


# ─── Tab: Overview ─────────────────────────────────────────────────────────────

def _tab_overview(user: UserProfile) -> FT:
    pct = int(user.trust_score)
    return Div(cls="pf-tab-panel pf-tab-panel-active", **{"data-panel": "overview"})(

        # Account Info card — auto-saves on blur
        Div(cls="profile-card")(
            Div(cls="pf-card-header")(
                Div(cls="pf-card-icon-wrap")(_icon_user_sm()),
                Div(cls="pf-card-header-text")(
                    Div("Account Info", cls="profile-card-title"),
                    Div("Tap a field to edit — saves automatically", cls="pf-card-sub"),
                ),
            ),
            Div(cls="pf-form")(
                Div(cls="pf-field")(
                    Div(cls="pf-field-row")(
                        Label("Email address", cls="pf-label", for_="pf-email"),
                        Div(id="pf-email-status", cls="pf-email-status"),
                    ),
                    Div(cls="pf-input-wrap")(
                        Span("✉️", cls="pf-input-icon"),
                        Input(
                            id="pf-email", name="email", type="email",
                            value=user.email or "",
                            placeholder="you@example.com",
                            cls="pf-input", autocomplete="email",
                            hx_post="/profile/edit",
                            hx_trigger="blur changed",
                            hx_target="#pf-email-status",
                            hx_swap="innerHTML",
                        ),
                    ),
                    P("Used for OTP codes. Never shared.", cls="pf-hint"),
                ),
                Div(cls="pf-field")(
                    Label("Phone number", cls="pf-label"),
                    Div(cls="pf-input-wrap pf-readonly")(
                        Span("📱", cls="pf-input-icon"),
                        Input(value=user.phone, type="tel", cls="pf-input", disabled=True),
                    ),
                    P("Your phone is your identity — cannot be changed.", cls="pf-hint"),
                ),
            ),
        ),

        # PIN card
        Div(cls="profile-card pf-pin-card")(
            Div(cls="pf-pin-row")(
                Div(cls="pf-card-icon-wrap")(_icon_lock()),
                Div(cls="pf-pin-body")(
                    Div("Security PIN", cls="pf-pin-title"),
                    Div(
                        "PIN is set — required to release payments ✓" if user.pin_hash
                        else "No PIN set — you need one to release payments",
                        cls="pf-pin-sub " + ("pf-pin-ok" if user.pin_hash else "pf-pin-warn"),
                    ),
                ),
                A(
                    "Change →" if user.pin_hash else "Set →",
                    href="/profile/change-pin",
                    cls="pf-pin-link",
                ),
            ),
        ),

        # Trust score card
        Div(cls="profile-card")(
            Div(cls="pf-card-header")(
                Div(cls="pf-card-icon-wrap")(_icon_star()),
                Div(cls="pf-card-header-text")(
                    Div("Trust Score", cls="profile-card-title"),
                    Div(f"{pct} / 100 · {user.trust_level.value.title()} level", cls="pf-card-sub"),
                ),
                Div(f"{pct}", cls="pf-trust-big-num"),
            ),
            Div(cls="profile-trust-bar", style="margin-top:12px")(
                Div(cls="profile-trust-fill", style=f"width:{pct}%"),
            ),
            P(_trust_hint(pct), cls="pf-trust-hint"),
        ),
    )


# ─── Tab: Photos ───────────────────────────────────────────────────────────────

def _tab_photos(user: UserProfile) -> FT:
    return Div(cls="pf-tab-panel", **{"data-panel": "photos"})(
        _avatar_card(user),
        _trust_photo_card(user),
    )


def _avatar_card(user: UserProfile) -> FT:
    return Div(cls="profile-card")(
        Div(cls="pf-card-header")(
            Div(cls="pf-card-icon-wrap")("🖼️"),
            Div(cls="pf-card-header-text")(
                Div("Profile Photo", cls="profile-card-title"),
                Div(
                    "Photo set ✓" if user.avatar_url else "No photo — add one to build trust",
                    cls="pf-card-sub " + ("pf-photo-ok" if user.avatar_url else ""),
                ),
            ),
        ),
        P("Shown to deal partners. Files are re-encoded — no malicious content can pass through.",
          cls="pf-photo-hint"),
        Form(
            id="avatar-form",
            hx_post="/profile/avatar",
            hx_target="#flash",
            hx_swap="innerHTML",
            hx_encoding="multipart/form-data",
        )(
            Div(cls="avatar-upload-area", id="avatar-drop-area")(
                Div(cls="avatar-preview-wrap")(
                    Img(src=user.avatar_url, alt="Current avatar", cls="avatar-preview-img")
                    if user.avatar_url else
                    Div(cls="avatar-preview-placeholder")("📷"),
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
                    id="avatar-file-input", type="file", name="avatar",
                    accept="image/jpeg,image/png,image/webp",
                    style="display:none",
                    onchange="previewAvatar(this)",
                ),
            ),
            Button(
                Span(cls="htmx-indicator"), "Upload Photo",
                type="submit", id="avatar-submit-btn",
                cls="pf-save-btn",
                style="margin-top:12px;display:none",
            ),
        ),
    )


def _trust_photo_card(user: UserProfile) -> FT:
    taken_label = ""
    if user.trust_photo_taken_at:
        try:
            dt = user.trust_photo_taken_at
            taken_label = dt.strftime("%-d %b %Y")
        except Exception:
            taken_label = "previously"

    existing = (
        Div(id="trust-photo-card")(
            Img(src=user.trust_photo_url, cls="trust-photo-result", alt="Trust photo"),
            P(f"📸 Taken {taken_label} · Visible to deal partners", cls="trust-photo-taken"),
            Button("Retake", cls="tp-retake-btn", onclick="startTrustCamera()", type="button"),
        )
        if user.trust_photo_url else
        Div(id="trust-photo-card")(
            Div(cls="tp-empty")(
                Div("🤳", cls="tp-empty-icon"),
                P("No trust photo yet", cls="tp-empty-label"),
            ),
        )
    )

    return Div(cls="profile-card")(
        Div(cls="pf-card-header")(
            Div(cls="pf-card-icon-wrap")("🤳"),
            Div(cls="pf-card-header-text")(
                Div("Real-Time Trust Photo", cls="profile-card-title"),
                Div(
                    "On file ✓ · boosts buyer confidence" if user.trust_photo_url
                    else "Optional · boosts buyer confidence",
                    cls="pf-card-sub " + ("pf-photo-ok" if user.trust_photo_url else ""),
                ),
            ),
        ),
        P("Live selfie via your camera — shows deal partners you're a real, present person. "
          "Not required for verification, but builds extra trust.",
          cls="pf-photo-hint"),

        # Camera UI
        Div(id="trust-camera-wrap", style="display:none")(
            Div(id="trust-status", cls="trust-status trust-status-detecting")(
                "🔍 Position your face in the oval…"
            ),
            Div(cls="trust-video-wrap")(
                Video(id="trust-video", autoplay=True, playsinline=True, muted=True, cls="trust-camera-feed"),
                Canvas(id="trust-overlay", cls="trust-overlay"),
            ),
            Div(cls="trust-live-bar-track")(
                Div(id="trust-live-bar", cls="trust-live-bar", style="width:0%"),
            ),
            Div(id="trust-bar-label", cls="trust-bar-label")("Liveness scan starting…"),
            Div(id="trust-challenge", cls="trust-challenge", style="visibility:hidden"),
            Canvas(id="trust-canvas", style="position:absolute;left:-9999px;top:-9999px;width:1px;height:1px"),
            Div(cls="trust-camera-controls")(
                Button("Cancel", cls="tp-cancel-btn", onclick="cancelTrustCamera()", type="button"),
            ),
        ),

        existing,

        Button(
            "📷 Take Live Photo",
            cls="pf-save-btn", id="tp-open-btn",
            style="margin-top:12px",
            type="button",
            onclick="startTrustCamera()",
        ),
    )


# ─── Tab: Verify ───────────────────────────────────────────────────────────────

def _tab_verify(user: UserProfile) -> FT:
    verified = user.gcash_verified or user.maya_verified
    return Div(cls="pf-tab-panel", **{"data-panel": "verify"})(

        # Status banner
        Div(cls="vc-banner " + ("vc-banner-ok" if verified else "vc-banner-pending"))(
            Div("🛡️", cls="vc-banner-icon"),
            Div(cls="vc-banner-text")(
                Div("Verified" if verified else "Not Verified", cls="vc-banner-title"),
                Div(
                    "Your wallet is linked and confirmed." if verified
                    else "Link a wallet to unlock all features.",
                    cls="vc-banner-sub",
                ),
            ),
        ) if True else None,

        # Benefits
        Div(cls="profile-card")(
            Div(cls="pf-card-header")(
                Div(cls="pf-card-icon-wrap")("⭐"),
                Div("Why verify?", cls="profile-card-title"),
            ),
            Div(cls="vc-benefits-grid")(
                _benefit("📈", "+20 Trust",      "Instant score boost"),
                _benefit("💰", "₱50k limit",    "vs ₱5k unverified"),
                _benefit("⚡", "Priority help",  "24h vs 72h disputes"),
                _benefit("✓",  "Verified badge", "Visible on all deals"),
            ),
        ),

        # Wallet cards
        Div(cls="profile-card")(
            Div(cls="pf-card-header")(
                Div(cls="pf-card-icon-wrap")("💳"),
                Div(cls="pf-card-header-text")(
                    Div("Link a Wallet", cls="profile-card-title"),
                    Div("Teluka sends ₱1 to confirm ownership", cls="pf-card-sub"),
                ),
            ),
            Div(cls="vc-wallet-list")(
                _wallet_item("gcash", "GCash",  "💚", "#06B",    user.gcash_verified),
                _wallet_item("maya",  "Maya",   "💜", "#7C3AED", user.maya_verified),
            ),
        ),
    )


def _wallet_item(key: str, label: str, emoji: str, color: str, verified: bool) -> FT:
    if verified:
        return Div(cls="vc-wallet-row vc-wallet-done")(
            Div(emoji, cls="vc-wallet-emoji"),
            Div(cls="vc-wallet-info")(
                Div(label, cls="vc-wallet-name"),
                Div("✓ Linked & verified", cls="vc-wallet-status ok"),
            ),
            Div("✓", cls="vc-wallet-check"),
        )
    return Div(cls="vc-wallet-row", id=f"vi-{key}")(
        Div(emoji, cls="vc-wallet-emoji"),
        Div(cls="vc-wallet-info")(
            Div(label, cls="vc-wallet-name"),
            Div("Not linked", cls="vc-wallet-status no"),
        ),
        Button(
            "Link →",
            cls="vc-wallet-btn",
            onclick=f"startVerify('{key}')",
            type="button",
        ),
    )


# ─── Tab: Settings ─────────────────────────────────────────────────────────────

def _tab_settings() -> FT:
    return Div(cls="pf-tab-panel", **{"data-panel": "settings"})(
        # Notifications card (prominent toggle)
        Div(cls="profile-card pf-notif-card")(
            Div(cls="pf-notif-row")(
                Div(cls="pf-notif-left")(
                    Div("🔔", cls="pf-notif-icon"),
                    Div(cls="pf-notif-text")(
                        Div("Deal Alerts", cls="pf-notif-title"),
                        Div(id="notif-status-label", cls="pf-notif-sub")("Loading…"),
                    ),
                ),
                Button(
                    Div(cls="pf-toggle-knob"),
                    cls="pf-toggle-btn",
                    id="notif-toggle-btn",
                    onclick="handleNotifToggle()",
                    type="button",
                    title="Toggle deal alerts",
                ),
            ),
            P("Get notified about deal events even when the app is closed.",
              cls="pf-notif-hint"),
        ),

        Div(cls="profile-card")(
            Div(cls="settings-list")(
                Button(
                    Div("◐", cls="settings-item-icon"),

                    Div("Appearance", cls="settings-item-label"),
                    Div(id="theme-label",
                        style="font-size:0.78rem;color:var(--muted);margin-right:8px"),
                    Span("›", cls="settings-item-arrow"),
                    cls="settings-item",
                    onclick="toggleTheme(); updateThemeLabel();",
                    type="button",
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
            ),
        ),
        # Sign out as a separate danger card
        Div(cls="profile-card")(
            Form(action="/logout", method="post")(
                Button(
                    Div("↩", cls="settings-item-icon"),
                    Div("Sign Out", cls="settings-item-label"),
                    cls="settings-item danger", type="submit",
                    style="width:100%",
                ),
            ),
        ),
    )


# ─── Verify modal fragments (returned by HTMX) ─────────────────────────────────

def verify_modal_html(key: str, label: str, emoji: str) -> FT:
    return Div(cls="verify-item vi-form-wrap", id=f"vi-{key}")(
        Div(emoji, cls="verify-icon unverified"),
        Div(cls="vi-form")(
            Input(
                name=f"{key}_number", id=f"{key}-num", type="tel",
                placeholder=f"Your {label} number (09xxxxxxxxx)",
                cls="vi-input", inputmode="numeric", maxlength="11",
            ),
            Div(cls="vi-form-row")(
                Button("Cancel", type="button", cls="vi-cancel",
                       onclick=f"cancelVerify('{key}')"),
                Button("Send ₱1 →", cls="vi-submit",
                       hx_post=f"/profile/verify-{key}",
                       hx_target=f"#vi-{key}",
                       hx_swap="outerHTML",
                       hx_include=f"#{key}-num"),
            ),
        ),
    )


def verify_pending_html(key: str, label: str, emoji: str) -> FT:
    return Div(cls="verify-item vi-form-wrap", id=f"vi-{key}")(
        Div(emoji, cls="verify-icon unverified"),
        Div(cls="vi-form")(
            P(f"We sent ₱1 to your {label}. Check for the reference number.", cls="vi-sent-msg"),
            Input(
                name="ref", id=f"{key}-ref", type="text",
                placeholder="Reference number (e.g. ABC123456789)",
                cls="vi-input", autocomplete="off",
            ),
            Div(cls="vi-form-row")(
                Button("Cancel", type="button", cls="vi-cancel",
                       onclick=f"cancelVerify('{key}')"),
                Button("Confirm →", cls="vi-submit",
                       hx_post=f"/profile/verify-{key}-confirm",
                       hx_target=f"#vi-{key}",
                       hx_swap="outerHTML",
                       hx_include=f"#{key}-ref"),
            ),
        ),
    )


def verify_done_html(label: str, emoji: str) -> FT:
    return Div(cls="verify-item verify-item-done")(
        Div(emoji, cls="verify-icon verified"),
        Div(
            Div(label, cls="verify-label"),
            Div("✓ Verified", cls="verify-status ok"),
        ),
        Div("✓", cls="vi-check"),
    )


# ─── Trust helpers ──────────────────────────────────────────────────────────────

def _trust_hint(pct: int) -> str:
    if pct == 0:  return "Complete your first deal to start building trust."
    if pct < 30:  return "Grows with every completed deal and verified wallet."
    if pct < 60:  return "Good progress! Verify GCash or Maya to unlock higher trust."
    if pct < 80:  return "Strong score. You're a reliable community member."
    return "Excellent! You're among Teluka's most trusted members."


def _benefit(icon: str, title: str, desc: str) -> FT:
    return Div(cls="vb-item")(
        Div(icon, cls="vb-icon"),
        Div(cls="vb-text")(
            Div(title, cls="vb-title"),
            Div(desc,  cls="vb-desc"),
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
            si("home",    "/dashboard",        _icon_home(),  "Home"),
            A(cls="sidebar-item sidebar-cta", href="/transactions/new")(_icon_plus(), "New Protected Deal"),
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

def _icon_user_sm() -> FT:
    return Svg(NotStr('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round", width="18", height="18")

def _icon_lock() -> FT:
    return Svg(NotStr('<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round", width="18", height="18")

def _icon_star() -> FT:
    return Svg(NotStr('<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round", width="18", height="18")

def _tab_icon_overview() -> FT:
    return Svg(NotStr('<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round", width="18", height="18", cls="pf-tab-icon")

def _tab_icon_photos() -> FT:
    return Svg(NotStr('<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round", width="18", height="18", cls="pf-tab-icon")

def _tab_icon_verify() -> FT:
    return Svg(NotStr('<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round", width="18", height="18", cls="pf-tab-icon")

def _tab_icon_settings() -> FT:
    return Svg(NotStr('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round", width="18", height="18", cls="pf-tab-icon")


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
        Style("""
/* ── Profile hero ── */
.pf-hero{display:flex;align-items:center;gap:14px;padding:18px 0 10px;flex-wrap:wrap}
.pf-avatar-btn{background:none;border:none;cursor:pointer;position:relative;padding:0;flex-shrink:0}
.pf-avatar-edit-badge{position:absolute;bottom:2px;right:2px;background:var(--primary);
  color:#fff;border-radius:50%;width:20px;height:20px;font-size:0.65rem;
  display:flex;align-items:center;justify-content:center;border:2px solid var(--bg)}
.avatar-lg{width:72px;height:72px;font-size:1.3rem}
.pf-hero-info{flex:1;min-width:0}
.pf-hero-name{font-weight:800;font-size:1.05rem;color:var(--text);letter-spacing:0.02em}
.pf-hero-email{font-size:0.8rem;color:var(--muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pf-hero-badges{display:flex;gap:6px;margin-top:8px;flex-wrap:wrap}
.pf-hero-edit-btn{flex-shrink:0;display:flex;align-items:center;gap:5px;padding:8px 14px;
  border-radius:999px;border:1px solid var(--border);background:var(--card-bg);
  color:var(--text);font-size:0.82rem;font-weight:600;cursor:pointer;align-self:flex-start}
.pf-hero-edit-btn:hover{border-color:var(--primary);color:var(--primary)}
.app-header-back{font-size:0.88rem;font-weight:600;color:var(--primary);text-decoration:none;padding:6px 0}

/* ── Stats strip ── */
.pf-stats-strip{display:flex;background:var(--card-bg);border-radius:16px;padding:16px;
  margin-bottom:16px;border:1px solid var(--border);align-items:center}
.pf-stat-pill{flex:1;display:flex;flex-direction:column;align-items:center;gap:4px}
.pf-stat-divider{width:1px;height:32px;background:var(--border)}
.pf-stat-val{font-size:1.4rem;font-weight:900;color:var(--text)}
.pf-stat-lbl{font-size:0.72rem;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.04em}
.pf-stat-score-wrap{display:flex;flex-direction:column;align-items:center;gap:4px}
.pf-trust-mini-bar{width:48px;height:4px;background:var(--border);border-radius:99px;overflow:hidden}
.pf-trust-mini-fill{height:100%;background:var(--primary);border-radius:99px;transition:width 1.2s cubic-bezier(.16,1,.3,1)}

/* ── Tab bar ── */
.pf-tab-bar{display:flex;background:var(--card-bg);border-radius:16px;padding:5px;
  margin-bottom:16px;gap:3px;border:1px solid var(--border)}
.pf-tab-btn{flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;
  padding:9px 4px;background:none;border:none;border-radius:12px;cursor:pointer;
  color:var(--muted);transition:all .2s;font-family:inherit}
.pf-tab-btn.pf-tab-active{background:var(--primary);color:#fff}
.pf-tab-label{font-size:0.68rem;font-weight:700;letter-spacing:.01em}

/* ── Tab panels ── */
.pf-tabs-body{min-height:300px}
.pf-tab-panel{display:none;animation:tabIn .25s cubic-bezier(.16,1,.3,1)}
.pf-tab-panel.pf-tab-panel-active{display:block}
@keyframes tabIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}

/* ── Card header pattern ── */
.pf-card-header{display:flex;align-items:center;gap:10px;margin-bottom:16px}
.pf-card-icon-wrap{width:36px;height:36px;border-radius:10px;background:rgba(13,148,136,.12);
  display:flex;align-items:center;justify-content:center;font-size:1rem;flex-shrink:0;
  color:var(--primary)}
.pf-card-header-text{flex:1;min-width:0}
.pf-card-sub{font-size:0.78rem;color:var(--muted);margin-top:1px}
.pf-trust-big-num{font-size:2rem;font-weight:900;color:var(--primary);margin-left:auto}
.pf-trust-hint{font-size:0.8rem;color:var(--muted);margin-top:10px;line-height:1.5}
.pf-photo-ok{color:#34D399}
.pf-form{display:flex;flex-direction:column;gap:12px}
.pf-field-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:4px}
.pf-field-row .pf-label{margin-bottom:0}
.pf-email-status{font-size:0.75rem;font-weight:600}
.pf-email-status .pf-email-saved{color:#34D399}

/* ── PIN card ── */
.pf-pin-card{padding:14px 16px}
.pf-pin-row{display:flex;align-items:center;gap:10px}
.pf-pin-body{flex:1}
.pf-pin-title{font-weight:700;font-size:0.9rem;color:var(--text)}
.pf-pin-sub{font-size:0.78rem;margin-top:2px}
.pf-pin-ok{color:#34D399}
.pf-pin-warn{color:#F59E0B}
.pf-pin-link{font-size:0.82rem;font-weight:700;color:var(--primary);text-decoration:none;white-space:nowrap}

/* ── Notifications card ── */
.pf-notif-card{padding:16px}
.pf-notif-row{display:flex;align-items:center;gap:12px}
.pf-notif-left{display:flex;align-items:center;gap:12px;flex:1;min-width:0}
.pf-notif-icon{font-size:1.5rem;flex-shrink:0}
.pf-notif-title{font-weight:700;font-size:0.95rem;color:var(--text)}
.pf-notif-sub{font-size:0.78rem;color:var(--muted);margin-top:2px}
.pf-notif-hint{font-size:0.78rem;color:var(--muted);margin-top:10px;line-height:1.5}
/* Toggle switch */
.pf-toggle-btn{flex-shrink:0;width:52px;height:28px;border-radius:999px;
  border:none;cursor:pointer;padding:3px;
  background:var(--border);transition:background .25s;position:relative}
.pf-toggle-btn.pf-toggle-on{background:var(--primary)}
.pf-toggle-btn.pf-toggle-blocked{background:#EF4444;cursor:not-allowed}
.pf-toggle-knob{width:22px;height:22px;border-radius:50%;background:#fff;
  box-shadow:0 1px 4px rgba(0,0,0,.25);transition:transform .25s;display:block}
.pf-toggle-btn.pf-toggle-on .pf-toggle-knob{transform:translateX(24px)}
.pf-toggle-btn.pf-toggle-blocked .pf-toggle-knob{transform:translateX(24px)}

/* ── Verify tab ── */
.vc-banner{display:flex;align-items:center;gap:12px;padding:14px 16px;border-radius:14px;
  margin-bottom:14px;border:1px solid}
.vc-banner-ok{background:rgba(52,211,153,.08);border-color:rgba(52,211,153,.25)}
.vc-banner-pending{background:rgba(245,158,11,.08);border-color:rgba(245,158,11,.25)}
.vc-banner-icon{font-size:1.6rem;flex-shrink:0}
.vc-banner-title{font-weight:800;font-size:0.95rem;color:var(--text)}
.vc-banner-sub{font-size:0.8rem;color:var(--muted);margin-top:2px}
.vc-wallet-list{display:flex;flex-direction:column;gap:10px;margin-top:4px}
.vc-wallet-row{display:flex;align-items:center;gap:12px;padding:12px 14px;
  border-radius:12px;border:1px solid var(--border);background:var(--bg)}
.vc-wallet-done{border-color:rgba(52,211,153,.3);background:rgba(52,211,153,.05)}
.vc-wallet-emoji{font-size:1.4rem;flex-shrink:0}
.vc-wallet-info{flex:1}
.vc-wallet-name{font-weight:700;font-size:0.9rem;color:var(--text)}
.vc-wallet-status{font-size:0.75rem;margin-top:2px}
.vc-wallet-status.ok{color:#34D399}
.vc-wallet-status.no{color:var(--muted)}
.vc-wallet-btn{padding:7px 16px;border-radius:999px;border:1px solid var(--primary);
  background:none;color:var(--primary);font-weight:700;font-size:0.82rem;cursor:pointer}
.vc-wallet-btn:hover{background:var(--primary);color:#fff}
.vc-wallet-check{color:#34D399;font-size:1.2rem;font-weight:900}
.vc-benefits-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:4px}
"""),
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

/* ── Tab event delegation (handles tab bar + avatar button) ── */
document.addEventListener('DOMContentLoaded', function() {
  var bar = document.getElementById('pf-tab-bar');
  if (bar) bar.addEventListener('click', function(e) {
    var btn = e.target.closest('[data-tab]');
    if (btn) switchTab(btn.getAttribute('data-tab'));
  });
  var avatarBtn = document.querySelector('.pf-avatar-btn[data-tab]');
  if (avatarBtn) avatarBtn.addEventListener('click', function() {
    switchTab(avatarBtn.getAttribute('data-tab'));
  });
});

/* ── Edit button — switch to overview and focus email input ── */
function focusEditForm() {
  switchTab('overview');
  var el = document.getElementById('pf-email');
  if (el) { el.focus(); el.scrollIntoView({behavior: 'smooth', block: 'center'}); }
}

/* ── Tab switcher ── */
function switchTab(key) {
  document.querySelectorAll('.pf-tab-btn').forEach(function(b) {
    b.classList.toggle('pf-tab-active', b.getAttribute('data-tab') === key);
  });
  document.querySelectorAll('.pf-tab-panel').forEach(function(p) {
    p.classList.toggle('pf-tab-panel-active', p.getAttribute('data-panel') === key);
  });
  localStorage.setItem('pf-tab', key);
}
(function() {
  var saved = localStorage.getItem('pf-tab');
  if (saved) switchTab(saved);
})();

/* ── Wallet verify ── */
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
  fetch('/profile/verify-' + key, {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: key + '_number=' + encodeURIComponent(num),
  }).then(function(r){ return r.text(); }).then(function(html){
    var wrap = document.getElementById('vi-' + key);
    if (wrap) wrap.outerHTML = html;
    _showToast('₱1 sent! Check your ' + label + '.', 'success');
  }).catch(function(){ _showToast('Network error — try again', 'error'); });
}

/* ── Toast ── */
function _showToast(msg, type) {
  var el = document.getElementById('flash');
  if (!el) return;
  el.innerHTML = '<div class="toast toast-' + type + '">' + msg + '</div>';
  setTimeout(function(){ el.innerHTML = ''; }, 3200);
}

/* ── Avatar preview ── */
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

/* ── Entrance animation ── */
(function() {
  var items = document.querySelectorAll('.profile-card, .pf-hero, .pf-stats-strip, .pf-tab-bar');
  items.forEach(function(el, i) {
    el.style.opacity = '0';
    el.style.transform = 'translateY(14px)';
    el.style.transition = 'opacity 0.4s cubic-bezier(0.16,1,0.3,1), transform 0.4s cubic-bezier(0.16,1,0.3,1)';
    setTimeout(function(){ el.style.opacity = '1'; el.style.transform = 'none'; }, 40 + i * 55);
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
    setTimeout(function(){ fill.style.transition = 'width 1.2s cubic-bezier(0.16,1,0.3,1)'; fill.style.width = target; }, 500);
  }
  var mini = document.querySelector('.pf-trust-mini-fill');
  if (mini) {
    var t2 = mini.style.width; mini.style.width = '0%';
    setTimeout(function(){ mini.style.transition = 'width 1.2s cubic-bezier(0.16,1,0.3,1)'; mini.style.width = t2; }, 500);
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

/* ── Real-time trust photo — liveness detection ── */
var _trustStream=null,_trustInterval=null,_manualTimer=null,_trustState='idle';
var _prevFrameData=null,_motionHistory=[],_livenessScore=0,_faceDetector=null;
var _challenges=['Blink slowly','Nod your head','Look left','Look right'];
var _MOTION_MICRO=1.2,_MOTION_ACTION=7,_SCORE_THRESH=45;

function startTrustCamera() {
  var wrap=document.getElementById('trust-camera-wrap');
  var openBtn=document.getElementById('tp-open-btn');
  var card=document.getElementById('trust-photo-card');
  if (!wrap) return;
  _trustState='idle'; _livenessScore=0; _prevFrameData=null; _motionHistory=[];
  navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'user'},width:{ideal:640},height:{ideal:640}}})
  .then(function(stream) {
    _trustStream=stream;
    var video=document.getElementById('trust-video');
    video.srcObject=stream;
    wrap.style.display=''; if (openBtn) openBtn.style.display='none'; if (card) card.style.display='none';
    _resetLivenessUI();
    if ('FaceDetector' in window) { try { _faceDetector=new FaceDetector({maxDetectedFaces:1,fastMode:true}); } catch(e){_faceDetector=null;} }
    video.addEventListener('loadeddata',function(){
      _syncOverlay(); _trustState='detecting'; _trustInterval=setInterval(_liveLoop,150);
      _manualTimer=setTimeout(_showFallbackBtn,25000);
    },{once:true});
  }).catch(function(){ _showToast('Camera access denied — allow camera permission and try again.','error'); });
}
function _syncOverlay(){var v=document.getElementById('trust-video'),o=document.getElementById('trust-overlay');if(!v||!o)return;o.width=v.videoWidth||640;o.height=v.videoHeight||640;}
async function _liveLoop(){
  var video=document.getElementById('trust-video');
  if(!video||video.readyState<2||_trustState==='captured')return;
  var w=video.videoWidth,h=video.videoHeight; if(!w||!h)return;
  var canvas=document.getElementById('trust-canvas'),scale=0.25;
  var sw=Math.floor(w*scale),sh=Math.floor(h*scale);
  canvas.width=sw; canvas.height=sh;
  var ctx=canvas.getContext('2d',{willReadFrequently:true});
  ctx.drawImage(video,0,0,sw,sh);
  var px=ctx.getImageData(0,0,sw,sh).data;
  var motion=0;
  if(_prevFrameData&&_prevFrameData.length===px.length){
    for(var i=0;i<px.length;i+=4) motion+=(Math.abs(px[i]-_prevFrameData[i])+Math.abs(px[i+1]-_prevFrameData[i+1])+Math.abs(px[i+2]-_prevFrameData[i+2]))/3;
    motion/=px.length/4;
  }
  _prevFrameData=new Uint8ClampedArray(px); _motionHistory.push(motion);
  if(_motionHistory.length>20) _motionHistory.shift();
  var hasFace=false;
  if(_faceDetector){try{var faces=await _faceDetector.detect(video);hasFace=faces.length>0;}catch(e){}}
  if(!hasFace) hasFace=_skinToneCheck(px,sw,sh);
  _drawOval(hasFace);
  var avgAll=_motionHistory.reduce(function(a,b){return a+b;},0)/(_motionHistory.length||1);
  var recent5=_motionHistory.slice(-5).reduce(function(a,b){return a+b;},0)/5;
  if(_trustState==='detecting'){
    if(hasFace&&avgAll>_MOTION_MICRO) _livenessScore=Math.min(_livenessScore+3,100);
    else if(hasFace) _livenessScore=Math.min(_livenessScore+1,100);
    else _livenessScore=Math.max(_livenessScore-1,0);
    _setStatus(hasFace?'✓ Face detected — hold still…':'🔍 Looking for face…',hasFace);
    _setBarLabel(hasFace?'Analyzing liveness…':'Position your face in the oval');
    _setBar(_livenessScore);
    if(_livenessScore>=_SCORE_THRESH&&hasFace){
      _trustState='challenging';
      var ch=_challenges[Math.floor(Math.random()*_challenges.length)];
      _showChallenge('👉 '+ch); _setStatus('Challenge: '+ch,true);
      _setBarLabel("Perform the action to confirm you're live");
    }
  } else if(_trustState==='challenging'){
    if(recent5>_MOTION_ACTION){
      _trustState='captured'; clearInterval(_trustInterval); clearTimeout(_manualTimer);
      _setBar(100); _setBarLabel('✓ Liveness confirmed!'); _setStatus('✓ Live person confirmed — capturing…',true);
      _hideChallenge(); setTimeout(captureTrustPhoto,700);
    }
  }
}
function _skinToneCheck(px,w,h){var x0=Math.floor(w*0.25),y0=Math.floor(h*0.25),x1=Math.floor(w*0.75),y1=Math.floor(h*0.75),skin=0,total=0;for(var y=y0;y<y1;y++){for(var x=x0;x<x1;x++){var i=(y*w+x)*4,r=px[i],g=px[i+1],b=px[i+2];if(r>60&&g>25&&b>10&&r>b&&r>g*0.75&&r-b>10)skin++;total++;}}return total>0&&skin/total>0.04;}
function _drawOval(hasFace){var ov=document.getElementById('trust-overlay');if(!ov)return;var ctx=ov.getContext('2d'),ow=ov.width,oh=ov.height;ctx.clearRect(0,0,ow,oh);var cx=ow/2,cy=oh/2,rx=ow*0.32,ry=oh*0.42;ctx.save();ctx.fillStyle='rgba(0,0,0,0.38)';ctx.fillRect(0,0,ow,oh);ctx.globalCompositeOperation='destination-out';ctx.beginPath();ctx.ellipse(cx,cy,rx,ry,0,0,Math.PI*2);ctx.fill();ctx.restore();ctx.beginPath();ctx.ellipse(cx,cy,rx,ry,0,0,Math.PI*2);ctx.strokeStyle=hasFace?'#34D399':'rgba(255,255,255,0.55)';ctx.lineWidth=hasFace?3.5:2;ctx.stroke();if(hasFace){var x=cx-rx,y=cy-ry,x2=cx+rx,y2=cy+ry,cs=18;ctx.strokeStyle='#34D399';ctx.lineWidth=3;[[x,y+cs,x,y,x+cs,y],[x2-cs,y,x2,y,x2,y+cs],[x,y2-cs,x,y2,x+cs,y2],[x2-cs,y2,x2,y2,x2,y2-cs]].forEach(function(p){ctx.beginPath();ctx.moveTo(p[0],p[1]);ctx.lineTo(p[2],p[3]);ctx.lineTo(p[4],p[5]);ctx.stroke();});}}
function _setStatus(txt,ok){var el=document.getElementById('trust-status');if(!el)return;el.textContent=txt;el.className='trust-status '+(ok?'trust-status-ok':'trust-status-detecting');}
function _setBar(pct){var el=document.getElementById('trust-live-bar');if(el)el.style.width=Math.min(pct,100)+'%';}
function _setBarLabel(txt){var el=document.getElementById('trust-bar-label');if(el)el.textContent=txt;}
function _showChallenge(txt){var el=document.getElementById('trust-challenge');if(!el)return;el.textContent=txt;el.style.visibility='';el.classList.add('trust-challenge-pulse');}
function _hideChallenge(){var el=document.getElementById('trust-challenge');if(el){el.style.visibility='hidden';el.classList.remove('trust-challenge-pulse');}}
function _resetLivenessUI(){_setStatus('🔍 Position your face in the oval…',false);_setBar(0);_setBarLabel('Liveness scan starting…');_hideChallenge();}
function _showFallbackBtn(){if(_trustState==='captured')return;var ctrl=document.querySelector('.trust-camera-controls');if(!ctrl)return;var btn=document.createElement('button');btn.type='button';btn.className='tp-capture-btn';btn.textContent='📷 Capture Manually';btn.onclick=function(){_trustState='captured';clearInterval(_trustInterval);captureTrustPhoto();};ctrl.prepend(btn);}
function captureTrustPhoto(){
  var video=document.getElementById('trust-video'),canvas=document.getElementById('trust-canvas');
  if(!video||!canvas)return;
  canvas.width=video.videoWidth;canvas.height=video.videoHeight;
  canvas.getContext('2d').drawImage(video,0,0);
  canvas.toBlob(function(blob){
    if(_trustStream){_trustStream.getTracks().forEach(function(t){t.stop();});_trustStream=null;}
    var fd=new FormData(); fd.append('trust_photo',blob,'capture.jpg');
    var m=document.cookie.match(/(?:^|;[ ]*)csrf_token=([^;]*)/);
    var hdrs=m?{'X-CSRF-Token':decodeURIComponent(m[1])}:{};
    fetch('/profile/trust-photo',{method:'POST',headers:hdrs,body:fd})
      .then(function(r){return r.text();})
      .then(function(html){
        var flash=document.getElementById('flash');
        if(flash){flash.innerHTML=html;setTimeout(function(){flash.innerHTML='';},3500);}
        document.getElementById('trust-camera-wrap').style.display='none';
        var ob=document.getElementById('tp-open-btn'); if(ob)ob.style.display='';
        var cd=document.getElementById('trust-photo-card'); if(cd)cd.style.display='';
      }).catch(function(){_showToast('Upload failed — please try again','error');});
  },'image/jpeg',0.92);
}
function cancelTrustCamera(){
  clearInterval(_trustInterval);clearTimeout(_manualTimer);
  if(_trustStream){_trustStream.getTracks().forEach(function(t){t.stop();});_trustStream=null;}
  _trustState='idle';
  document.getElementById('trust-camera-wrap').style.display='none';
  var ob=document.getElementById('tp-open-btn'); if(ob)ob.style.display='';
  var cd=document.getElementById('trust-photo-card'); if(cd)cd.style.display='';
}

/* ── Notifications toggle ── */
function _notifSetUI(state) {
  /* state: 'on' | 'off' | 'blocked' | 'unsupported' */
  var btn = document.getElementById('notif-toggle-btn');
  var lbl = document.getElementById('notif-status-label');
  if (!btn || !lbl) return;
  btn.classList.remove('pf-toggle-on','pf-toggle-blocked');
  if (state === 'on')        { btn.classList.add('pf-toggle-on');      lbl.textContent = 'On — you\'ll get deal alerts'; }
  else if (state==='blocked'){ btn.classList.add('pf-toggle-blocked'); lbl.textContent = 'Blocked in browser settings'; }
  else if (state==='unsupported'){ lbl.textContent='Not supported in this browser'; btn.disabled=true; }
  else                       { lbl.textContent = 'Off — tap to enable'; }
}
(function(){
  if (!('Notification' in window)||!('PushManager' in window)){ _notifSetUI('unsupported'); return; }
  if (Notification.permission==='granted') _notifSetUI('on');
  else if (Notification.permission==='denied') _notifSetUI('blocked');
  else _notifSetUI('off');
})();
async function handleNotifToggle(){
  if (!('Notification' in window)||!('PushManager' in window)) return;
  if (Notification.permission==='denied'){
    _showToast('Notifications are blocked. Go to your browser settings to allow them.','error'); return;
  }
  if (Notification.permission==='granted'){
    await telukaPushUnsubscribe();
    _notifSetUI('off');
    _showToast('Deal alerts turned off.','success');
  } else {
    var perm = await Notification.requestPermission();
    if (perm==='granted'){
      var ok = await telukaPushSubscribe();
      _notifSetUI(ok ? 'on' : 'off');
      _showToast(ok ? 'Deal alerts enabled!' : 'Could not subscribe — try again.', ok ? 'success' : 'error');
    } else if (perm==='denied'){
      _notifSetUI('blocked');
    }
  }
}

/* ── PWA ── */
if('serviceWorker' in navigator) window.addEventListener('load',function(){navigator.serviceWorker.register('/static/sw.js');});
""")

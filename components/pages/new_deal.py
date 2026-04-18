from fasthtml.common import *
from schemas.user import UserProfile, TrustLevel


def new_deal_page(session_user_id: str) -> FT:
    return Html(
        _head(),
        Body(
            Div(cls="app-layout")(
                _sidebar(),
                Div(cls="dash-body")(
                    _app_header(),
                    Main(cls="app-main")(
                        Div(cls="app-content")(
                            Div("New Protected Deal", cls="dash-page-title"),
                            _deal_form(),
                        ),
                    ),
                    _bottom_nav(),
                ),
            ),
            Div(id="flash"),
            _scripts(),
        ),
    )


# ─── Deal form ────────────────────────────────────────────────────────────

def _deal_form() -> FT:
    return Div(cls="deal-form-wrap")(
        # Step indicators
        Div(cls="deal-steps")(
            Div(cls="deal-step active")(Span("1"), "Find Seller"),
            Div(cls="deal-step-divider"),
            Div(cls="deal-step", id="step2-indicator")(Span("2"), "Deal Details"),
            Div(cls="deal-step-divider"),
            Div(cls="deal-step", id="step3-indicator")(Span("3"), "Confirm"),
        ),

        # ── Step 1: Find seller by phone ─────────────────────────────────
        Div(id="step1", cls="deal-step-panel")(
            Div(cls="deal-card")(
                Div(cls="deal-card-title")("🔍 Find Seller"),
                P("Enter the seller's Philippine mobile number.",
                  style="font-size:0.85rem;color:var(--muted);margin-bottom:20px"),
                Form(
                    Div(cls="form-group")(
                        Label("Seller's Mobile Number", cls="form-label"),
                        Div(cls="input-wrap")(
                            Span("+63", cls="input-prefix"),
                            Input(
                                type="tel", name="phone",
                                placeholder="9XX XXX XXXX",
                                maxlength="10", inputmode="numeric",
                                cls="form-input has-prefix",
                                autocomplete="off", required=True,
                            ),
                        ),
                    ),
                    Button(
                        Span("Look Up Seller"),
                        Span(cls="htmx-indicator"),
                        type="submit",
                        cls="btn btn-primary btn-block",
                    ),
                    hx_post="/sellers/lookup",
                    hx_target="#seller-result",
                    hx_swap="innerHTML",
                    hx_indicator="find .htmx-indicator",
                ),
                Div(id="seller-result", style="margin-top:20px"),
            ),
        ),

        # ── Step 2: Deal details (revealed after seller confirmed) ────────
        Div(id="step2", cls="deal-step-panel", style="display:none")(
            Div(cls="deal-card")(
                Div(cls="deal-card-title")("📦 Deal Details"),
                Form(
                    Input(type="hidden", name="seller_id", id="confirmed-seller-id"),
                    Div(cls="form-group")(
                        Label("What are you buying?", cls="form-label"),
                        Input(
                            name="item_description",
                            placeholder="e.g. iPhone 15 Pro Max 256GB Black",
                            cls="form-input", required=True,
                        ),
                        P("Be specific — this description is locked into the escrow contract.",
                          cls="form-hint"),
                    ),
                    Div(cls="form-group")(
                        Label("Agreed Amount (₱)", cls="form-label"),
                        Div(cls="input-wrap")(
                            Span("₱", cls="input-prefix"),
                            Input(
                                name="amount_php", type="number",
                                min="50", step="0.01",
                                placeholder="0.00",
                                cls="form-input has-prefix",
                                required=True,
                            ),
                        ),
                        P("Minimum ₱50. Funds will be held until you confirm delivery.",
                          cls="form-hint"),
                    ),
                    Div(id="deal-summary", style="margin-bottom:20px"),
                    Button(
                        Span("Review & Confirm"),
                        Span(cls="htmx-indicator"),
                        type="submit",
                        cls="btn btn-primary btn-block",
                    ),
                    hx_post="/transactions/create",
                    hx_target="#flash",
                    hx_swap="innerHTML",
                    hx_indicator="find .htmx-indicator",
                ),
            ),
        ),
    )


# ─── Seller result fragments (returned by /sellers/lookup) ─────────────────

def seller_not_found(phone: str) -> FT:
    return Div(cls="seller-not-found")(
        Div("😕", style="font-size:2rem;margin-bottom:8px"),
        Div("Seller not found", style="font-weight:700;color:var(--text);margin-bottom:4px"),
        Div(
            f"No Teluka account found for +63 {phone[-10:]}. "
            "Ask the seller to sign up first.",
            style="font-size:0.82rem;color:var(--muted);line-height:1.5",
        ),
    )


def seller_blocked(phone: str, reason: str) -> FT:
    return Div(cls="seller-blocked")(
        Div("🚫", style="font-size:2rem;margin-bottom:8px"),
        Div("Transaction Blocked", style="font-weight:700;color:#FB7185;margin-bottom:4px"),
        Div(reason, style="font-size:0.82rem;color:var(--muted);line-height:1.5"),
    )


def seller_found_card(seller: UserProfile, risk_flags: list[str]) -> FT:
    pct       = int(seller.trust_score)
    level_cls = {
        TrustLevel.NEW:         "badge-trust-new",
        TrustLevel.LOW:         "badge-trust-low",
        TrustLevel.MEDIUM:      "badge-trust-medium",
        TrustLevel.HIGH:        "badge-trust-high",
        TrustLevel.BLACKLISTED: "badge-trust-blacklisted",
    }.get(seller.trust_level, "badge-trust-new")

    phone = seller.phone
    masked = phone[:3] + "•" * (len(phone) - 7) + phone[-4:] if len(phone) > 7 else phone

    warn_block = Div(cls="risk-warn")(
        Div("⚠️ Warnings", cls="risk-warn-title"),
        *[Div(f"• {f.replace('_', ' ').title()}", cls="risk-warn-item") for f in risk_flags],
    ) if risk_flags else None

    return Div(
        Div(cls="seller-card")(
            Div(cls="seller-card-left")(
                Div(phone[-4:], cls="seller-avatar"),
                Div(
                    Div(masked, cls="seller-phone"),
                    Div(cls="seller-meta")(
                        Span(
                            seller.trust_level.value.title() + " Trust",
                            cls=f"profile-badge {level_cls}",
                        ),
                        Span(
                            "✓ GCash" if seller.gcash_verified else ("✓ Maya" if seller.maya_verified else "Unverified"),
                            cls="profile-badge badge-kyc-unverified" if not (seller.gcash_verified or seller.maya_verified) else "profile-badge badge-kyc-verified",
                        ),
                    ),
                ),
            ),
            Div(cls="seller-card-right")(
                Div(f"{pct}", cls="seller-trust-val"),
                Div("trust", style="font-size:0.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.06em"),
            ),
        ),
        # Trust bar
        Div(cls="trust-bar", style="margin:12px 0 16px")(
            Div(cls="trust-fill", style=f"width:{pct}%"),
        ),
        warn_block,
        # Confirm seller button → reveals step 2
        Button(
            "✓ This is my seller — Continue",
            cls="btn btn-primary btn-block",
            style="margin-top:4px",
            onclick=f"confirmSeller('{seller.id}')",
        ),
    )


# ─── Shared shell (same pattern as dashboard/profile) ─────────────────────

def _sidebar() -> FT:
    return Aside(cls="dash-sidebar")(
        Div("Teluka", cls="sidebar-logo"),
        Nav(cls="sidebar-nav")(
            A(cls="sidebar-item", href="/dashboard")(
                _icon_home(), "Home"
            ),
            A(cls="sidebar-item sidebar-cta active", href="/transactions/new")(
                _icon_plus(), "New Protected Deal"
            ),
            A(cls="sidebar-item", href="/profile")(
                _icon_user(), "Profile"
            ),
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
        Div("New Deal", cls="app-header-logo"),
        Div(cls="app-header-actions")(
            Button(
                _icon_sun(), _icon_moon(),
                cls="icon-btn theme-toggle",
                onclick="toggleTheme()",
            ),
            Form(
                Button(_icon_logout(), cls="icon-btn", title="Sign out"),
                action="/logout", method="post",
            ),
        ),
    )


def _bottom_nav() -> FT:
    def ni(page, href, icon, label):
        cls = "nav-item active" if page == "new" else "nav-item"
        return A(cls=cls, href=href)(icon, Span(label))
    return Nav(cls="bottom-nav")(
        ni("home",    "/dashboard",        _icon_home_nav(), "Home"),
        A(cls="nav-item nav-cta active", href="/transactions/new")(
            _icon_plus_nav(), Span("New"),
        ),
        ni("profile", "/profile",          _icon_user_nav(), "Profile"),
    )


# ─── SVG icons ────────────────────────────────────────────────────────────

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


# ─── Head / scripts ───────────────────────────────────────────────────────

def _head() -> FT:
    return Head(
        Meta(charset="UTF-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Meta(name="theme-color", content="#0D9488"),
        Title("New Deal — Teluka"),
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
  h.setAttribute('data-theme', n);
  localStorage.setItem('teluka-theme', n);
}

function confirmSeller(sellerId) {
  // Populate hidden seller_id field and reveal step 2
  document.getElementById('confirmed-seller-id').value = sellerId;
  document.getElementById('step1').style.display = 'none';
  document.getElementById('step2').style.display = '';
  document.getElementById('step2-indicator').classList.add('active');
  document.querySelector('.app-main').scrollTo({top: 0, behavior: 'smooth'});
  window.scrollTo({top: 0, behavior: 'smooth'});
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

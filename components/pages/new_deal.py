from fasthtml.common import *
from schemas.user import UserProfile, TrustLevel
from core.tiers import PLANS


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
                            _deal_form(),
                        ),
                    ),
                    _bottom_nav(),
                ),
            ),
            Div(id="flash", style="position:fixed;bottom:80px;left:0;right:0;z-index:900;padding:0 16px;"),
            _scripts(),
        ),
    )


# ─── Deal form ─────────────────────────────────────────────────────────────────

def _deal_form() -> FT:
    return Div(cls="nd-wrap")(

        # Page title row
        Div(cls="nd-title-row")(
            Div(cls="nd-title")("New Protected Deal"),
            Div(cls="nd-title-sub")("Buyer initiates · funds held until confirmed"),
        ),

        # Progress bar — updated by JS when steps change
        Div(cls="nd-progress")(
            Div(cls="nd-progress-header")(
                Span("🔍", id="nd-step-icon", cls="nd-prog-icon"),
                Span("Step 1 of 3", id="nd-step-count", cls="nd-prog-step"),
                Span(" — Find Seller", id="nd-step-label", cls="nd-prog-label"),
            ),
            Div(cls="nd-progress-track")(
                Div(cls="nd-progress-fill", id="nd-progress-fill", style="width:33%"),
            ),
        ),

        # ── Step 1: Find seller ───────────────────────────────────────────────
        Div(id="step1", cls="nd-panel")(
            Div(cls="nd-card")(
                Div(cls="nd-card-icon")("🔍"),
                Div(cls="nd-card-title")("Find Seller"),
                P("Enter the seller's PH mobile number to look them up.",
                  cls="nd-card-sub"),
                Form(
                    Div(cls="nd-phone-wrap")(
                        Span("+63", cls="nd-prefix"),
                        Input(
                            type="tel", name="phone",
                            placeholder="9XX XXX XXXX",
                            maxlength="10", inputmode="numeric",
                            cls="form-input nd-phone-input",
                            autocomplete="off", required=True,
                        ),
                    ),
                    Button(
                        Span("Look Up"),
                        Span(cls="htmx-indicator"),
                        type="submit",
                        cls="btn btn-primary btn-block nd-lookup-btn",
                    ),
                    hx_post="/sellers/lookup",
                    hx_target="#seller-result",
                    hx_swap="innerHTML",
                    hx_indicator="find .htmx-indicator",
                    style="margin-top:16px;",
                ),
                Div(id="seller-result", style="margin-top:16px"),
            ),
        ),

        # ── Step 2: Deal details ──────────────────────────────────────────────
        Div(id="step2", cls="nd-panel", style="display:none")(
            # Back link
            Button(
                NotStr('<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>'),
                " Back to seller lookup",
                cls="nd-back-btn", type="button",
                onclick="showStep('step1')",
            ),
            Input(type="hidden", id="confirmed-seller-id"),
            Div(cls="nd-card")(
                Div(cls="nd-card-icon")("📦"),
                Div(cls="nd-card-title")("Deal Details"),
                P("Describe exactly what you're buying and the agreed price.",
                  cls="nd-card-sub"),

                Div(cls="form-group")(
                    Label("Item description", cls="form-label"),
                    Input(
                        name="item_description", id="item-desc-input",
                        placeholder="e.g. iPhone 15 Pro Max 256GB Black",
                        cls="form-input", required=True,
                        oninput="updateChecklist()",
                    ),
                    P("Be specific — this locks in exactly what you're buying.", cls="form-hint"),
                ),

                Div(cls="form-group")(
                    Label("Agreed amount (₱)", cls="form-label"),
                    Div(cls="nd-amount-wrap")(
                        Span("₱", cls="nd-prefix nd-amount-prefix"),
                        Input(
                            name="amount_php", type="number",
                            min="50", step="0.01", placeholder="0.00",
                            id="amount-input",
                            cls="form-input nd-amount-input",
                            required=True,
                            oninput="onAmountChange(this.value); updateChecklist()",
                        ),
                    ),
                    Div(cls="nd-amount-preview hidden", id="amount-preview")(
                        Span("Deal amount:", cls="nd-preview-label"),
                        Span("₱0", cls="nd-preview-val", id="amount-preview-val"),
                    ),
                ),

                # Protection checklist
                Div(cls="nd-checklist")(
                    Div(cls="nd-checklist-title")("✓ Your money is protected when:"),
                    Div(cls="nd-check-row", id="chk-desc")(
                        Div(cls="nd-check-dot"), Span("Item description is filled in"),
                    ),
                    Div(cls="nd-check-row", id="chk-amount")(
                        Div(cls="nd-check-dot"), Span("Amount is ₱50 or more"),
                    ),
                    Div(cls="nd-check-row nd-check-done")(
                        Div(cls="nd-check-dot"), Span("Seller is confirmed on Teluka"),
                    ),
                ),

                Button(
                    "Next: Choose Protection",
                    NotStr('<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>'),
                    type="button", id="to-step3-btn",
                    cls="btn btn-primary btn-block",
                    style="margin-top:20px;gap:6px;",
                    onclick="goToStep3()",
                ),
            ),
        ),

        # ── Step 3: Protection plan picker ────────────────────────────────────
        Div(id="step3", cls="nd-panel", style="display:none")(
            Button(
                NotStr('<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>'),
                " Back to deal details",
                cls="nd-back-btn", type="button",
                onclick="showStep('step2')",
            ),
            Div(cls="nd-card")(
                Div(cls="nd-card-icon")("🛡️"),
                Div(cls="nd-card-title")("Choose Protection"),
                P("Select the security level for this deal. Higher value = stronger plan.",
                  cls="nd-card-sub"),

                Div(cls="nd-plan-grid", id="plan-grid")(
                    *[_plan_card(p) for p in PLANS.values()]
                ),

                # Fee summary
                Div(cls="nd-summary hidden", id="plan-summary")(
                    Div(cls="nd-summary-row")(
                        Span("Item price", cls="nd-summary-label"),
                        Span(id="summary-item", cls="nd-summary-val"),
                    ),
                    Div(cls="nd-summary-row")(
                        Span("Teluka service fee", cls="nd-summary-label"),
                        Span(id="summary-fee", cls="nd-summary-val nd-summary-fee"),
                    ),
                    Div(cls="nd-summary-row nd-summary-total")(
                        Span("Total you pay", cls="nd-summary-label"),
                        Span(id="summary-total", cls="nd-summary-val"),
                    ),
                ),

                Form(
                    Input(type="hidden", name="seller_id",        id="form-seller-id"),
                    Input(type="hidden", name="item_description", id="form-item-desc"),
                    Input(type="hidden", name="amount_php",       id="form-amount"),
                    Input(type="hidden", name="protection_plan",  id="form-plan", value="basic"),
                    Button(
                        NotStr('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'),
                        Span("Protect This Deal"),
                        Span(cls="htmx-indicator"),
                        type="submit", id="submit-deal-btn",
                        cls="btn btn-primary btn-block",
                        style="margin-top:16px;gap:8px;",
                        disabled=True,
                    ),
                    hx_post="/transactions/create",
                    hx_target="#flash",
                    hx_swap="innerHTML",
                    hx_indicator="find .htmx-indicator",
                ),
            ),
        ),
    )


def _plan_card(plan) -> FT:
    fee_text = (
        f"₱{plan.flat_fee_centavos // 100} flat"
        if plan.fee_type == "flat"
        else f"{int(plan.percent_fee * 100)}% of deal"
    )
    perks_html = [
        Div(cls="nd-perk")(Span("✓", cls="nd-perk-check"), Span(p))
        for p in plan.perks
    ]
    return Div(
        cls="nd-plan-card",
        id=f"plan-{plan.id}",
        onclick=f"selectPlan('{plan.id}')",
        **{
            "data-plan":     plan.id,
            "data-flat":     str(plan.flat_fee_centavos),
            "data-pct":      str(plan.percent_fee),
            "data-fee-type": plan.fee_type,
            "data-min-fee":  str(plan.min_fee_centavos),
        },
    )(
        # Header row — always visible
        Div(cls="nd-plan-header")(
            Div(cls="nd-plan-radio", id=f"radio-{plan.id}"),
            Span(plan.icon, cls="nd-plan-icon"),
            Div(cls="nd-plan-info")(
                Span(plan.name, cls="nd-plan-name"),
                Span(plan.tagline, cls="nd-plan-tagline"),
            ),
            Div(fee_text, cls="nd-plan-fee"),
        ),
        # Perks — slide open when selected
        Div(cls="nd-plan-perks", id=f"perks-{plan.id}")(*perks_html),
    )


# ─── Seller result fragments ───────────────────────────────────────────────────

def seller_not_found(phone: str) -> FT:
    return Div(cls="nd-seller-msg nd-seller-notfound")(
        Span("😕", cls="nd-seller-msg-icon"),
        Div(cls="nd-seller-msg-body")(
            Div("Seller not found", cls="nd-seller-msg-title"),
            Div(
                f"No Teluka account for +63 {phone[-10:]}. Ask them to sign up first.",
                cls="nd-seller-msg-sub",
            ),
        ),
    )


def seller_blocked(phone: str, reason: str) -> FT:
    return Div(cls="nd-seller-msg nd-seller-blocked")(
        Span("🚫", cls="nd-seller-msg-icon"),
        Div(cls="nd-seller-msg-body")(
            Div("Transaction Blocked", cls="nd-seller-msg-title"),
            Div(reason, cls="nd-seller-msg-sub"),
        ),
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

    phone  = seller.phone
    masked = phone[:3] + "•" * (len(phone) - 7) + phone[-4:] if len(phone) > 7 else phone

    warn_block = Div(cls="nd-risk-warn")(
        Div("⚠️ Warnings", cls="nd-risk-title"),
        *[Div(f"· {f.replace('_', ' ').title()}", cls="nd-risk-item") for f in risk_flags],
    ) if risk_flags else None

    return Div(cls="nd-seller-found")(
        Div(cls="nd-seller-row")(
            Div(phone[-4:], cls="nd-seller-avatar"),
            Div(cls="nd-seller-info")(
                Div(masked, cls="nd-seller-phone"),
                Div(cls="nd-seller-badges")(
                    Span(seller.trust_level.value.title() + " Trust", cls=f"profile-badge {level_cls}"),
                    Span(
                        "✓ GCash" if seller.gcash_verified else ("✓ Maya" if seller.maya_verified else "Unverified"),
                        cls="profile-badge badge-kyc-verified" if (seller.gcash_verified or seller.maya_verified) else "profile-badge badge-kyc-unverified",
                    ),
                ),
            ),
            Div(cls="nd-trust-score")(
                Div(f"{pct}", cls="nd-trust-num"),
                Div("trust", cls="nd-trust-label"),
            ),
        ),
        Div(cls="nd-trust-bar")(
            Div(cls="nd-trust-fill", style=f"width:{pct}%"),
        ),
        warn_block,
        Button(
            NotStr('<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'),
            " This is my seller — Continue",
            cls="btn btn-primary btn-block",
            style="margin-top:12px;gap:6px;",
            onclick=f"confirmSeller('{seller.id}')",
        ),
    )


# ─── Shared shell ──────────────────────────────────────────────────────────────

def _sidebar() -> FT:
    return Aside(cls="dash-sidebar")(
        Div("Teluka", cls="sidebar-logo"),
        Nav(cls="sidebar-nav")(
            A(cls="sidebar-item", href="/dashboard")(_icon_home(), "Home"),
            A(cls="sidebar-item sidebar-cta active", href="/transactions/new")(_icon_plus(), "New Protected Deal"),
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


def _app_header() -> FT:
    return Header(cls="app-header")(
        Div("New Deal", cls="app-header-logo"),
        Div(cls="app-header-actions")(
            Button(_icon_sun(), _icon_moon(), cls="icon-btn theme-toggle", onclick="toggleTheme()"),
            Form(Button(_icon_logout(), cls="icon-btn", title="Sign out"), action="/logout", method="post"),
        ),
    )


def _bottom_nav() -> FT:
    def ni(page, href, icon, label):
        return A(cls="nav-item active" if page == "new" else "nav-item", href=href)(icon, Span(label))
    return Nav(cls="bottom-nav")(
        ni("home",    "/dashboard", _icon_home_nav(), "Home"),
        A(cls="nav-item nav-cta active", href="/transactions/new")(_icon_plus_nav(), Span("New")),
        ni("profile", "/profile",   _icon_user_nav(), "Profile"),
    )


# ─── SVG icons ─────────────────────────────────────────────────────────────────

def _icon_home():
    return Svg(NotStr('<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>'),
        xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round")

def _icon_plus():
    return Svg(NotStr('<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>'),
        xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2.5", stroke_linecap="round")

def _icon_user():
    return Svg(NotStr('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'),
        xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round")

def _icon_logout():
    return Svg(NotStr('<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>'),
        xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round")

def _icon_sun():
    return Svg(NotStr('<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>'),
        xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round", cls="icon-sun")

def _icon_moon():
    return Svg(NotStr('<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>'),
        xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round", cls="icon-moon")

def _icon_home_nav():
    return Svg(NotStr('<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>'),
        xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round")

def _icon_plus_nav():
    return Svg(NotStr('<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>'),
        xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2.5", stroke_linecap="round")

def _icon_user_nav():
    return Svg(NotStr('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'),
        xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round")


# ─── Head / scripts ────────────────────────────────────────────────────────────

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

/* ── Progress bar update ── */
var _STEP_DATA = {
  step1: { icon:'🔍', count:'Step 1 of 3', label:' — Find Seller',    pct:'33%'  },
  step2: { icon:'📦', count:'Step 2 of 3', label:' — Deal Details',   pct:'67%'  },
  step3: { icon:'🛡️', count:'Step 3 of 3', label:' — Choose Plan',    pct:'100%' },
};

function _updateProgress(stepId) {
  var d = _STEP_DATA[stepId];
  if (!d) return;
  var icon  = document.getElementById('nd-step-icon');
  var count = document.getElementById('nd-step-count');
  var label = document.getElementById('nd-step-label');
  var fill  = document.getElementById('nd-progress-fill');
  if (icon)  icon.textContent  = d.icon;
  if (count) count.textContent = d.count;
  if (label) label.textContent = d.label;
  if (fill)  fill.style.width  = d.pct;
}

function showStep(id) {
  ['step1','step2','step3'].forEach(function(s) {
    var el = document.getElementById(s);
    if (!el) return;
    el.style.display = s === id ? '' : 'none';
    if (s === id) {
      el.classList.remove('nd-panel'); void el.offsetWidth; el.classList.add('nd-panel');
    }
  });
  _updateProgress(id);
  window.scrollTo({ top: 0, behavior: 'smooth' });
  var main = document.querySelector('.app-main');
  if (main) main.scrollTo({ top: 0, behavior: 'smooth' });
}

/* ── Amount preview ── */
function onAmountChange(val) {
  var preview    = document.getElementById('amount-preview');
  var previewVal = document.getElementById('amount-preview-val');
  var num = parseFloat(val);
  if (!preview || !previewVal) return;
  if (isNaN(num) || num <= 0) { preview.classList.add('hidden'); return; }
  preview.classList.remove('hidden');
  previewVal.textContent = '₱' + num.toLocaleString('en-PH', {minimumFractionDigits:2, maximumFractionDigits:2});
  previewVal.classList.remove('pop'); void previewVal.offsetWidth; previewVal.classList.add('pop');
  // Pre-highlight recommended plan
  var cents = num * 100;
  var rec = cents >= 500000 ? 'premium' : (cents >= 100000 ? 'standard' : 'basic');
  document.querySelectorAll('.nd-plan-card').forEach(function(c) {
    c.classList.toggle('nd-plan-recommended', c.dataset.plan === rec);
  });
}

/* ── Security checklist ── */
function updateChecklist() {
  var desc   = document.getElementById('item-desc-input');
  var amount = document.getElementById('amount-input');
  var chkDesc   = document.getElementById('chk-desc');
  var chkAmount = document.getElementById('chk-amount');
  if (chkDesc)   chkDesc.classList.toggle('nd-check-done',   desc   && desc.value.trim().length > 2);
  if (chkAmount) chkAmount.classList.toggle('nd-check-done', amount && parseFloat(amount.value) >= 50);
}

function confirmSeller(sellerId) {
  document.getElementById('confirmed-seller-id').value = sellerId;
  showStep('step2');
}

function goToStep3() {
  var desc   = document.getElementById('item-desc-input').value.trim();
  var amount = parseFloat(document.getElementById('amount-input').value);
  if (!desc || desc.length < 2) { _toast('Please enter an item description.', 'error'); return; }
  if (isNaN(amount) || amount < 50) { _toast('Please enter an amount of at least ₱50.', 'error'); return; }
  document.getElementById('form-seller-id').value  = document.getElementById('confirmed-seller-id').value;
  document.getElementById('form-item-desc').value  = desc;
  document.getElementById('form-amount').value      = amount;
  showStep('step3');
  onAmountChange(amount);
}

/* ── Plan selection ── */
var _selectedPlan = null;
function selectPlan(planId) {
  _selectedPlan = planId;
  document.querySelectorAll('.nd-plan-card').forEach(function(c) {
    var sel = c.dataset.plan === planId;
    c.classList.toggle('nd-plan-selected', sel);
    var perks = document.getElementById('perks-' + c.dataset.plan);
    var radio = document.getElementById('radio-' + c.dataset.plan);
    if (perks) perks.classList.toggle('nd-plan-perks-open', sel);
    if (radio) radio.classList.toggle('nd-radio-checked', sel);
  });
  document.getElementById('form-plan').value = planId;

  var amount  = parseFloat(document.getElementById('form-amount').value) * 100;
  var card    = document.querySelector('[data-plan="' + planId + '"]');
  var feeType = card.dataset.feeType;
  var fee = 0;
  if (feeType === 'flat') {
    fee = parseInt(card.dataset.flat);
  } else if (feeType === 'percent') {
    fee = Math.max(parseInt(card.dataset.minFee), Math.round(amount * parseFloat(card.dataset.pct)));
  }
  var fmt = function(c) {
    return '₱' + (c/100).toLocaleString('en-PH', {minimumFractionDigits:2, maximumFractionDigits:2});
  };
  document.getElementById('summary-item').textContent  = fmt(amount);
  document.getElementById('summary-fee').textContent   = fmt(fee);
  document.getElementById('summary-total').textContent = fmt(amount + fee);

  var s = document.getElementById('plan-summary');
  s.classList.remove('hidden');
  document.getElementById('submit-deal-btn').disabled = false;
}

/* ── Toast helper ── */
function _toast(msg, type) {
  var f = document.getElementById('flash');
  if (!f) return;
  var cls = type === 'error' ? 'toast toast-error' : 'toast toast-success';
  f.innerHTML = '<div class="' + cls + '">' + msg + '</div>';
  setTimeout(function(){ f.innerHTML = ''; }, 3500);
}

/* ── Scroll-hide header / nav ── */
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

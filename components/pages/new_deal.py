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
            Div(cls="deal-step active", id="step1-indicator")(Span("1"), "Find Seller"),
            Div(cls="deal-step-divider"),
            Div(cls="deal-step", id="step2-indicator")(Span("2"), "Deal Details"),
            Div(cls="deal-step-divider"),
            Div(cls="deal-step", id="step3-indicator")(Span("3"), "Choose Plan"),
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

        # ── Step 2: Deal details ──────────────────────────────────────────
        Div(id="step2", cls="deal-step-panel", style="display:none")(
            Div(cls="deal-card")(
                Div(cls="deal-card-title")("📦 Deal Details"),
                Div(
                    Input(type="hidden", name="seller_id", id="confirmed-seller-id"),
                    Div(cls="form-group")(
                        Label("What are you buying?", cls="form-label"),
                        Input(
                            name="item_description",
                            id="item-desc-input",
                            placeholder="e.g. iPhone 15 Pro Max 256GB Black",
                            cls="form-input", required=True,
                            oninput="updateChecklist()",
                        ),
                        P("Be specific — this locks in exactly what you're buying.",
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
                                id="amount-input",
                                cls="form-input has-prefix",
                                required=True,
                                oninput="onAmountChange(this.value); updateChecklist()",
                            ),
                        ),
                        P("Minimum ₱50. Held safely until you confirm the item.", cls="form-hint"),
                        Div(cls="amount-preview hidden", id="amount-preview")(
                            Div(cls="amount-preview-label")("Deal amount"),
                            Div(cls="amount-preview-val", id="amount-preview-val")("₱0"),
                        ),
                    ),
                    Div(cls="security-checklist")(
                        Div("Your money is protected when:", cls="security-checklist-title"),
                        Div(cls="check-item", id="chk-desc")(
                            Div("✓", cls="check-dot"), Span("Item description is filled in"),
                        ),
                        Div(cls="check-item", id="chk-amount")(
                            Div("✓", cls="check-dot"), Span("Amount is ₱50 or more"),
                        ),
                        Div(cls="check-item done")(
                            Div("✓", cls="check-dot"), Span("Seller is confirmed"),
                        ),
                    ),
                    Button(
                        "Next: Choose Protection →",
                        type="button",
                        cls="btn btn-primary btn-block",
                        style="margin-top:16px",
                        id="to-step3-btn",
                        onclick="goToStep3()",
                    ),
                ),
            ),
        ),

        # ── Step 3: Protection plan picker ────────────────────────────────
        Div(id="step3", cls="deal-step-panel", style="display:none")(
            Div(cls="deal-card")(
                Div(cls="deal-card-title")("🛡️ Choose Your Protection Plan"),
                P("Pick the level of security for this deal. You can always upgrade.",
                  style="font-size:0.85rem;color:var(--muted);margin-bottom:20px"),

                # Plan cards
                Div(cls="plan-grid", id="plan-grid")(
                    *[_plan_card(p) for p in PLANS.values()]
                ),

                # Fee summary
                Div(cls="plan-summary hidden", id="plan-summary")(
                    Div(cls="plan-summary-row")(
                        Span("Item amount", cls="plan-summary-label"),
                        Span(id="summary-item", cls="plan-summary-val"),
                    ),
                    Div(cls="plan-summary-row")(
                        Span("Teluka service fee", cls="plan-summary-label"),
                        Span(id="summary-fee", cls="plan-summary-val plan-summary-fee"),
                    ),
                    Div(cls="plan-summary-row plan-summary-total")(
                        Span("Total you pay", cls="plan-summary-label"),
                        Span(id="summary-total", cls="plan-summary-val"),
                    ),
                ),

                # Hidden inputs submitted with the form
                Form(
                    Input(type="hidden", name="seller_id",        id="form-seller-id"),
                    Input(type="hidden", name="item_description", id="form-item-desc"),
                    Input(type="hidden", name="amount_php",       id="form-amount"),
                    Input(type="hidden", name="protection_plan",  id="form-plan", value="basic"),
                    Button(
                        Span("Protect This Deal"),
                        Span(cls="htmx-indicator"),
                        type="submit",
                        id="submit-deal-btn",
                        cls="btn btn-primary btn-block",
                        style="margin-top:20px",
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
    perks_html = [
        Div(cls="plan-perk")(Span("✓", cls="plan-perk-check"), Span(p))
        for p in plan.perks
    ]
    fee_text = (
        f"\u20b1{plan.flat_fee_centavos // 100} flat"
        if plan.fee_type == "flat"
        else f"{int(plan.percent_fee * 100)}% of deal"
    )
    fee_badge = Div(fee_text, cls="plan-fee-badge plan-fee-paid")
    return Div(
        cls="plan-card",
        id=f"plan-{plan.id}",
        onclick=f"selectPlan('{plan.id}')",
        **{"data-plan": plan.id,
           "data-flat": str(plan.flat_fee_centavos),
           "data-pct": str(plan.percent_fee),
           "data-fee-type": plan.fee_type,
           "data-min-fee": str(plan.min_fee_centavos)},
    )(
        Div(cls="plan-card-header")(
            Div(cls="plan-icon")(plan.icon),
            Div(cls="plan-name")(plan.name),
            fee_badge,
        ),
        Div(cls="plan-tagline")(plan.tagline),
        Div(cls="plan-perks")(*perks_html),
        Div(cls="plan-select-indicator")("✓ Selected"),
    )


# ─── Seller result fragments ───────────────────────────────────────────────

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

    phone  = seller.phone
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
                        Span(seller.trust_level.value.title() + " Trust", cls=f"profile-badge {level_cls}"),
                        Span(
                            "✓ GCash" if seller.gcash_verified else ("✓ Maya" if seller.maya_verified else "Unverified"),
                            cls="profile-badge badge-kyc-verified" if (seller.gcash_verified or seller.maya_verified) else "profile-badge badge-kyc-unverified",
                        ),
                    ),
                ),
            ),
            Div(cls="seller-card-right")(
                Div(f"{pct}", cls="seller-trust-val"),
                Div("trust", style="font-size:0.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.06em"),
            ),
        ),
        Div(cls="trust-bar", style="margin:12px 0 16px")(
            Div(cls="trust-fill", style=f"width:{pct}%"),
        ),
        warn_block,
        Button(
            "✓ This is my seller — Continue",
            cls="btn btn-primary btn-block",
            style="margin-top:4px",
            onclick=f"confirmSeller('{seller.id}')",
        ),
    )


# ─── Shared shell ─────────────────────────────────────────────────────────

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


# ─── SVG icons ────────────────────────────────────────────────────────────

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

/* ── Live amount preview ── */
function updateAmountPreview(val) {
  var preview = document.getElementById('amount-preview');
  var previewVal = document.getElementById('amount-preview-val');
  var num = parseFloat(val);
  if (!preview || !previewVal) return;
  if (isNaN(num) || num <= 0) { preview.classList.add('hidden'); return; }
  preview.classList.remove('hidden');
  previewVal.textContent = '₱' + num.toLocaleString('en-PH', {minimumFractionDigits:2,maximumFractionDigits:2});
  previewVal.classList.remove('pop');
  void previewVal.offsetWidth;
  previewVal.classList.add('pop');
  setTimeout(function() { previewVal.classList.remove('pop'); }, 200);
}

function onAmountChange(val) {
  updateAmountPreview(val);
  // Pre-highlight recommended plan in step 3
  var num = parseFloat(val) * 100;
  if (isNaN(num)) return;
  var recommended = num >= 500000 ? 'premium' : (num >= 100000 ? 'standard' : 'basic');
  document.querySelectorAll('.plan-card').forEach(function(c) {
    c.classList.toggle('plan-recommended', c.dataset.plan === recommended);
  });
}

/* ── Security checklist ── */
function updateChecklist() {
  var desc   = document.getElementById('item-desc-input');
  var amount = document.getElementById('amount-input');
  var chkDesc   = document.getElementById('chk-desc');
  var chkAmount = document.getElementById('chk-amount');
  if (chkDesc)   chkDesc.classList.toggle('done',   desc   && desc.value.trim().length > 3);
  if (chkAmount) chkAmount.classList.toggle('done', amount && parseFloat(amount.value) >= 50);
}

function confirmSeller(sellerId) {
  document.getElementById('confirmed-seller-id').value = sellerId;
  showStep('step2');
  document.getElementById('step2-indicator').classList.add('active');
}

function goToStep3() {
  var desc   = document.getElementById('item-desc-input').value.trim();
  var amount = parseFloat(document.getElementById('amount-input').value);
  if (!desc || desc.length < 2) { alert('Please enter an item description.'); return; }
  if (isNaN(amount) || amount < 50) { alert('Please enter an amount of at least ₱50.'); return; }

  // Copy values to the hidden form inputs in step 3
  document.getElementById('form-seller-id').value  = document.getElementById('confirmed-seller-id').value;
  document.getElementById('form-item-desc').value  = desc;
  document.getElementById('form-amount').value     = amount;

  showStep('step3');
  document.getElementById('step3-indicator').classList.add('active');

  // Trigger recommended plan highlight
  onAmountChange(amount);
}

function showStep(id) {
  ['step1','step2','step3'].forEach(function(s) {
    var el = document.getElementById(s);
    if (el) el.style.display = s === id ? '' : 'none';
    // Re-trigger slide animation
    if (s === id && el) {
      el.classList.remove('deal-step-panel');
      void el.offsetWidth;
      el.classList.add('deal-step-panel');
    }
  });
  document.querySelector('.app-main').scrollTo({top:0,behavior:'smooth'});
  window.scrollTo({top:0,behavior:'smooth'});
}

/* ── Plan selection ── */
var _selectedPlan = null;

function selectPlan(planId) {
  _selectedPlan = planId;
  document.querySelectorAll('.plan-card').forEach(function(c) {
    c.classList.toggle('plan-selected', c.dataset.plan === planId);
  });
  document.getElementById('form-plan').value = planId;

  var amount = parseFloat(document.getElementById('form-amount').value) * 100;
  var card   = document.querySelector('[data-plan="' + planId + '"]');
  var feeType = card.dataset.feeType;
  var fee = 0;
  if (feeType === 'flat') {
    fee = parseInt(card.dataset.flat);
  } else if (feeType === 'percent') {
    fee = Math.max(parseInt(card.dataset.minFee), Math.round(amount * parseFloat(card.dataset.pct)));
  }

  var fmt = function(c) { return '₱' + (c/100).toLocaleString('en-PH',{minimumFractionDigits:2,maximumFractionDigits:2}); };
  document.getElementById('summary-item').textContent  = fmt(amount);
  document.getElementById('summary-fee').textContent   = fmt(fee);
  document.getElementById('summary-total').textContent = fmt(amount + fee);

  var summary = document.getElementById('plan-summary');
  summary.classList.remove('hidden');
  summary.classList.add('plan-summary-enter');
  setTimeout(function() { summary.classList.remove('plan-summary-enter'); }, 400);

  document.getElementById('submit-deal-btn').disabled = false;
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

from fasthtml.common import *


# ─── SVG icons ────────────────────────────────────────────────────────────────

def _ico_phone() -> FT:
    return Svg(NotStr('<path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1-9.4 0-17-7.6-17-17 0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1L6.6 10.8z"/>'), xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="currentColor", width="16", height="16")

def _ico_email() -> FT:
    return Svg(NotStr('<path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>'), xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="currentColor", width="16", height="16")

def _ico_check() -> FT:
    return Svg(NotStr('<polyline points="20 6 9 17 4 12"/>'), xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2.5", stroke_linecap="round", stroke_linejoin="round", width="15", height="15")

def _ico_lock() -> FT:
    return Svg(NotStr('<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>'), xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round", width="16", height="16")

def _ico_shield() -> FT:
    return Svg(NotStr('<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'), xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round", width="13", height="13")


# ─── Step chrome helpers ─────────────────────────────────────────────────────

_HIDE_CHROME = """
(function(){
  ['auth-headline','auth-tabs-row'].forEach(function(id){
    var el = document.getElementById(id);
    if (!el) return;
    el.style.maxHeight = el.scrollHeight + 'px';
    el.offsetHeight;
    el.style.maxHeight = '0';
    el.style.opacity = '0';
    el.style.marginBottom = '0';
    el.style.pointerEvents = 'none';
  });
})();
"""

_SHOW_CHROME = """
(function(){
  ['auth-headline','auth-tabs-row'].forEach(function(id){
    var el = document.getElementById(id);
    if (!el) return;
    el.style.maxHeight = '220px';
    el.style.opacity = '1';
    el.style.marginBottom = '';
    el.style.pointerEvents = '';
  });
})();
"""


# ─── Page shell ───────────────────────────────────────────────────────────────

def login_page(error: str | None = None) -> FT:
    return Html(
        _head(),
        Body(
            _page_loader(),
            _bg_blobs(),
            Div(cls="auth-page")(
                Div(cls="auth-card")(

                    # Top row: back button + brand
                    Div(cls="auth-toprow")(
                        A(cls="auth-back-btn", href="/")(
                            NotStr('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>'),
                            Span("Back"),
                        ),
                        Div(cls="auth-brand")(
                            Div(cls="auth-logo-mark")("T"),
                            Div(
                                A("Teluka", href="/", cls="auth-logo"),
                                Div("PH Escrow", cls="auth-logo-tag"),
                            ),
                        ),
                    ),

                    Div(id="auth-headline")(
                        H1("Welcome back", cls="auth-title"),
                        P("Secure escrow for Philippines marketplace deals.", cls="auth-sub"),
                    ),

                    # Sign In / Sign Up tabs
                    Div(cls="auth-tabs", id="auth-tabs-row")(
                        Div(cls="auth-tab-slider", id="tab-slider"),
                        Button("Sign In", cls="auth-tab active", id="tab-signin",
                               onclick="switchTab('signin')", type="button"),
                        Button("Sign Up", cls="auth-tab", id="tab-signup",
                               onclick="switchTab('signup')", type="button"),
                    ),

                    # Form panes
                    Div(id="auth-step")(
                        Div(id="pane-signin")(_signin_form(error=error)),
                        Div(id="pane-signup", style="display:none")(_signup_form()),
                    ),

                    Div(id="flash"),

                    # Trust badges
                    _trust_badges(),
                ),
            ),
            # Portal outside backdrop-filter context so position:fixed overlays center on viewport
            Div(id="vso-portal"),
            Script(_TAB_SCRIPT),
            _pwa_script(),
        ),
    )


def _progress_bar(step: int) -> FT:
    labels  = {1: "Enter your details", 2: "Verify your email", 3: "Set your PIN"}
    pct     = {1: 33, 2: 67, 3: 100}
    icons   = {1: "👤", 2: "✉️", 3: "🔐"}
    return Div(cls="auth-progress")(
        Div(cls="auth-progress-header")(
            Span(icons[step], cls="auth-prog-icon"),
            Span(f"Step {step} of 3", cls="auth-prog-step"),
            Span(f" — {labels[step]}", cls="auth-prog-label"),
        ),
        Div(cls="auth-progress-track")(
            Div(cls="auth-progress-fill", style=f"width:{pct[step]}%"),
        ),
    )


def _trust_badges() -> FT:
    return Div(
        style=(
            "display:flex;gap:16px;justify-content:center;flex-wrap:wrap;"
            "margin-top:24px;padding-top:20px;border-top:1px solid var(--border);"
        )
    )(
        *[
            Div(
                style="display:flex;align-items:center;gap:5px;font-size:0.72rem;color:var(--muted);font-weight:600;"
            )(Span(icon, style="color:var(--jade-light)"), Span(text))
            for icon, text in [("🔒", "End-to-end encrypted"), ("🇵🇭", "PH-native"), ("✓", "No passwords")]
        ]
    )


# ─── Sign In form ─────────────────────────────────────────────────────────────

def _signin_form(error: str | None = None) -> FT:
    return Form(
        # Phone / Email inner toggle
        Div(cls="input-mode-toggle")(
            Div(cls="imt-slider", id="imt-slider"),
            Button(
                _ico_phone(), Span("Phone"),
                cls="imt-btn active", id="imt-phone",
                onclick="switchInput('phone')", type="button",
            ),
            Button(
                _ico_email(), Span("Email"),
                cls="imt-btn", id="imt-email",
                onclick="switchInput('email')", type="button",
            ),
        ),

        # Phone input (shown by default)
        Div(cls="form-group", id="input-phone-wrap")(
            Label("Mobile Number", cls="form-label"),
            Div(cls="input-icon-wrap", id="signin-phone-wrap")(
                Div(cls="input-icon")(_ico_phone()),
                Input(
                    type="tel",
                    name="identifier",
                    id="signin-phone",
                    placeholder="09171234567",
                    cls="form-input",
                    autocomplete="tel",
                    inputmode="numeric",
                    oninput="validateIdentifier(this,'signin-phone-wrap')",
                ),
                Div(cls="input-valid-icon")(_ico_check()),
            ),
            P("New to Teluka? We'll ask you to sign up.", cls="form-hint"),
        ),

        # Email input (hidden by default)
        Div(cls="form-group", id="input-email-wrap", style="display:none")(
            Label("Email Address", cls="form-label"),
            Div(cls="input-icon-wrap", id="signin-email-wrap")(
                Div(cls="input-icon")(_ico_email()),
                Input(
                    type="email",
                    name="identifier",
                    id="signin-email",
                    placeholder="you@gmail.com",
                    cls="form-input",
                    autocomplete="email",
                    oninput="validateIdentifier(this,'signin-email-wrap')",
                ),
                Div(cls="input-valid-icon")(_ico_check()),
            ),
            P("OTP will be sent to this email.", cls="form-hint"),
        ),

        Div(
            Div(error, cls="toast toast-error") if error else None,
            style="margin-bottom:16px" if error else "",
        ),
        Button(
            Span("Continue"),
            Span(cls="htmx-indicator"),
            type="submit",
            cls="btn btn-primary btn-block",
            style="gap:8px;",
        ),
        hx_post="/check-identifier",
        hx_target="#auth-step",
        hx_swap="innerHTML",
        hx_indicator="find .htmx-indicator",
    )


def identifier_form_fragment(error: str | None = None) -> FT:
    return Div(
        Div(id="pane-signin")(_signin_form(error=error)),
        Div(id="pane-signup", style="display:none")(_signup_form()),
        Script(_SHOW_CHROME),
        Script(_TAB_SCRIPT),
    )


# ─── Sign Up form ─────────────────────────────────────────────────────────────

def _signup_form(phone: str = "", email: str = "", error: str | None = None) -> FT:
    local = phone[3:] if phone.startswith("+63") else phone
    return Form(
        Div(cls="form-group")(
            Label("Mobile Number", cls="form-label"),
            Div(cls="input-wrap input-icon-wrap", id="signup-phone-wrap")(
                Span("+63", cls="input-prefix", style="left:14px;"),
                Input(
                    type="tel",
                    name="phone",
                    placeholder="917 123 4567",
                    maxlength="12",
                    inputmode="numeric",
                    cls="form-input has-prefix",
                    autocomplete="tel",
                    required=True,
                    value=local,
                    oninput="validatePhone(this,'signup-phone-wrap')",
                    style="padding-left:58px;",
                ),
                Div(cls="input-valid-icon")(_ico_check()),
            ),
            P("Your permanent identity on Teluka. Cannot be changed.", cls="form-hint"),
        ),
        Div(cls="form-group")(
            Label("Email Address", cls="form-label"),
            Div(cls="input-icon-wrap", id="signup-email-wrap")(
                Div(cls="input-icon")(_ico_email()),
                Input(
                    type="email",
                    name="email",
                    placeholder="you@gmail.com",
                    cls="form-input",
                    autocomplete="email",
                    required=True,
                    value=email,
                    oninput="validateEmail(this,'signup-email-wrap')",
                ),
                Div(cls="input-valid-icon")(_ico_check()),
            ),
            P("OTP codes are always sent here.", cls="form-hint"),
        ),
        # Honeypot — bots fill this, humans don't see it
        Input(
            type="text",
            name="email_confirm",
            tabindex="-1",
            autocomplete="off",
            style="position:absolute;left:-9999px;width:1px;height:1px;opacity:0;",
            aria_hidden="true",
        ),
        Div(
            Div(error, cls="toast toast-error") if error else None,
            style="margin-bottom:16px" if error else "",
        ),
        Button(
            _ico_shield(),
            Span("Create Account"),
            Span(cls="htmx-indicator"),
            type="submit",
            cls="btn btn-primary btn-block",
            style="gap:8px;",
        ),
        hx_post="/register",
        hx_target="#auth-step",
        hx_swap="innerHTML",
        hx_indicator="find .htmx-indicator",
    )


def signup_form_fragment(phone: str = "", email: str = "", error: str | None = None) -> FT:
    """HTMX fragment — shown when a new phone number is detected."""
    return Div(
        Div(id="pane-signin", style="display:none")(_signin_form()),
        Div(id="pane-signup")(_signup_form(phone=phone, email=email, error=error)),
        Script(_SHOW_CHROME),
        Script("""
(function(){
  var btnIn  = document.getElementById('tab-signin');
  var btnUp  = document.getElementById('tab-signup');
  var slider = document.getElementById('tab-slider');
  if (btnIn)  btnIn.className  = 'auth-tab';
  if (btnUp)  btnUp.className  = 'auth-tab active';
  if (slider) slider.className = 'auth-tab-slider right';
})();
        """),
        Script(_TAB_SCRIPT),
    )


# ─── OTP step ─────────────────────────────────────────────────────────────────

def otp_step(masked_email: str, email: str, error: str | None = None, _phone: str = "") -> FT:
    return Div(
        cls="otp-step-wrap",
        style="animation:auth-enter 0.4s cubic-bezier(0.16,1,0.3,1) both;",
    )(
        _progress_bar(2),

        # Hero email icon
        Div(cls="otp-hero")(
            Div(cls="otp-hero-icon-wrap")(
                Div(cls="otp-hero-pulse"),
                Div(cls="otp-hero-pulse otp-hero-pulse-2"),
                Div(cls="otp-hero-icon")("✉️"),
            ),
            H2("Check your email", cls="otp-hero-title"),
            P(
                Span("Code sent to ", style="color:var(--muted);"),
                Span(masked_email, style="color:var(--jade-light);font-weight:800;"),
                cls="otp-hero-sub",
            ),
            P("Check inbox and spam · expires in 10 min", cls="otp-hero-hint"),
        ),

        Div(Div(error, cls="toast toast-error"), style="margin-bottom:16px") if error else None,

        Form(
            id="otp-form",
            hx_post="/verify-otp",
            hx_target="#auth-step",
            hx_swap="innerHTML",
            hx_indicator="find .htmx-indicator",
        )(
            Input(type="hidden", name="email", value=email),
            Input(type="hidden", name="phone", value=_phone) if _phone else None,
            Input(type="hidden", name="otp",   id="otp-hidden"),

            Div(cls="form-group")(
                Label("Enter the 6-digit code", cls="form-label",
                      style="text-align:center;display:block;margin-bottom:12px;"),
                Div(cls="otp-wrap", id="otp-boxes")(
                    *[
                        Input(
                            type="tel",
                            maxlength="1",
                            cls="otp-input",
                            id=f"otp-{i}",
                            name=f"otp-{i}",
                            inputmode="numeric",
                            autocomplete="one-time-code" if i == 0 else "off",
                            pattern="[0-9]",
                        )
                        for i in range(6)
                    ]
                ),
            ),

            Button(
                _ico_lock(),
                Span("Verify & Continue"),
                Span(cls="htmx-indicator"),
                type="submit",
                id="otp-submit",
                cls="btn btn-primary btn-block",
                style="margin-top:4px;gap:8px;",
                disabled=True,
            ),
        ),

        Div(cls="otp-actions")(
            Button(
                Span(id="resend-label")("Resend code"),
                cls="btn btn-ghost btn-sm",
                id="resend-btn",
                type="button",
                disabled=True,
                hx_post="/resend-otp",
                hx_vals=f'{{"email":"{email}"}}',
                hx_target="#flash",
                hx_swap="innerHTML",
                onclick="startResendCooldown()",
            ),
            Span(cls="otp-actions-sep")("·"),
            Button(
                "← Back",
                cls="btn btn-ghost btn-sm",
                type="button",
                hx_get="/login/identifier-form",
                hx_target="#auth-step",
                hx_swap="innerHTML",
            ),
        ),

        Script(_HIDE_CHROME),
        Script(_OTP_SCRIPT),
    )


# ─── JavaScript ───────────────────────────────────────────────────────────────

_TAB_SCRIPT = """
/* ── Sign In / Sign Up main tabs ── */
function switchTab(tab) {
  var signin = document.getElementById('pane-signin');
  var signup = document.getElementById('pane-signup');
  var btnIn  = document.getElementById('tab-signin');
  var btnUp  = document.getElementById('tab-signup');
  var slider = document.getElementById('tab-slider');
  if (!signin) return;
  if (tab === 'signin') {
    signin.style.display = ''; signup.style.display = 'none';
    btnIn.className = 'auth-tab active'; btnUp.className = 'auth-tab';
    if (slider) slider.className = 'auth-tab-slider';
  } else {
    signin.style.display = 'none'; signup.style.display = '';
    btnIn.className = 'auth-tab'; btnUp.className = 'auth-tab active';
    if (slider) slider.className = 'auth-tab-slider right';
  }
}

/* ── Phone / Email inner toggle ── */
function switchInput(mode) {
  var phoneWrap = document.getElementById('input-phone-wrap');
  var emailWrap = document.getElementById('input-email-wrap');
  var btnPhone  = document.getElementById('imt-phone');
  var btnEmail  = document.getElementById('imt-email');
  var slider    = document.getElementById('imt-slider');
  if (mode === 'phone') {
    if (phoneWrap) phoneWrap.style.display = '';
    if (emailWrap) emailWrap.style.display = 'none';
    if (btnPhone) btnPhone.className = 'imt-btn active';
    if (btnEmail) btnEmail.className = 'imt-btn';
    if (slider)   slider.className   = 'imt-slider';
    var inp = document.getElementById('signin-phone');
    if (inp) inp.focus();
  } else {
    if (phoneWrap) phoneWrap.style.display = 'none';
    if (emailWrap) emailWrap.style.display = '';
    if (btnPhone) btnPhone.className = 'imt-btn';
    if (btnEmail) btnEmail.className = 'imt-btn active';
    if (slider)   slider.className   = 'imt-slider right';
    var inp = document.getElementById('signin-email');
    if (inp) inp.focus();
  }
}

function validateIdentifier(inp, wrapId) {
  var val  = inp.value.trim();
  var wrap = document.getElementById(wrapId);
  if (!wrap) return;
  var isPhone = /^[0-9\\s\\-\\+]+$/.test(val) && val.replace(/\\D/g,'').length >= 9;
  var isEmail = /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(val);
  wrap.classList.toggle('is-valid', isPhone || isEmail);
}

function validatePhone(inp, wrapId) {
  var digits = inp.value.replace(/\\D/g,'');
  var wrap = document.getElementById(wrapId);
  if (wrap) wrap.classList.toggle('is-valid', digits.length >= 9);
}

function validateEmail(inp, wrapId) {
  var wrap = document.getElementById(wrapId);
  var ok = /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(inp.value.trim());
  if (wrap) wrap.classList.toggle('is-valid', ok);
}
"""

_OTP_SCRIPT = """
(function () {
  var inputs  = document.querySelectorAll('.otp-input');
  var hidden  = document.getElementById('otp-hidden');
  var submit  = document.getElementById('otp-submit');
  var form    = document.getElementById('otp-form');
  var RESEND_COOLDOWN = 60;

  function syncHidden() {
    hidden.value = Array.from(inputs).map(function(i){ return i.value; }).join('');
    var ready = hidden.value.length === 6;
    submit.disabled = !ready;
    if (ready) { form.dispatchEvent(new Event('submit', {bubbles:true, cancelable:true})); }
  }

  inputs.forEach(function(inp, idx) {
    inp.addEventListener('input', function() {
      inp.value = inp.value.replace(/\\D/g, '').slice(-1);
      if (inp.value) {
        inp.classList.add('filled');
        inp.classList.remove('pop');
        void inp.offsetWidth;
        inp.classList.add('pop');
      } else {
        inp.classList.remove('filled');
      }
      syncHidden();
      if (inp.value && idx < inputs.length - 1) inputs[idx + 1].focus();
    });
    inp.addEventListener('keydown', function(e) {
      if (e.key === 'Backspace' && !inp.value && idx > 0) {
        inputs[idx - 1].classList.remove('filled');
        inputs[idx - 1].focus();
      }
    });
    inp.addEventListener('paste', function(e) {
      e.preventDefault();
      var raw    = (e.clipboardData || window.clipboardData).getData('text');
      var digits = raw.replace(/\\D/g, '').slice(0, 6);
      digits.split('').forEach(function(d, i){
        if (inputs[i]) {
          inputs[i].value = d;
          inputs[i].classList.add('filled');
        }
      });
      syncHidden();
      var next = Math.min(digits.length, inputs.length - 1);
      if (inputs[next]) inputs[next].focus();
    });
  });

  if (inputs[0]) inputs[0].focus();

  var resendBtn   = document.getElementById('resend-btn');
  var resendLabel = document.getElementById('resend-label');

  function startResendCooldown() {
    if (!resendBtn) return;
    resendBtn.disabled = true;
    var remaining = RESEND_COOLDOWN;
    resendLabel.textContent = 'Resend in ' + remaining + 's';
    var timer = setInterval(function() {
      remaining--;
      if (remaining <= 0) {
        clearInterval(timer);
        resendBtn.disabled = false;
        resendLabel.textContent = 'Resend code';
      } else {
        resendLabel.textContent = 'Resend in ' + remaining + 's';
      }
    }, 1000);
  }

  window.startResendCooldown = startResendCooldown;
  startResendCooldown();
})();
"""


# ─── PIN creation step ────────────────────────────────────────────────────────

def pin_step(phone: str, email: str, error: str | None = None) -> FT:
    return Div(
        style="animation:auth-enter 0.4s cubic-bezier(0.16,1,0.3,1) both;",
    )(
        _progress_bar(3),

        # Header
        Div(cls="otp-hero")(
            Div(cls="otp-hero-icon-wrap")(
                Div(cls="otp-hero-pulse"),
                Div(cls="otp-hero-icon")("🔐"),
            ),
            H2("Set your PIN", cls="otp-hero-title"),
            P("Used to confirm critical actions like releasing payment.",
              cls="otp-hero-sub", style="color:var(--muted);"),
        ),

        Div(Div(error, cls="toast toast-error"), style="margin-bottom:16px") if error else None,

        Form(
            id="pin-form",
            hx_post="/set-pin",
            hx_target="#flash",
            hx_swap="innerHTML",
            hx_indicator="find .htmx-indicator",
        )(
            Input(type="hidden", name="phone", value=phone),
            Input(type="hidden", name="email", value=email),
            Input(type="hidden", name="pin",   id="pin-hidden"),
            Input(type="hidden", name="pin_confirm", id="pin-confirm-hidden"),

            # PIN entry
            Div(cls="form-group")(
                Label("Choose a 4-Digit PIN", cls="form-label",
                      style="text-align:center;display:block;"),
                Div(cls="otp-wrap", id="pin-boxes")(
                    *[
                        Input(
                            type="tel", maxlength="1",
                            cls="otp-input pin-input",
                            id=f"pin-{i}",
                            inputmode="numeric",
                            pattern="[0-9]",
                        )
                        for i in range(4)
                    ]
                ),
            ),

            # Confirm PIN
            Div(cls="form-group")(
                Label("Confirm PIN", cls="form-label",
                      style="text-align:center;display:block;"),
                Div(cls="otp-wrap", id="pin-confirm-boxes")(
                    *[
                        Input(
                            type="tel", maxlength="1",
                            cls="otp-input pin-confirm-input",
                            id=f"pinc-{i}",
                            inputmode="numeric",
                            pattern="[0-9]",
                        )
                        for i in range(4)
                    ]
                ),
                P(id="pin-match-hint", cls="form-hint",
                  style="text-align:center;min-height:1.2em;"),
            ),

            Button(
                _ico_lock(),
                Span("Create Account & Set PIN"),
                Span(cls="htmx-indicator"),
                type="submit",
                id="pin-submit",
                cls="btn btn-primary btn-block",
                style="margin-top:8px;gap:8px;",
                disabled=True,
            ),
        ),

        Script(_HIDE_CHROME),
        Script(_PIN_SCRIPT),
    )


_PIN_SCRIPT = """
(function () {
  var pinInputs  = document.querySelectorAll('.pin-input');
  var confInputs = document.querySelectorAll('.pin-confirm-input');
  var pinHidden  = document.getElementById('pin-hidden');
  var confHidden = document.getElementById('pin-confirm-hidden');
  var submit     = document.getElementById('pin-submit');
  var hint       = document.getElementById('pin-match-hint');

  function fillBoxes(inputs, hiddenEl) {
    inputs.forEach(function(inp, idx) {
      inp.addEventListener('input', function() {
        inp.value = inp.value.replace(/\\D/g,'').slice(-1);
        if (inp.value) {
          inp.classList.add('filled');
          inp.classList.remove('pop'); void inp.offsetWidth; inp.classList.add('pop');
        } else {
          inp.classList.remove('filled');
        }
        hiddenEl.value = Array.from(inputs).map(function(i){ return i.value; }).join('');
        if (inp.value && idx < inputs.length - 1) inputs[idx + 1].focus();
        checkMatch();
      });
      inp.addEventListener('keydown', function(e) {
        if (e.key === 'Backspace' && !inp.value && idx > 0) {
          inputs[idx - 1].classList.remove('filled');
          inputs[idx - 1].focus();
        }
      });
    });
  }

  function checkMatch() {
    var p = pinHidden.value;
    var c = confHidden.value;
    if (p.length < 4 || c.length < 4) {
      hint.textContent = '';
      hint.style.color = '';
      submit.disabled = true;
      return;
    }
    if (p === c) {
      hint.textContent = '✓ PINs match';
      hint.style.color = 'var(--jade-light)';
      submit.disabled = false;
    } else {
      hint.textContent = '✗ PINs do not match';
      hint.style.color = 'var(--danger)';
      submit.disabled = true;
    }
  }

  fillBoxes(pinInputs, pinHidden);
  fillBoxes(confInputs, confHidden);

  if (pinInputs[0]) pinInputs[0].focus();
})();
"""


# ─── Page shell helpers ───────────────────────────────────────────────────────

def _head() -> FT:
    return Head(
        Meta(charset="UTF-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Meta(name="theme-color", content="#0D9488"),
        Meta(name="apple-mobile-web-app-capable", content="yes"),
        Title("Sign In — Teluka"),
        Link(rel="manifest",         href="/static/manifest.json"),
        Link(rel="apple-touch-icon", href="/static/icons/icon-192.png"),
        Link(rel="preconnect",       href="https://fonts.googleapis.com"),
        Link(rel="preconnect",       href="https://fonts.gstatic.com", crossorigin=""),
        Link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap",
            rel="stylesheet",
        ),
        Link(rel="stylesheet", href="/static/css/app.css"),
        Style("""
          #auth-headline, #auth-tabs-row {
            overflow: hidden;
            transition: max-height 0.35s cubic-bezier(0.4,0,0.2,1),
                        opacity 0.25s ease,
                        margin-bottom 0.3s ease;
          }
          #auth-step {
            transition: opacity 0.18s ease;
          }
          #auth-step.htmx-swapping {
            opacity: 0;
          }
        """),
        Script(src="https://unpkg.com/htmx.org@1.9.12"),
        Script(src="/static/js/app.js"),
        Script(
            "(function(){var t=localStorage.getItem('teluka-theme')||"
            "(window.matchMedia('(prefers-color-scheme:light)').matches?'light':'dark');"
            "document.documentElement.setAttribute('data-theme',t);})();"
        ),
    )


def _bg_blobs() -> FT:
    return Div(
        style="position:fixed;inset:0;z-index:-1;overflow:hidden;pointer-events:none;"
    )(
        Div(style=(
            "position:absolute;width:700px;height:700px;border-radius:50%;"
            "background:radial-gradient(circle,rgba(13,148,136,0.12) 0%,transparent 70%);"
            "top:-250px;left:-150px;animation:float1 8s ease-in-out infinite;"
        )),
        Div(style=(
            "position:absolute;width:500px;height:500px;border-radius:50%;"
            "background:radial-gradient(circle,rgba(64,224,255,0.08) 0%,transparent 70%);"
            "bottom:-150px;right:-80px;animation:float2 10s ease-in-out infinite;"
        )),
        Div(style=(
            "position:absolute;width:300px;height:300px;border-radius:50%;"
            "background:radial-gradient(circle,rgba(139,92,246,0.06) 0%,transparent 70%);"
            "top:50%;left:60%;animation:float1 12s ease-in-out infinite reverse;"
        )),
        Style("""
          @keyframes float1 {
            0%,100% { transform: translate(0,0); }
            50%      { transform: translate(20px,-30px); }
          }
          @keyframes float2 {
            0%,100% { transform: translate(0,0); }
            50%      { transform: translate(-15px,20px); }
          }
        """),
    )


def _page_loader() -> FT:
    return Div(id="page-loader")(
        Div(cls="loader-glow"),
        Div(cls="loader-glow-2"),
        Div(cls="loader-logo-wrap")(
            Div(cls="loader-spin-ring"),
            Div(cls="loader-logo")("T"),
        ),
        Div(cls="loader-brand-text")("Teluka"),
        Div(cls="loader-dots")(
            Div(cls="loader-dot"),
            Div(cls="loader-dot"),
            Div(cls="loader-dot"),
        ),
        Div(cls="loader-bar-track")(
            Div(cls="loader-bar-fill"),
        ),
        Script("""
(function(){
  function hide(){
    var l=document.getElementById('page-loader');
    if(l){l.classList.add('hidden');setTimeout(function(){l.remove();},520);}
  }
  if(document.readyState==='complete'){hide();}
  else{window.addEventListener('load',hide);}
})();
        """),
    )


def _pwa_script() -> FT:
    return Script("""
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/static/sw.js');
  });
}

/* Cursor-following glow on the auth card (desktop only) */
(function(){
  if (!window.matchMedia('(hover: hover)').matches) return;
  function attach() {
    var card = document.querySelector('.auth-card');
    if (!card) return;
    card.addEventListener('mousemove', function(e) {
      var r = card.getBoundingClientRect();
      var x = ((e.clientX - r.left) / r.width  * 100).toFixed(1) + '%';
      var y = ((e.clientY - r.top)  / r.height * 100).toFixed(1) + '%';
      card.style.setProperty('--mx', x);
      card.style.setProperty('--my', y);
    });
    card.addEventListener('mouseleave', function() {
      card.style.setProperty('--mx', '50%');
      card.style.setProperty('--my', '50%');
    });
  }
  attach();
  document.body.addEventListener('htmx:afterSwap', attach);
})();
""")

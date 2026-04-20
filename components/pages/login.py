from fasthtml.common import *


# ─── Icons ────────────────────────────────────────────────────────────────────

def _ico_phone() -> FT:
    return Svg(NotStr('<path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1-9.4 0-17-7.6-17-17 0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1L6.6 10.8z"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="currentColor", width="16", height="16")

def _ico_email() -> FT:
    return Svg(NotStr('<path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="currentColor", width="16", height="16")

def _ico_check() -> FT:
    return Svg(NotStr('<polyline points="20 6 9 17 4 12"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none",
               stroke="currentColor", stroke_width="2.5", stroke_linecap="round",
               stroke_linejoin="round", width="15", height="15")

def _ico_lock() -> FT:
    return Svg(NotStr('<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none",
               stroke="currentColor", stroke_width="2", stroke_linecap="round",
               stroke_linejoin="round", width="16", height="16")

def _ico_shield() -> FT:
    return Svg(NotStr('<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'),
               xmlns="http://www.w3.org/2000/svg", viewBox="0 0 24 24", fill="none",
               stroke="currentColor", stroke_width="2", stroke_linecap="round",
               stroke_linejoin="round", width="13", height="13")


# ─── Progress bar ─────────────────────────────────────────────────────────────

def _progress_bar(step: int) -> FT:
    steps = [
        ("Your details",  "👤"),
        ("Verify email",  "✉️"),
        ("Set your PIN",  "🔐"),
    ]
    return Div(cls="wz-progress")(
        # Step dots
        Div(cls="wz-dots")(
            *[
                Div(
                    cls="wz-dot " + (
                        "wz-dot-done"    if i + 1 < step else
                        "wz-dot-active"  if i + 1 == step else
                        "wz-dot-future"
                    ),
                )(
                    NotStr("✓") if i + 1 < step else Span(str(i + 1))
                )
                for i in range(3)
            ]
        ),
        # Label for current step
        Div(cls="wz-step-label")(
            Span(f"Step {step} of 3", cls="wz-step-num"),
            Span(" — ", cls="wz-sep"),
            Span(steps[step - 1][0], cls="wz-step-name"),
        ),
        # Progress bar
        Div(cls="auth-progress-track")(
            Div(cls="auth-progress-fill", style=f"width:{int(step / 3 * 100)}%"),
        ),
    )


# ─── Page shell ───────────────────────────────────────────────────────────────

def login_page(error: str | None = None) -> FT:
    return Html(
        _head(),
        Body(
            _page_loader(),
            _bg_blobs(),
            Div(cls="auth-page")(
                Div(cls="auth-card")(
                    _auth_toprow(),
                    Div(id="auth-step")(
                        _step1_form(error=error),
                    ),
                    Div(id="flash"),
                    _trust_badges(),
                ),
            ),
            Div(id="vso-portal"),
            _pwa_script(),
        ),
    )


# ─── Step 1 — Phone number ────────────────────────────────────────────────────

def _step1_form(error: str | None = None) -> FT:
    return Div(
        cls="wz-step",
        style="animation:auth-enter 0.4s cubic-bezier(0.16,1,0.3,1) both;",
    )(
        _progress_bar(1),

        Div(cls="wz-step-header")(
            Div(cls="wz-hero-icon")("👤"),
            H1("Enter your phone", cls="auth-title"),
            P("Already a member? We'll sign you in. New? We'll set you up.",
              cls="auth-sub"),
        ),

        # Phone form
        Div(id="phone-form-wrap")(
            Form(
                hx_post="/check-identifier",
                hx_target="#auth-step",
                hx_swap="innerHTML",
                hx_indicator="find .htmx-indicator",
            )(
                Div(cls="form-group")(
                    Label("Mobile Number", cls="form-label"),
                    Div(cls="input-icon-wrap", id="ph-wrap")(
                        Span("+63", cls="input-prefix"),
                        Input(
                            type="tel",
                            name="identifier",
                            id="ph-input",
                            placeholder="917 123 4567",
                            cls="form-input has-prefix",
                            autocomplete="tel",
                            inputmode="numeric",
                            autofocus=True,
                            oninput="validatePhone(this,'ph-wrap')",
                        ),
                        Div(cls="input-valid-icon")(_ico_check()),
                    ),
                ),
                Div(Div(error, cls="toast toast-error"), style="margin-bottom:12px") if error else None,
                Button(
                    Span("Continue"),
                    Span(cls="htmx-indicator"),
                    type="submit",
                    cls="btn btn-primary btn-block",
                ),
            ),
            Div(cls="wz-alt-row")(
                Span("Prefer email?", cls="wz-alt-text"),
                Button("Sign in with email →", cls="wz-alt-link",
                       type="button", onclick="showEmailForm()"),
            ),
        ),

        # Email form (hidden, swaps in)
        Div(id="email-form-wrap", style="display:none")(
            Form(
                hx_post="/check-identifier",
                hx_target="#auth-step",
                hx_swap="innerHTML",
                hx_indicator="find .htmx-indicator",
            )(
                Div(cls="form-group")(
                    Label("Email Address", cls="form-label"),
                    Div(cls="input-icon-wrap", id="em-wrap")(
                        Div(cls="input-icon")(_ico_email()),
                        Input(
                            type="email",
                            name="identifier",
                            id="em-input",
                            placeholder="you@gmail.com",
                            cls="form-input",
                            autocomplete="email",
                            oninput="validateEmail(this,'em-wrap')",
                        ),
                        Div(cls="input-valid-icon")(_ico_check()),
                    ),
                    P("OTP will be sent to this address.", cls="form-hint"),
                ),
                Button(
                    Span("Continue"),
                    Span(cls="htmx-indicator"),
                    type="submit",
                    cls="btn btn-primary btn-block",
                ),
            ),
            Button("← Use phone instead", cls="wz-back-link",
                   type="button", onclick="showPhoneForm()"),
        ),

        Script("""
function showEmailForm() {
  document.getElementById('phone-form-wrap').style.display = 'none';
  document.getElementById('email-form-wrap').style.display = '';
  var el = document.getElementById('em-input');
  if (el) el.focus();
}
function showPhoneForm() {
  document.getElementById('email-form-wrap').style.display = 'none';
  document.getElementById('phone-form-wrap').style.display = '';
  var el = document.getElementById('ph-input');
  if (el) el.focus();
}
function validatePhone(inp, wrapId) {
  var digits = inp.value.replace(/\\D/g, '');
  var wrap = document.getElementById(wrapId);
  if (wrap) wrap.classList.toggle('is-valid', digits.length >= 9);
}
function validateEmail(inp, wrapId) {
  var wrap = document.getElementById(wrapId);
  var ok = /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(inp.value.trim());
  if (wrap) wrap.classList.toggle('is-valid', ok);
}
        """),
    )


def identifier_form_fragment(error: str | None = None) -> FT:
    """Returned by the ← Back button from the OTP step."""
    return Div(
        _step1_form(error=error),
    )


# ─── Step 1b — Email collection (new user detected) ──────────────────────────

def _signup_form(phone: str = "", email: str = "", error: str | None = None) -> FT:
    local = phone[3:] if phone.startswith("+63") else phone
    return Div(
        cls="wz-step",
        style="animation:auth-enter 0.4s cubic-bezier(0.16,1,0.3,1) both;",
    )(
        _progress_bar(1),

        Div(cls="wz-step-header")(
            Div(cls="wz-hero-icon")("✉️"),
            H1("One more thing", cls="auth-title"),
            P("New to Teluka! Enter your email — we'll send your verification code there.",
              cls="auth-sub"),
        ),

        # Confirmed phone chip
        Div(cls="wz-confirmed-chip")(
            Span("📱", cls="wz-chip-icon"),
            Span(f"+63 {local}", cls="wz-chip-val"),
            Span("confirmed", cls="wz-chip-badge"),
        ),

        Form(
            hx_post="/register",
            hx_target="#auth-step",
            hx_swap="innerHTML",
            hx_indicator="find .htmx-indicator",
        )(
            Input(type="hidden", name="phone", value=phone),
            # Honeypot
            Input(
                type="text", name="email_confirm", tabindex="-1",
                autocomplete="off",
                style="position:absolute;left:-9999px;width:1px;height:1px;opacity:0;",
                aria_hidden="true",
            ),
            Div(cls="form-group")(
                Label("Email Address", cls="form-label"),
                Div(cls="input-icon-wrap", id="su-email-wrap")(
                    Div(cls="input-icon")(_ico_email()),
                    Input(
                        type="email", name="email", id="su-email-input",
                        placeholder="you@gmail.com",
                        cls="form-input",
                        autocomplete="email",
                        required=True,
                        value=email,
                        autofocus=True,
                        oninput="validateEmailField(this,'su-email-wrap')",
                    ),
                    Div(cls="input-valid-icon")(_ico_check()),
                ),
                P("OTP codes are always sent here. We never share your email.", cls="form-hint"),
            ),
            Div(Div(error, cls="toast toast-error"), style="margin-bottom:12px") if error else None,
            Button(
                _ico_shield(),
                Span("Send Verification Code"),
                Span(cls="htmx-indicator"),
                type="submit",
                cls="btn btn-primary btn-block",
                style="gap:8px;",
            ),
        ),

        Div(cls="wz-nav-row")(
            Button(
                "← Change phone",
                cls="wz-back-link",
                type="button",
                hx_get="/login/identifier-form",
                hx_target="#auth-step",
                hx_swap="innerHTML",
            ),
        ),

        Script("""
function validateEmailField(inp, wrapId) {
  var wrap = document.getElementById(wrapId);
  var ok = /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(inp.value.trim());
  if (wrap) wrap.classList.toggle('is-valid', ok);
}
var su = document.getElementById('su-email-input');
if (su) su.focus();
        """),
    )


def signup_form_fragment(phone: str = "", email: str = "", error: str | None = None) -> FT:
    return Div(_signup_form(phone=phone, email=email, error=error))


# ─── Step 2 — OTP verification ────────────────────────────────────────────────

def otp_step(masked_email: str, email: str, error: str | None = None, _phone: str = "") -> FT:
    return Div(
        cls="wz-step",
        style="animation:auth-enter 0.4s cubic-bezier(0.16,1,0.3,1) both;",
    )(
        _progress_bar(2),

        Div(cls="wz-step-header")(
            Div(cls="wz-hero-icon-wrap")(
                Div(cls="otp-hero-pulse"),
                Div(cls="otp-hero-pulse otp-hero-pulse-2"),
                Div(cls="wz-hero-icon", style="position:relative;z-index:1")("✉️"),
            ),
            H1("Check your email", cls="auth-title"),
            P(
                Span("Code sent to ", style="color:var(--muted)"),
                Span(masked_email, style="color:var(--jade-light);font-weight:800;"),
                cls="auth-sub",
                style="margin-bottom:4px",
            ),
            P("Check inbox and spam · expires in 10 min", cls="auth-sub",
              style="font-size:0.78rem;margin-bottom:20px"),
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
                Label("6-digit code", cls="form-label",
                      style="text-align:center;display:block;margin-bottom:14px;"),
                Div(cls="otp-wrap", id="otp-boxes")(
                    *[
                        Input(
                            type="tel", maxlength="1",
                            cls="otp-input",
                            id=f"otp-{i}", name=f"otp-{i}",
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

        Div(cls="wz-nav-row")(
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
            Span("·", cls="wz-nav-sep"),
            Button(
                "← Back",
                cls="btn btn-ghost btn-sm",
                type="button",
                hx_get="/login/identifier-form",
                hx_target="#auth-step",
                hx_swap="innerHTML",
            ),
        ),

        Script(_OTP_SCRIPT),
    )


# ─── Step 3 — PIN creation ────────────────────────────────────────────────────

def pin_step(phone: str, email: str, error: str | None = None) -> FT:
    return Div(
        cls="wz-step",
        style="animation:auth-enter 0.4s cubic-bezier(0.16,1,0.3,1) both;",
    )(
        _progress_bar(3),

        Div(cls="wz-step-header")(
            Div(cls="wz-hero-icon")("🔐"),
            H1("Set your PIN", cls="auth-title"),
            P("Used to confirm critical actions like releasing payment. Keep it secret.",
              cls="auth-sub"),
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
            Input(type="hidden", name="pin",         id="pin-hidden"),
            Input(type="hidden", name="pin_confirm",  id="pin-confirm-hidden"),

            Div(cls="form-group")(
                Label("Choose a 4-digit PIN", cls="form-label",
                      style="text-align:center;display:block;"),
                Div(cls="otp-wrap", id="pin-boxes")(
                    *[
                        Input(
                            type="tel", maxlength="1",
                            cls="otp-input pin-input",
                            id=f"pin-{i}",
                            inputmode="numeric", pattern="[0-9]",
                        )
                        for i in range(4)
                    ]
                ),
            ),

            Div(cls="form-group")(
                Label("Confirm PIN", cls="form-label",
                      style="text-align:center;display:block;"),
                Div(cls="otp-wrap", id="pin-confirm-boxes")(
                    *[
                        Input(
                            type="tel", maxlength="1",
                            cls="otp-input pin-confirm-input",
                            id=f"pinc-{i}",
                            inputmode="numeric", pattern="[0-9]",
                        )
                        for i in range(4)
                    ]
                ),
                P(id="pin-match-hint", cls="form-hint",
                  style="text-align:center;min-height:1.2em;"),
            ),

            Button(
                _ico_lock(),
                Span("Create Account"),
                Span(cls="htmx-indicator"),
                type="submit",
                id="pin-submit",
                cls="btn btn-primary btn-block",
                style="margin-top:8px;gap:8px;",
                disabled=True,
            ),
        ),

        Script(_PIN_SCRIPT),
    )


# ─── Trust badges ─────────────────────────────────────────────────────────────

def _trust_badges() -> FT:
    return Div(cls="wz-trust-strip")(
        *[
            Div(cls="wz-trust-item")(Span(icon, cls="wz-trust-icon"), Span(text))
            for icon, text in [
                ("🔒", "End-to-end encrypted"),
                ("🇵🇭", "PH-native"),
                ("✓",  "No passwords"),
            ]
        ]
    )


# ─── Shell helpers ─────────────────────────────────────────────────────────────

def _auth_toprow() -> FT:
    return Div(cls="auth-toprow")(
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
    )


# ─── JavaScript ───────────────────────────────────────────────────────────────

_OTP_SCRIPT = """
(function () {
  var inputs  = document.querySelectorAll('.otp-input');
  var hidden  = document.getElementById('otp-hidden');
  var submit  = document.getElementById('otp-submit');
  var form    = document.getElementById('otp-form');

  function syncHidden() {
    hidden.value = Array.from(inputs).map(function(i){ return i.value; }).join('');
    var ready = hidden.value.length === 6;
    submit.disabled = !ready;
    if (ready) form.dispatchEvent(new Event('submit', {bubbles:true, cancelable:true}));
  }

  inputs.forEach(function(inp, idx) {
    inp.addEventListener('input', function() {
      inp.value = inp.value.replace(/\\D/g, '').slice(-1);
      if (inp.value) { inp.classList.add('filled'); inp.classList.remove('pop'); void inp.offsetWidth; inp.classList.add('pop'); }
      else inp.classList.remove('filled');
      syncHidden();
      if (inp.value && idx < inputs.length - 1) inputs[idx + 1].focus();
    });
    inp.addEventListener('keydown', function(e) {
      if (e.key === 'Backspace' && !inp.value && idx > 0) {
        inputs[idx - 1].classList.remove('filled'); inputs[idx - 1].focus();
      }
    });
    inp.addEventListener('paste', function(e) {
      e.preventDefault();
      var digits = (e.clipboardData || window.clipboardData).getData('text').replace(/\\D/g,'').slice(0,6);
      digits.split('').forEach(function(d,i){ if(inputs[i]){inputs[i].value=d;inputs[i].classList.add('filled');} });
      syncHidden();
      if (inputs[Math.min(digits.length, inputs.length-1)]) inputs[Math.min(digits.length, inputs.length-1)].focus();
    });
  });

  if (inputs[0]) inputs[0].focus();

  var resendBtn   = document.getElementById('resend-btn');
  var resendLabel = document.getElementById('resend-label');
  var COOLDOWN = 60;

  function startResendCooldown() {
    if (!resendBtn) return;
    resendBtn.disabled = true;
    var left = COOLDOWN;
    resendLabel.textContent = 'Resend in ' + left + 's';
    var t = setInterval(function() {
      left--;
      if (left <= 0) { clearInterval(t); resendBtn.disabled = false; resendLabel.textContent = 'Resend code'; }
      else resendLabel.textContent = 'Resend in ' + left + 's';
    }, 1000);
  }
  window.startResendCooldown = startResendCooldown;
  startResendCooldown();
})();
"""

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
        if (inp.value) { inp.classList.add('filled'); inp.classList.remove('pop'); void inp.offsetWidth; inp.classList.add('pop'); }
        else inp.classList.remove('filled');
        hiddenEl.value = Array.from(inputs).map(function(i){ return i.value; }).join('');
        if (inp.value && idx < inputs.length - 1) inputs[idx + 1].focus();
        checkMatch();
      });
      inp.addEventListener('keydown', function(e) {
        if (e.key === 'Backspace' && !inp.value && idx > 0) {
          inputs[idx - 1].classList.remove('filled'); inputs[idx - 1].focus();
        }
      });
    });
  }

  function checkMatch() {
    var p = pinHidden.value, c = confHidden.value;
    if (p.length < 4 || c.length < 4) { hint.textContent=''; submit.disabled=true; return; }
    if (p === c) { hint.textContent='✓ PINs match'; hint.style.color='var(--jade-light)'; submit.disabled=false; }
    else { hint.textContent='✗ PINs do not match'; hint.style.color='var(--danger)'; submit.disabled=true; }
  }

  fillBoxes(pinInputs, pinHidden);
  fillBoxes(confInputs, confHidden);
  if (pinInputs[0]) pinInputs[0].focus();
})();
"""


# ─── Head ─────────────────────────────────────────────────────────────────────

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
        Link(href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap",
             rel="stylesheet"),
        Link(rel="stylesheet", href="/static/css/app.css"),
        Style("""
/* ── Wizard step shell ── */
.wz-step { animation: auth-enter 0.4s cubic-bezier(0.16,1,0.3,1) both; }

/* ── Progress ── */
.wz-progress { margin-bottom: 28px; }
.wz-dots { display: flex; align-items: center; gap: 0; margin-bottom: 10px; }
.wz-dot {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.75rem; font-weight: 800; flex-shrink: 0;
  transition: all .3s;
}
.wz-dot-done   { background: var(--jade-primary); color: #fff; }
.wz-dot-active { background: var(--jade-light); color: #fff;
                 box-shadow: 0 0 0 4px rgba(20,184,166,.2); }
.wz-dot-future { background: var(--border); color: var(--muted); }
.wz-dots .wz-dot:not(:last-child)::after {
  content: ''; display: block; width: 32px; height: 2px;
  background: var(--border); margin: 0 4px; flex-shrink: 0;
}
/* Can't use ::after on flex children easily — use connector divs instead */
.wz-dot-done + .wz-dot-connector   { background: var(--jade-primary); }
.wz-step-label {
  font-size: 0.8rem; color: var(--muted); margin-top: 8px;
  display: flex; align-items: center; gap: 2px;
}
.wz-step-num  { color: var(--jade-light); font-weight: 800; }
.wz-step-name { color: var(--muted); font-weight: 500; }
.wz-sep       { color: var(--subtle); }

/* ── Step header ── */
.wz-step-header { text-align: center; margin-bottom: 28px; }
.wz-hero-icon {
  font-size: 2.4rem; margin-bottom: 12px; display: block;
  filter: drop-shadow(0 0 12px rgba(20,184,166,.3));
}
.wz-hero-icon-wrap {
  position: relative; display: inline-flex; align-items: center;
  justify-content: center; margin-bottom: 12px;
}

/* ── Confirmed phone chip ── */
.wz-confirmed-chip {
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(20,184,166,.1); border: 1px solid rgba(20,184,166,.25);
  border-radius: 999px; padding: 6px 14px; margin-bottom: 20px;
  font-size: 0.85rem; color: var(--text);
}
.wz-chip-icon  { font-size: 1rem; }
.wz-chip-val   { font-weight: 700; }
.wz-chip-badge {
  background: rgba(20,184,166,.2); color: var(--jade-light);
  font-size: 0.7rem; font-weight: 700; padding: 2px 8px;
  border-radius: 999px; text-transform: uppercase; letter-spacing: .04em;
}

/* ── Navigation row ── */
.wz-nav-row {
  display: flex; align-items: center; justify-content: center;
  gap: 10px; margin-top: 16px; flex-wrap: wrap;
}
.wz-nav-sep { color: var(--subtle); font-size: 0.85rem; }

/* ── Alt link (email / phone toggle) ── */
.wz-alt-row {
  display: flex; align-items: center; justify-content: center;
  gap: 6px; margin-top: 14px;
}
.wz-alt-text  { font-size: 0.8rem; color: var(--muted); }
.wz-alt-link  {
  background: none; border: none; cursor: pointer;
  font-size: 0.8rem; color: var(--jade-light); font-weight: 600;
  font-family: inherit; padding: 0; text-decoration: underline;
  text-underline-offset: 2px;
}
.wz-back-link {
  background: none; border: none; cursor: pointer;
  font-size: 0.82rem; color: var(--muted); font-weight: 600;
  font-family: inherit; padding: 0; margin-top: 12px;
  text-decoration: none; display: inline-block;
}
.wz-back-link:hover { color: var(--text); }

/* ── Trust strip ── */
.wz-trust-strip {
  display: flex; gap: 14px; justify-content: center; flex-wrap: wrap;
  margin-top: 24px; padding-top: 20px;
  border-top: 1px solid var(--border);
  font-size: 0.72rem; color: var(--muted); font-weight: 600;
}
.wz-trust-item { display: flex; align-items: center; gap: 5px; }
.wz-trust-icon { color: var(--jade-light); }

/* ── Step transition ── */
#auth-step { transition: opacity 0.18s ease; }
#auth-step.htmx-swapping { opacity: 0; }

/* ── Progress bar dots connector fix ── */
.wz-dots {
  display: grid;
  grid-template-columns: 28px 1fr 28px 1fr 28px;
  align-items: center;
}
.wz-dot-connector {
  height: 2px; background: var(--border); border-radius: 999px;
  transition: background .3s;
}
.wz-dot-connector.done { background: var(--jade-primary); }
        """),
        Script(src="https://unpkg.com/htmx.org@1.9.12"),
        Script(src="/static/js/app.js"),
        Script("(function(){var t=localStorage.getItem('teluka-theme')||(window.matchMedia('(prefers-color-scheme:light)').matches?'light':'dark');document.documentElement.setAttribute('data-theme',t);})();"),
    )


# ─── Background / loader ──────────────────────────────────────────────────────

def _bg_blobs() -> FT:
    return Div(style="position:fixed;inset:0;z-index:-1;overflow:hidden;pointer-events:none;")(
        Div(style="position:absolute;width:700px;height:700px;border-radius:50%;background:radial-gradient(circle,rgba(13,148,136,0.12) 0%,transparent 70%);top:-250px;left:-150px;animation:float1 8s ease-in-out infinite;"),
        Div(style="position:absolute;width:500px;height:500px;border-radius:50%;background:radial-gradient(circle,rgba(64,224,255,0.08) 0%,transparent 70%);bottom:-150px;right:-80px;animation:float2 10s ease-in-out infinite;"),
        Div(style="position:absolute;width:300px;height:300px;border-radius:50%;background:radial-gradient(circle,rgba(139,92,246,0.06) 0%,transparent 70%);top:50%;left:60%;animation:float1 12s ease-in-out infinite reverse;"),
        Style("""
          @keyframes float1{0%,100%{transform:translate(0,0)}50%{transform:translate(20px,-30px)}}
          @keyframes float2{0%,100%{transform:translate(0,0)}50%{transform:translate(-15px,20px)}}
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
            Div(cls="loader-dot"), Div(cls="loader-dot"), Div(cls="loader-dot"),
        ),
        Div(cls="loader-bar-track")(Div(cls="loader-bar-fill")),
        Script("""
(function(){
  function hide(){var l=document.getElementById('page-loader');if(l){l.classList.add('hidden');setTimeout(function(){l.remove();},520);}}
  if(document.readyState==='complete'){hide();}else{window.addEventListener('load',hide);}
})();
        """),
    )


def _pwa_script() -> FT:
    return Script("""
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() { navigator.serviceWorker.register('/static/sw.js'); });
}
(function(){
  if (!window.matchMedia('(hover: hover)').matches) return;
  function attach() {
    var card = document.querySelector('.auth-card');
    if (!card) return;
    card.addEventListener('mousemove', function(e) {
      var r = card.getBoundingClientRect();
      card.style.setProperty('--mx', ((e.clientX-r.left)/r.width*100).toFixed(1)+'%');
      card.style.setProperty('--my', ((e.clientY-r.top)/r.height*100).toFixed(1)+'%');
    });
    card.addEventListener('mouseleave', function() {
      card.style.setProperty('--mx','50%'); card.style.setProperty('--my','50%');
    });
  }
  attach();
  document.body.addEventListener('htmx:afterSwap', attach);
})();
""")

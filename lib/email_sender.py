"""
Email OTP delivery.

Priority order:
  1. Resend API  (RESEND_API_KEY set)       — production, works on all cloud platforms
  2. Gmail SMTP  (GMAIL_USER set, no key)   — local dev fallback via port 587
  3. Terminal    (nothing configured)        — dev print fallback

Resend free tier: 3,000 emails/month, 100/day.
Sign up at resend.com → API Keys → create key → set RESEND_API_KEY in .env
"""
import asyncio
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from lib.config import get_config

logger = logging.getLogger(__name__)

_SUBJECT      = "Your Teluka verification code"
_RESEND_URL   = "https://api.resend.com/emails"
_SMTP_TIMEOUT = 10


_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#0f1117;font-family:Inter,sans-serif;">
  <div style="max-width:480px;margin:40px auto;background:#1a1d27;border-radius:20px;
              padding:40px;border:1px solid rgba(255,255,255,0.08);">
    <div style="font-size:1.4rem;font-weight:900;color:#14B8A6;margin-bottom:8px;">
      Teluka
    </div>
    <div style="font-size:0.85rem;color:#94A3B8;margin-bottom:32px;">
      Secure Escrow for the Philippines
    </div>
    <div style="font-size:0.95rem;color:#CBD5E1;margin-bottom:24px;line-height:1.6;">
      Your one-time verification code is:
    </div>
    <div style="background:#0f1117;border-radius:14px;padding:24px;text-align:center;
                border:1px solid rgba(20,184,166,0.2);margin-bottom:24px;">
      <span style="font-size:2.5rem;font-weight:900;letter-spacing:0.2em;color:#14B8A6;">
        {code}
      </span>
    </div>
    <div style="font-size:0.82rem;color:#64748B;line-height:1.6;">
      Valid for <strong style="color:#94A3B8;">10 minutes</strong>.
      Never share this code with anyone — Teluka will never ask for it.<br><br>
      If you didn't request this, you can safely ignore this email.
    </div>
  </div>
</body>
</html>
"""


# ── Public helpers ────────────────────────────────────────────────────────────

def mask_email(email: str) -> str:
    try:
        local, domain = email.split("@", 1)
        masked = local[0] + "*" * max(1, len(local) - 1)
        return f"{masked}@{domain}"
    except Exception:
        return email


async def send_otp_email(to_email: str, code: str) -> bool:
    """Send OTP. Returns True on success. Never raises."""
    cfg = get_config()

    # ── 1. Resend API (preferred for production) ──────────────────────────────
    if cfg.resend_api_key:
        return await _send_resend(cfg.resend_api_key, cfg.email_from, to_email, code)

    # ── 2. Gmail SMTP (local dev) ─────────────────────────────────────────────
    if cfg.gmail_user and cfg.gmail_app_password:
        loop = asyncio.get_event_loop()
        try:
            sent = await asyncio.wait_for(
                loop.run_in_executor(
                    None, _send_gmail_sync,
                    cfg.gmail_user, cfg.gmail_app_password, to_email, code,
                ),
                timeout=12,
            )
            if sent:
                return True
            logger.warning("Gmail failed — falling back to terminal print (set RESEND_API_KEY for production)")
        except asyncio.TimeoutError:
            logger.error("Gmail SMTP timed out (port 587 blocked) — falling back to terminal print")

    # ── 3. Dev fallback — OTP always visible in server logs ───────────────────
    _dev_print(to_email, code)
    return True


# ── Resend ────────────────────────────────────────────────────────────────────

async def _send_resend(api_key: str, from_addr: str, to_email: str, code: str) -> bool:
    plain = (
        f"Your Teluka verification code: {code}\n"
        "Valid for 10 minutes. Never share this code."
    )
    payload = {
        "from":    from_addr,
        "to":      [to_email],
        "subject": _SUBJECT,
        "html":    _HTML_TEMPLATE.format(code=code),
        "text":    plain,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                _RESEND_URL,
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )
        if resp.is_success:
            logger.info("OTP email sent via Resend to ...%s", to_email.split("@")[-1])
            return True
        logger.error("Resend error %d: %s", resp.status_code, resp.text[:200])
        return False
    except Exception as exc:
        logger.error("Resend request failed: %s", exc)
        return False


# ── Gmail SMTP (local dev fallback) ──────────────────────────────────────────

def _send_gmail_sync(gmail_user: str, app_password: str, to_email: str, code: str) -> bool:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = _SUBJECT
    msg["From"]    = f"Teluka <{gmail_user}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(
        f"Your Teluka verification code: {code}\nValid for 10 minutes.", "plain"
    ))
    msg.attach(MIMEText(_HTML_TEMPLATE.format(code=code), "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=_SMTP_TIMEOUT) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            server.login(gmail_user, app_password)
            server.sendmail(gmail_user, to_email, msg.as_string())
        logger.info("OTP email sent via Gmail to ...%s", to_email.split("@")[-1])
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail auth failed — check GMAIL_USER and GMAIL_APP_PASSWORD")
        return False
    except Exception as exc:
        logger.error("Gmail send failed: %s", exc)
        return False


# ── Dev terminal fallback ─────────────────────────────────────────────────────

def _dev_print(email: str, code: str) -> None:
    sep = "─" * 50
    logger.info(
        "\n%s\n  [DEV EMAIL → %s]\n  Code: %s\n  (Valid 10 min)\n%s",
        sep, email, code, sep,
    )

"""
Email OTP delivery.

Delivery chain (first success wins):
  1. Brevo API    — production, free 300/day, no domain needed, works on Railway
  2. Resend API   — production, free 3k/month, requires verified domain
  3. Gmail SMTP   — local dev only (port 587 blocked on most cloud platforms)
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

_SUBJECT    = "Your Teluka verification code"
_RESEND_URL = "https://api.resend.com/emails"
_BREVO_URL  = "https://api.brevo.com/v3/smtp/email"

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0f1117;font-family:'Inter',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f1117;padding:40px 0;">
    <tr><td align="center">
      <table width="480" cellpadding="0" cellspacing="0"
             style="background:#1a1d27;border-radius:20px;padding:40px;
                    border:1px solid rgba(255,255,255,0.08);max-width:480px;width:100%;">
        <tr><td>
          <div style="font-size:1.4rem;font-weight:900;color:#14B8A6;margin-bottom:6px;">Teluka</div>
          <div style="font-size:0.82rem;color:#94A3B8;margin-bottom:32px;">Secure Escrow · Philippines</div>

          <div style="font-size:0.95rem;color:#CBD5E1;margin-bottom:20px;line-height:1.6;">
            Your one-time verification code:
          </div>

          <div style="background:#0f1117;border-radius:14px;padding:28px 20px;text-align:center;
                      border:1px solid rgba(20,184,166,0.25);margin-bottom:24px;">
            <span style="font-size:2.8rem;font-weight:900;letter-spacing:0.25em;
                         color:#14B8A6;font-variant-numeric:tabular-nums;">
              {code}
            </span>
          </div>

          <div style="font-size:0.82rem;color:#64748B;line-height:1.7;">
            Valid for <strong style="color:#94A3B8;">10 minutes</strong>.
            Never share this code — Teluka will never ask for it.<br><br>
            If you didn't request this, you can safely ignore this email.
          </div>
        </td></tr>
      </table>
      <div style="font-size:0.72rem;color:#334155;margin-top:20px;text-align:center;">
        Teluka &middot; Secure Escrow for the Philippines
      </div>
    </td></tr>
  </table>
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
    """
    Deliver OTP. Returns True on success, False if every provider fails.
    Never raises.
    """
    cfg = get_config()

    # ── 1. Brevo (production — API, no domain needed, works on Railway) ───────
    if cfg.brevo_api_key:
        if await _send_brevo(cfg.brevo_api_key, cfg.brevo_sender_email,
                             cfg.brevo_sender_name, to_email, code):
            return True
        logger.warning("Brevo failed — trying Resend")

    # ── 2. Resend (production — requires verified domain) ────────────────────
    resend_ready = (
        cfg.resend_api_key
        and "onboarding@resend.dev" not in cfg.email_from
    )
    if resend_ready:
        if await _send_resend(cfg.resend_api_key, cfg.email_from, to_email, code):
            return True
        logger.warning("Resend failed — trying Gmail")

    # ── 3. Gmail SMTP (local dev only — port 587 blocked on most cloud hosts) ─
    if cfg.gmail_user and cfg.gmail_app_password:
        loop = asyncio.get_event_loop()
        try:
            sent = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    _send_gmail_sync,
                    cfg.gmail_user,
                    cfg.gmail_app_password,
                    to_email,
                    code,
                ),
                timeout=15,
            )
            if sent:
                return True
        except asyncio.TimeoutError:
            logger.error("Gmail SMTP timed out — port 587 is blocked on this host (expected on Railway/Render/Heroku)")
        except Exception as exc:
            logger.error("Gmail executor error: %s", exc)

    logger.error(
        "All email providers failed for ...%s — "
        "set BREVO_API_KEY in .env (free at brevo.com, no domain needed).",
        to_email.split("@")[-1],
    )
    return False


# ── Brevo ────────────────────────────────────────────────────────────────────

async def _send_brevo(api_key: str, sender_email: str, sender_name: str,
                      to_email: str, code: str) -> bool:
    payload = {
        "sender":      {"name": sender_name, "email": sender_email},
        "to":          [{"email": to_email}],
        "subject":     _SUBJECT,
        "htmlContent": _HTML_TEMPLATE.format(code=code),
        "textContent": (
            f"Your Teluka verification code: {code}\n"
            "Valid for 10 minutes. Never share this code with anyone."
        ),
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                _BREVO_URL,
                json=payload,
                headers={
                    "api-key": api_key,
                    "Content-Type": "application/json",
                },
            )
        if resp.is_success:
            logger.info("OTP sent via Brevo → ...%s", to_email.split("@")[-1])
            return True
        body = resp.text[:400]
        if resp.status_code == 401:
            logger.error("Brevo 401 — BREVO_API_KEY invalid. Regenerate at brevo.com → SMTP & API → API Keys. Body: %s", body)
        elif resp.status_code == 400:
            logger.error("Brevo 400 — sender not verified. Go to brevo.com → Senders & IPs → add %s and verify it. Body: %s", sender_email, body)
        else:
            logger.error("Brevo %d: %s", resp.status_code, body)
        return False
    except httpx.TimeoutException:
        logger.error("Brevo request timed out")
        return False
    except Exception as exc:
        logger.error("Brevo request exception: %s", exc)
        return False


# ── Resend ────────────────────────────────────────────────────────────────────

async def _send_resend(api_key: str, from_addr: str, to_email: str, code: str) -> bool:
    payload = {
        "from":    from_addr,
        "to":      [to_email],
        "subject": _SUBJECT,
        "html":    _HTML_TEMPLATE.format(code=code),
        "text":    (
            f"Your Teluka verification code: {code}\n"
            "Valid for 10 minutes. Never share this code with anyone."
        ),
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                _RESEND_URL,
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )
        if resp.is_success:
            logger.info("OTP sent via Resend → ...%s", to_email.split("@")[-1])
            return True

        body = resp.text[:400]
        if resp.status_code == 401:
            logger.error(
                "Resend 401 — API key invalid or revoked. "
                "Regenerate at resend.com/api-keys. Body: %s", body
            )
        elif resp.status_code in (403, 422):
            logger.error(
                "Resend %d — sender domain not verified. "
                "Using onboarding@resend.dev only works for your own account email. "
                "Verify a domain at resend.com/domains and update EMAIL_FROM. Body: %s",
                resp.status_code, body,
            )
        else:
            logger.error("Resend %d: %s", resp.status_code, body)
        return False

    except httpx.TimeoutException:
        logger.error("Resend request timed out")
        return False
    except Exception as exc:
        logger.error("Resend request exception: %s", exc)
        return False


# ── Gmail SMTP ────────────────────────────────────────────────────────────────

def _send_gmail_sync(gmail_user: str, app_password: str, to_email: str, code: str) -> bool:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = _SUBJECT
    msg["From"]    = f"Teluka <{gmail_user}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(
        f"Your Teluka verification code: {code}\n"
        "Valid for 10 minutes. Never share this code with anyone.",
        "plain",
    ))
    msg.attach(MIMEText(_HTML_TEMPLATE.format(code=code), "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            server.login(gmail_user, app_password)
            server.sendmail(gmail_user, to_email, msg.as_string())
        logger.info("OTP sent via Gmail → ...%s", to_email.split("@")[-1])
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "Gmail auth failed — ensure GMAIL_APP_PASSWORD is a 16-char App Password, "
            "not your normal Gmail password. Create one at myaccount.google.com/apppasswords"
        )
        return False
    except Exception as exc:
        logger.error("Gmail send error: %s", exc)
        return False

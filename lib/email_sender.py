"""
Email OTP delivery via Gmail SMTP.

Setup (one-time):
  1. Enable 2-Step Verification on your Google account
  2. Go to myaccount.google.com → Security → App passwords
  3. Create an app password named "Teluka"
  4. Copy the 16-char password into GMAIL_APP_PASSWORD in .env

Dev mode: Leave GMAIL_USER blank → code prints to terminal.
"""
import asyncio
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from lib.config import get_config

logger = logging.getLogger(__name__)

_SUBJECT = "Your Teluka verification code"

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


def _mask_email(email: str) -> str:
    """d****@gmail.com"""
    local, domain = email.split("@", 1)
    masked_local = local[0] + "*" * max(1, len(local) - 1)
    return f"{masked_local}@{domain}"


def mask_email(email: str) -> str:
    """Public helper — used by login page to display masked email."""
    try:
        return _mask_email(email)
    except Exception:
        return email


async def send_otp_email(to_email: str, code: str) -> bool:
    """
    Send OTP to `to_email`. Returns True on success.
    Falls back to terminal print when Gmail is not configured.
    """
    cfg = get_config()

    if not cfg.gmail_user:
        _dev_print(to_email, code)
        return True

    if not cfg.gmail_app_password:
        logger.error("GMAIL_APP_PASSWORD is not set")
        return False

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _send_gmail_sync, cfg.gmail_user, cfg.gmail_app_password, to_email, code
    )


def _send_gmail_sync(
    gmail_user: str,
    app_password: str,
    to_email: str,
    code: str,
) -> bool:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = _SUBJECT
    msg["From"]    = f"Teluka <{gmail_user}>"
    msg["To"]      = to_email

    plain = f"Your Teluka verification code: {code}\nValid for 10 minutes. Never share this code."
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(_HTML_TEMPLATE.format(code=code), "html"))

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
            server.login(gmail_user, app_password)
            server.sendmail(gmail_user, to_email, msg.as_string())
        logger.info("OTP email sent to ...%s", to_email.split("@")[-1])
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "Gmail authentication failed — check GMAIL_USER and GMAIL_APP_PASSWORD"
        )
        return False
    except Exception as exc:
        logger.error("Gmail send failed: %s", exc)
        return False


def _dev_print(email: str, code: str) -> None:
    sep = "─" * 50
    logger.info(
        "\n%s\n  [DEV EMAIL → %s]\n  Code: %s\n  (Valid 10 min)\n%s",
        sep, email, code, sep,
    )

"""
SMS gateway — supports Semaphore (PH-native), Vonage, and Twilio.

Dev mode:   Leave credentials blank → code prints to the terminal, free.
Production: Set SMS_PROVIDER=semaphore and fill SEMAPHORE_API_KEY.
Fallback:   Set SMS_PROVIDER=vonage or twilio with their respective vars.
"""
import logging

import httpx

from lib.config import get_config

logger = logging.getLogger(__name__)

_MESSAGE_TEMPLATE = (
    "Your Teluka verification code: {code}\n"
    "Valid for 10 minutes. Never share this code with anyone."
)


async def send_otp(phone: str, code: str) -> bool:
    """
    Send OTP SMS. Returns True on success.
    Falls back to terminal print when credentials are not configured.
    """
    cfg     = get_config()
    message = _MESSAGE_TEMPLATE.format(code=code)

    if cfg.sms_provider == "semaphore":
        return await _send_semaphore(cfg, phone, message)
    if cfg.sms_provider == "vonage":
        return await _send_vonage(cfg, phone, message)
    return await _send_twilio(cfg, phone, message)


# ── Semaphore (PH-native, ₱0.50/SMS) ─────────────────────────────────────────

async def _send_semaphore(cfg, phone: str, message: str) -> bool:
    if not cfg.semaphore_api_key:
        _dev_print(phone, message)
        return True

    # Semaphore expects local PH format: 09XXXXXXXXX
    local_phone = phone.replace("+63", "0") if phone.startswith("+63") else phone

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.semaphore.co/api/v4/messages",
                data={
                    "apikey":      cfg.semaphore_api_key,
                    "number":      local_phone,
                    "message":     message,
                    "sendername":  cfg.semaphore_sender_name,
                },
            )
    except httpx.TimeoutException:
        logger.error("Semaphore request timed out for phone=...%s", phone[-4:])
        return False
    except httpx.RequestError as exc:
        logger.error("Semaphore request error: %s", exc)
        return False

    if resp.status_code == 200:
        try:
            body   = resp.json()
            msg_id = body[0].get("message_id", "?") if isinstance(body, list) else "?"
        except Exception:
            msg_id = "?"
        logger.info("SMS sent via Semaphore id=%s phone=...%s", msg_id, phone[-4:])
        return True

    logger.error(
        "Semaphore delivery failed status=%d body=%r phone=...%s",
        resp.status_code, resp.text[:200], phone[-4:],
    )
    return False


# ── Vonage ────────────────────────────────────────────────────────────────────

async def _send_vonage(cfg, phone: str, message: str) -> bool:
    if not cfg.vonage_api_key:
        _dev_print(phone, message)
        return True

    if not cfg.vonage_api_secret:
        logger.error("VONAGE_API_SECRET is missing")
        return False

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://rest.nexmo.com/sms/json",
                data={
                    "api_key":    cfg.vonage_api_key,
                    "api_secret": cfg.vonage_api_secret,
                    "from":       cfg.vonage_from,
                    "to":         phone,
                    "text":       message,
                },
            )
    except httpx.TimeoutException:
        logger.error("Vonage request timed out for phone=...%s", phone[-4:])
        return False
    except httpx.RequestError as exc:
        logger.error("Vonage request error: %s", exc)
        return False

    try:
        body = resp.json()
        msg  = body.get("messages", [{}])[0]
        status = msg.get("status", "-1")
    except Exception:
        logger.error("Vonage unparseable response: %s", resp.text[:200])
        return False

    if status == "0":
        logger.info(
            "SMS sent via Vonage id=%s remaining=%s phone=...%s",
            msg.get("message-id", "?"),
            msg.get("remaining-balance", "?"),
            phone[-4:],
        )
        return True

    # Vonage error codes: https://developer.vonage.com/en/messaging/sms/guides/troubleshooting-sms
    logger.error(
        "Vonage delivery failed status=%s error=%r phone=...%s",
        status, msg.get("error-text", "unknown"), phone[-4:],
    )
    return False


# ── Twilio ────────────────────────────────────────────────────────────────────

async def _send_twilio(cfg, phone: str, message: str) -> bool:
    if not cfg.twilio_account_sid:
        _dev_print(phone, message)
        return True

    if not cfg.twilio_auth_token or not cfg.twilio_from:
        logger.error(
            "Twilio is partially configured — TWILIO_AUTH_TOKEN or TWILIO_FROM is missing"
        )
        return False

    url = (
        f"https://api.twilio.com/2010-04-01"
        f"/Accounts/{cfg.twilio_account_sid}/Messages.json"
    )

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                url,
                auth=(cfg.twilio_account_sid, cfg.twilio_auth_token),
                data={"From": cfg.twilio_from, "To": phone, "Body": message},
            )
    except httpx.TimeoutException:
        logger.error("Twilio request timed out for phone=...%s", phone[-4:])
        return False
    except httpx.RequestError as exc:
        logger.error("Twilio request error: %s", exc)
        return False

    if resp.status_code == 201:
        sid = resp.json().get("sid", "?")
        logger.info("SMS sent via Twilio sid=%s phone=...%s", sid, phone[-4:])
        return True

    # Twilio returns 4xx/5xx with a JSON body explaining the error
    try:
        body = resp.json()
        code = body.get("code", "?")
        detail = body.get("message", resp.text)
    except Exception:
        code, detail = "?", resp.text

    logger.error(
        "Twilio delivery failed status=%d code=%s detail=%r phone=...%s",
        resp.status_code, code, detail, phone[-4:],
    )
    return False


# ── Dev fallback ──────────────────────────────────────────────────────────────

def _dev_print(phone: str, message: str) -> None:
    """Print the OTP to the terminal when no SMS provider is configured."""
    sep = "─" * 50
    logger.info("\n%s\n  [DEV SMS → %s]\n  %s\n%s", sep, phone, message, sep)

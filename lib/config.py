"""
Centralised application config — loaded once at startup.
Raises a clear RuntimeError if a required env var is missing
so the app fails fast rather than crashing on first use.
"""
import logging
import os
from functools import lru_cache

logger = logging.getLogger(__name__)


class _MissingEnvError(RuntimeError):
    pass


def _require(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        raise _MissingEnvError(
            f"Required environment variable '{name}' is not set. "
            "Add it to your .env file and restart."
        )
    return val


def _optional(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


class Config:
    def __init__(self) -> None:
        # ── Supabase ──────────────────────────────────────────────────────────
        self.supabase_url: str        = _require("SUPABASE_URL")
        self.supabase_anon_key: str   = _require("SUPABASE_KEY")
        self.supabase_service_key: str = (
            _optional("SUPABASE_SERVICE_KEY") or self.supabase_anon_key
        )

        # ── Sessions ──────────────────────────────────────────────────────────
        self.session_secret: str = _require("SESSION_SECRET")

        # ── PayMongo ──────────────────────────────────────────────────────────
        self.mock_payments: bool = _optional("MOCK_PAYMENTS", "false").lower() in ("1", "true", "yes")
        self.paymongo_secret_key: str = _optional("PAYMONGO_SECRET_KEY")
        if not self.paymongo_secret_key and not self.mock_payments:
            logger.warning(
                "PAYMONGO_SECRET_KEY is not set — escrow/payment features "
                "will raise errors at runtime. Set MOCK_PAYMENTS=true to bypass."
            )

        # ── Mock uploads (EXIF check + Supabase Storage) ──────────────────────
        # When MOCK_PAYMENTS=true, uploads are also mocked by default so the
        # entire deal flow works end-to-end without any real credentials.
        # Override with MOCK_UPLOADS=false to test real uploads with mock payments.
        _mock_uploads_raw = _optional("MOCK_UPLOADS", "").lower()
        if _mock_uploads_raw in ("1", "true", "yes"):
            self.mock_uploads: bool = True
        elif _mock_uploads_raw in ("0", "false", "no"):
            self.mock_uploads = False
        else:
            self.mock_uploads = self.mock_payments  # inherit from mock_payments

        # ── SMS ───────────────────────────────────────────────────────────────
        self.sms_provider: str       = _optional("SMS_PROVIDER", "semaphore")
        # Semaphore (PH-native)
        self.semaphore_api_key: str     = _optional("SEMAPHORE_API_KEY")
        self.semaphore_sender_name: str = _optional("SEMAPHORE_SENDER_NAME", "TELUKA")
        # Vonage (fallback)
        self.vonage_api_key: str    = _optional("VONAGE_API_KEY")
        self.vonage_api_secret: str = _optional("VONAGE_API_SECRET")
        self.vonage_from: str       = _optional("VONAGE_FROM", "TELUKA")
        # Twilio (fallback)
        self.twilio_account_sid: str = _optional("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token: str  = _optional("TWILIO_AUTH_TOKEN")
        self.twilio_from: str        = _optional("TWILIO_FROM")

        # ── Email (OTP delivery) ──────────────────────────────────────────────
        self.resend_api_key: str     = _optional("RESEND_API_KEY")
        self.email_from: str         = _optional("EMAIL_FROM", "Teluka <onboarding@resend.dev>")
        # Brevo (production API — no domain needed, works on all cloud platforms)
        self.brevo_api_key: str      = _optional("BREVO_API_KEY")
        self.brevo_sender_email: str = _optional("BREVO_SENDER_EMAIL", "llanesdanmarc@gmail.com")
        self.brevo_sender_name: str  = _optional("BREVO_SENDER_NAME", "Teluka")
        # Gmail SMTP (local dev only — blocked on most cloud platforms)
        self.gmail_user: str         = _optional("GMAIL_USER")
        self.gmail_app_password: str = _optional("GMAIL_APP_PASSWORD")

        # ── Supabase Storage ──────────────────────────────────────────────────
        self.storage_bucket: str = _optional("STORAGE_BUCKET", "evidence")

        # ── Redis (optional — Upstash free tier works well) ───────────────────
        self.redis_url: str = _optional("REDIS_URL")

        # ── Auth hardening ────────────────────────────────────────────────────
        # Server-side pepper for HMAC-SHA256 OTP hashing.
        # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
        self.otp_secret: str = _optional("OTP_SECRET")

        # ── Web Push (VAPID) ─────────────────────────────────────────────────
        # Generate once with: python -c "from py_vapid import Vapid; v=Vapid(); v.generate_keys(); print(v.private_pem().decode()); print(v.public_key.decode())"
        self.vapid_private_key: str = _optional("VAPID_PRIVATE_KEY")
        self.vapid_public_key: str  = _optional("VAPID_PUBLIC_KEY")
        self.vapid_email: str       = _optional("VAPID_EMAIL", "admin@teluka.dev")

        # ── Allowed hosts (CSRF + TrustedHost) ───────────────────────────────
        _hosts = _optional("ALLOWED_HOSTS", "localhost,127.0.0.1")
        self.allowed_hosts: set[str] = {h.strip() for h in _hosts.split(",") if h.strip()}

        # ── Runtime ───────────────────────────────────────────────────────────
        self.env: str = _optional("ENV", "development")
        self.is_production: bool = self.env == "production"


@lru_cache(maxsize=1)
def get_config() -> Config:
    return Config()

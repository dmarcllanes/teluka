import base64
import logging
import secrets
import time
from typing import Any

import httpx

from lib.config import get_config

logger    = logging.getLogger(__name__)
_BASE_URL = "https://api.paymongo.com/v1"

# In-memory store for mock payment intents (keyed by mock intent id)
_mock_intents: dict[str, dict[str, Any]] = {}


# ── Mock helpers ──────────────────────────────────────────────────────────────

def _mock_intent(amount_centavos: int, description: str) -> dict[str, Any]:
    intent_id = f"mock_pi_{secrets.token_hex(10)}"
    intent = {
        "id": intent_id,
        "type": "payment_intent",
        "attributes": {
            "amount": amount_centavos,
            "currency": "PHP",
            "description": description,
            "status": "awaiting_payment_method",
            "capture_type": "manual",
            "created_at": int(time.time()),
        },
    }
    _mock_intents[intent_id] = intent
    logger.info("[MOCK] Created PaymentIntent id=%s amount=%d", intent_id, amount_centavos)
    return intent


def _mock_capture(payment_intent_id: str, amount_centavos: int) -> dict[str, Any]:
    intent = _mock_intents.get(payment_intent_id, {"id": payment_intent_id, "attributes": {}})
    intent["attributes"]["status"] = "succeeded"
    intent["attributes"]["captured_amount"] = amount_centavos
    logger.info("[MOCK] Captured PaymentIntent id=%s", payment_intent_id)
    return intent


def _mock_cancel(payment_intent_id: str) -> dict[str, Any]:
    intent = _mock_intents.get(payment_intent_id, {"id": payment_intent_id, "attributes": {}})
    intent["attributes"]["status"] = "cancelled"
    logger.info("[MOCK] Cancelled PaymentIntent id=%s", payment_intent_id)
    return intent


def _mock_get(payment_intent_id: str) -> dict[str, Any]:
    if payment_intent_id in _mock_intents:
        return _mock_intents[payment_intent_id]
    # Unknown mock id — return a generic succeeded state
    return {
        "id": payment_intent_id,
        "attributes": {"status": "succeeded"},
    }


# ── Real API helpers ──────────────────────────────────────────────────────────

def _auth_headers() -> dict[str, str]:
    cfg = get_config()
    if not cfg.paymongo_secret_key:
        raise RuntimeError(
            "PAYMONGO_SECRET_KEY is not configured. "
            "Add it to your .env file, or set MOCK_PAYMENTS=true to bypass."
        )
    token = base64.b64encode(f"{cfg.paymongo_secret_key}:".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }


def _raise_for_paymongo(resp: httpx.Response) -> None:
    if resp.is_error:
        try:
            body   = resp.json()
            errors = body.get("errors", [])
            detail = errors[0].get("detail", resp.text) if errors else resp.text
        except Exception:
            detail = resp.text
        raise RuntimeError(f"PayMongo error {resp.status_code}: {detail}")


# ── Public API ────────────────────────────────────────────────────────────────

async def create_payment_intent(amount_centavos: int, description: str) -> dict[str, Any]:
    """Create a PaymentIntent to hold funds (GCash/Maya). Returns mock data if MOCK_PAYMENTS=true."""
    if get_config().mock_payments:
        return _mock_intent(amount_centavos, description)

    payload = {
        "data": {
            "attributes": {
                "amount": amount_centavos,
                "payment_method_allowed": ["gcash", "paymaya"],
                "payment_method_options": {"card": {"request_three_d_secure": "any"}},
                "currency": "PHP",
                "description": description,
                "capture_type": "manual",
            }
        }
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{_BASE_URL}/payment_intents",
            json=payload,
            headers=_auth_headers(),
        )
        _raise_for_paymongo(resp)
        data = resp.json()["data"]
        logger.info("Created PaymentIntent id=%s amount=%d", data["id"], amount_centavos)
        return data


async def capture_payment_intent(payment_intent_id: str, amount_centavos: int) -> dict[str, Any]:
    """Release escrowed funds to the seller."""
    if get_config().mock_payments:
        return _mock_capture(payment_intent_id, amount_centavos)

    payload = {"data": {"attributes": {"amount": amount_centavos}}}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{_BASE_URL}/payment_intents/{payment_intent_id}/capture",
            json=payload,
            headers=_auth_headers(),
        )
        _raise_for_paymongo(resp)
        logger.info("Captured PaymentIntent id=%s", payment_intent_id)
        return resp.json()["data"]


async def cancel_payment_intent(payment_intent_id: str) -> dict[str, Any]:
    """Cancel a held PaymentIntent (refund to buyer)."""
    if get_config().mock_payments:
        return _mock_cancel(payment_intent_id)

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{_BASE_URL}/payment_intents/{payment_intent_id}/cancel",
            headers=_auth_headers(),
        )
        _raise_for_paymongo(resp)
        logger.info("Cancelled PaymentIntent id=%s", payment_intent_id)
        return resp.json()["data"]


async def get_payment_intent(payment_intent_id: str) -> dict[str, Any]:
    """Fetch current status of a PaymentIntent."""
    if get_config().mock_payments:
        return _mock_get(payment_intent_id)

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{_BASE_URL}/payment_intents/{payment_intent_id}",
            headers=_auth_headers(),
        )
        _raise_for_paymongo(resp)
        return resp.json()["data"]

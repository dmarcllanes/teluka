import base64
import logging
from typing import Any

import httpx

from lib.config import get_config

logger   = logging.getLogger(__name__)
_BASE_URL = "https://api.paymongo.com/v1"


def _auth_headers() -> dict[str, str]:
    cfg   = get_config()
    if not cfg.paymongo_secret_key:
        raise RuntimeError(
            "PAYMONGO_SECRET_KEY is not configured. "
            "Add it to your .env file to enable payment features."
        )
    token = base64.b64encode(f"{cfg.paymongo_secret_key}:".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }


def _raise_for_paymongo(resp: httpx.Response) -> None:
    """Raise a clear RuntimeError for PayMongo API errors."""
    if resp.is_error:
        try:
            body   = resp.json()
            errors = body.get("errors", [])
            detail = errors[0].get("detail", resp.text) if errors else resp.text
        except Exception:
            detail = resp.text
        raise RuntimeError(f"PayMongo error {resp.status_code}: {detail}")


async def create_payment_intent(amount_centavos: int, description: str) -> dict[str, Any]:
    """Create a PayMongo PaymentIntent to hold funds (GCash/Maya)."""
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
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{_BASE_URL}/payment_intents/{payment_intent_id}/cancel",
            headers=_auth_headers(),
        )
        _raise_for_paymongo(resp)
        logger.info("Cancelled PaymentIntent id=%s", payment_intent_id)
        return resp.json()["data"]


async def get_payment_intent(payment_intent_id: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{_BASE_URL}/payment_intents/{payment_intent_id}",
            headers=_auth_headers(),
        )
        _raise_for_paymongo(resp)
        return resp.json()["data"]

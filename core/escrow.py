import logging
from datetime import datetime, timezone

from core.forensics import compute_trust_score
from lib.paymongo_client import (
    cancel_payment_intent,
    capture_payment_intent,
    create_payment_intent,
    get_payment_intent,
)
from lib.supabase_client import get_supabase_admin
from schemas.transaction import Transaction, TransactionStatus

logger = logging.getLogger(__name__)


async def initiate_escrow(transaction: Transaction) -> str:
    """
    Create a PayMongo PaymentIntent and hold the buyer's funds.
    Returns the payment_intent_id stored on the transaction.
    """
    data = await create_payment_intent(
        amount_centavos=transaction.amount_centavos,
        description=transaction.item_description,
    )
    payment_intent_id: str = data["id"]

    supabase = await get_supabase_admin()
    await supabase.table("transactions").update(
        {
            "payment_intent_id": payment_intent_id,
            "status": TransactionStatus.ESCROWED,
        }
    ).eq("id", transaction.id).execute()

    logger.info("Escrow initiated tx=%s intent=%s", transaction.id, payment_intent_id)
    return payment_intent_id


async def release_escrow(transaction: Transaction) -> None:
    """
    Capture escrowed funds — called after buyer confirms receipt.
    Also recalculates trust scores for both parties.
    """
    if not transaction.payment_intent_id:
        raise ValueError(f"Transaction {transaction.id} has no payment_intent_id")

    await capture_payment_intent(
        payment_intent_id=transaction.payment_intent_id,
        amount_centavos=transaction.amount_centavos,
    )

    supabase = await get_supabase_admin()
    await supabase.table("transactions").update(
        {"status": TransactionStatus.COMPLETED}
    ).eq("id", transaction.id).execute()

    logger.info("Escrow released tx=%s", transaction.id)

    # Recalculate trust scores for both parties asynchronously
    # (non-blocking — failures don't affect the release)
    try:
        await _recalculate_trust_score(transaction.buyer_id)
        await _recalculate_trust_score(transaction.seller_id)
    except Exception:
        logger.exception(
            "Trust score recalculation failed after release tx=%s", transaction.id
        )


async def cancel_escrow(transaction: Transaction) -> None:
    """
    Cancel and refund escrowed funds back to the buyer.
    Handles the case where no PaymentIntent exists (pre-escrow cancellation).
    """
    supabase = await get_supabase_admin()

    if transaction.payment_intent_id:
        await cancel_payment_intent(transaction.payment_intent_id)
        new_status = TransactionStatus.REFUNDED
        logger.info("PaymentIntent cancelled tx=%s", transaction.id)
    else:
        # Cancelled before buyer paid — no payment to refund
        new_status = TransactionStatus.CANCELLED

    await supabase.table("transactions").update(
        {"status": new_status}
    ).eq("id", transaction.id).execute()

    logger.info("Deal cancelled tx=%s status=%s", transaction.id, new_status)


async def get_escrow_status(payment_intent_id: str) -> str:
    """Return the raw PayMongo status of a PaymentIntent."""
    data = await get_payment_intent(payment_intent_id)
    return data["attributes"]["status"]


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _recalculate_trust_score(user_id: str) -> None:
    """Recompute and persist the trust score for a user after a transaction event."""
    supabase = await get_supabase_admin()

    user_row = (
        await supabase.table("users").select("*").eq("id", user_id).single().execute()
    ).data
    if not user_row:
        return

    tx_rows = (
        await supabase.table("transactions")
        .select("status")
        .or_(f"buyer_id.eq.{user_id},seller_id.eq.{user_id}")
        .execute()
    ).data or []

    completed = sum(
        1 for r in tx_rows if r["status"] == TransactionStatus.COMPLETED
    )

    created_at_str = user_row.get("created_at")
    if created_at_str:
        created_at = datetime.fromisoformat(
            created_at_str.replace("Z", "+00:00")
        )
        account_age_days = (datetime.now(timezone.utc) - created_at).days
    else:
        account_age_days = 0

    new_score = compute_trust_score(
        total_transactions=completed,
        scam_reports=user_row.get("scam_reports", 0),
        is_kyc_verified=(
            user_row.get("gcash_verified", False)
            or user_row.get("maya_verified", False)
        ),
        account_age_days=account_age_days,
    )

    await supabase.table("users").update(
        {"trust_score": new_score}
    ).eq("id", user_id).execute()

    logger.info(
        "Trust score updated user=%s score=%.2f completed_tx=%d",
        user_id, new_score, completed,
    )

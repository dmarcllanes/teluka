from datetime import datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, field_validator


class TransactionStatus(StrEnum):
    PENDING = "pending"           # Created, awaiting payment
    ESCROWED = "escrowed"         # Funds held by PayMongo
    EVIDENCE_SUBMITTED = "evidence_submitted"  # Seller uploaded photos
    IN_TRANSIT = "in_transit"     # Logistics confirmed pickup
    DELIVERED = "delivered"       # Logistics confirmed delivery
    UNBOXING_UPLOADED = "unboxing_uploaded"    # Buyer uploaded video
    COMPLETED = "completed"       # Funds released to seller
    DISPUTED = "disputed"         # Buyer raised a dispute
    CANCELLED = "cancelled"       # Cancelled before escrow
    REFUNDED = "refunded"         # Funds returned to buyer


class Transaction(BaseModel):
    id: str
    buyer_id: str
    seller_id: str
    item_description: str
    amount_centavos: int          # e.g. ₱1,000 = 100_000
    status: TransactionStatus = TransactionStatus.PENDING
    payment_intent_id: Optional[str] = None
    evidence_photo_urls: list[str] = []
    unboxing_video_url: Optional[str] = None
    delivery_tracking_id: Optional[str] = None
    created_at: datetime = datetime.now()
    expires_at: Optional[datetime] = None  # Asia/Manila timezone

    @field_validator("amount_centavos")
    @classmethod
    def must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("amount_centavos must be positive")
        return v


class CreateTransactionRequest(BaseModel):
    buyer_id: str
    seller_id: str
    item_description: str
    amount_centavos: int

    @field_validator("amount_centavos")
    @classmethod
    def must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("amount_centavos must be positive")
        return v


class UpdateTransactionStatus(BaseModel):
    transaction_id: str
    status: TransactionStatus

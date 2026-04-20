from datetime import datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, constr


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
    amount_centavos: int           # item price, e.g. ₱1,000 = 100_000
    platform_fee_centavos: int = 0 # Teluka service fee
    protection_plan: str = "basic" # "basic" | "standard" | "premium"
    status: TransactionStatus = TransactionStatus.PENDING
    payment_intent_id: Optional[str] = None
    evidence_photo_urls: Optional[list[str]] = Field(default_factory=list)
    unboxing_video_url: Optional[str] = None
    delivery_tracking_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None  # Asia/Manila timezone

    @field_validator("evidence_photo_urls", mode="before")
    @classmethod
    def coerce_photo_urls(cls, v):
        return v if isinstance(v, list) else []

    @property
    def total_centavos(self) -> int:
        return self.amount_centavos + self.platform_fee_centavos

    @field_validator("amount_centavos")
    @classmethod
    def must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("amount_centavos must be positive")
        return v


class CreateTransactionRequest(BaseModel):
    buyer_id: str
    seller_id: str
    item_description: str = Field(min_length=3, max_length=300)
    amount_centavos: int
    protection_plan: str = Field(default="basic", max_length=20)
    platform_fee_centavos: int = 0

    @field_validator("amount_centavos")
    @classmethod
    def must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("amount_centavos must be positive")
        # Cap at ₱500,000 (50_000_000 centavos) — flag anything above for review
        if v > 50_000_000:
            raise ValueError("amount exceeds maximum transaction limit")
        return v


class UpdateTransactionStatus(BaseModel):
    transaction_id: str
    status: TransactionStatus

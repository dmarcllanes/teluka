from enum import StrEnum
from pydantic import BaseModel, field_validator


class KYCStatus(StrEnum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class TrustLevel(StrEnum):
    NEW = "new"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLACKLISTED = "blacklisted"


class UserProfile(BaseModel):
    id: str
    phone: str
    email: str | None = None
    gcash_verified: bool = False
    maya_verified: bool = False
    trust_score: float = 0.0  # 0.0 – 100.0
    trust_level: TrustLevel = TrustLevel.NEW
    kyc_status: KYCStatus = KYCStatus.UNVERIFIED
    total_transactions: int = 0
    scam_reports: int = 0

    @field_validator("trust_score")
    @classmethod
    def clamp_trust_score(cls, v: float) -> float:
        return max(0.0, min(100.0, v))

    @property
    def is_kyc_verified(self) -> bool:
        return self.gcash_verified or self.maya_verified


class CreateUserRequest(BaseModel):
    phone: str
    gcash_verified: bool = False
    maya_verified: bool = False

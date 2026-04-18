class TelukError(Exception):
    """Base exception for all Teluka domain errors."""


class InsufficientFunds(TelukError):
    """Raised when the buyer's payment method has insufficient funds."""


class VerificationFailed(TelukError):
    """Raised when evidence (photo EXIF, unboxing video) fails verification."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Verification failed: {reason}")


class ScamDetected(TelukError):
    """Raised when the risk engine flags a transaction or user as fraudulent."""

    def __init__(self, reason: str, risk_score: float | None = None) -> None:
        self.reason = reason
        self.risk_score = risk_score
        super().__init__(f"Scam detected ({risk_score=}): {reason}")

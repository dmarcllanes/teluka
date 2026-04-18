from dataclasses import dataclass

import polars as pl

from core.exceptions import ScamDetected

# Weights used in trust score computation
_W_REPORTS = 40.0
_W_COMPLETION_RATE = 30.0
_W_KYC = 20.0
_W_AGE = 10.0

_BLACKLIST_PATH = "data/blacklisted_phones.parquet"


@dataclass
class RiskResult:
    score: float       # 0 (safe) → 100 (high risk)
    flags: list[str]


def compute_trust_score(
    total_transactions: int,
    scam_reports: int,
    is_kyc_verified: bool,
    account_age_days: int,
) -> float:
    """
    Returns a trust score between 0.0 and 100.0.
    Higher is more trustworthy.
    """
    if total_transactions == 0:
        completion_rate = 0.5  # Neutral for new accounts
    else:
        completion_rate = max(0.0, 1.0 - (scam_reports / total_transactions))

    report_penalty = min(1.0, scam_reports / 5.0)  # 5+ reports → max penalty
    age_score = min(1.0, account_age_days / 180.0)  # 6 months → max age score

    score = (
        (1.0 - report_penalty) * _W_REPORTS
        + completion_rate * _W_COMPLETION_RATE
        + (1.0 if is_kyc_verified else 0.0) * _W_KYC
        + age_score * _W_AGE
    )
    return round(min(100.0, max(0.0, score)), 2)


def analyze_risk(
    phone: str,
    trust_score: float,
    scam_reports: int,
) -> RiskResult:
    """
    Run risk checks against the seller/buyer profile.
    Raises ScamDetected if the risk is unacceptable.
    """
    flags: list[str] = []
    risk_score = 100.0 - trust_score

    if scam_reports >= 3:
        flags.append(f"high_report_count:{scam_reports}")

    if trust_score < 20.0:
        flags.append("very_low_trust_score")

    if is_phone_blacklisted(phone):
        flags.append("blacklisted_phone")
        raise ScamDetected("Phone number is on the blacklist", risk_score=100.0)

    if risk_score >= 80.0:
        raise ScamDetected("Risk score too high to proceed", risk_score=risk_score)

    return RiskResult(score=risk_score, flags=flags)


def is_phone_blacklisted(phone: str) -> bool:
    """
    Check a phone number against the blacklist using Polars LazyFrame.
    Falls back to False if the blacklist file does not exist yet.
    """
    try:
        result = (
            pl.scan_parquet(_BLACKLIST_PATH)
            .filter(pl.col("phone") == phone)
            .limit(1)
            .collect()
        )
        return len(result) > 0
    except FileNotFoundError:
        return False


def load_risk_log(log_path: str) -> pl.LazyFrame:
    """Load a CSV risk/activity log as a LazyFrame for batch analysis."""
    return pl.scan_csv(log_path)


def top_risky_phones(log_path: str, top_n: int = 50) -> pl.DataFrame:
    """Return the top N phones by scam report count from a risk log CSV."""
    return (
        load_risk_log(log_path)
        .group_by("phone")
        .agg(pl.col("report_count").sum().alias("total_reports"))
        .sort("total_reports", descending=True)
        .limit(top_n)
        .collect()
    )

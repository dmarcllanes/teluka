"""
Teluka Protection Plans — user picks one when creating a deal.
The plan sets verification requirements AND the platform fee (Teluka's revenue).

  Basic    — Free       · 3 photos · 48h review
  Standard — ₱29 flat  · 5 photos · 72h · tracking required
  Premium  — 1.5%      · 7 photos · GPS · 96h · tracking · priority dispute
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProtectionPlan:
    id: str
    name: str
    icon: str
    tagline: str
    perks: tuple[str, ...]

    # Verification requirements
    min_photos: int
    review_hours: int
    requires_tracking: bool
    requires_gps: bool

    # Fee
    fee_type: str            # "free" | "flat" | "percent"
    flat_fee_centavos: int   # used when fee_type == "flat"
    percent_fee: float       # used when fee_type == "percent" (e.g. 0.015)
    min_fee_centavos: int    # floor for percent fees

    # UI
    badge_cls: str
    badge_icon: str
    recommended_above_centavos: int  # highlight as recommended above this amount

    # Backward compat (used by verification + activity log)
    @property
    def label(self) -> str:
        return self.name

    @property
    def description(self) -> str:
        return self.tagline

    def fee_centavos(self, amount_centavos: int) -> int:
        """Compute Teluka's platform fee for a given deal amount."""
        if self.fee_type == "free":
            return 0
        if self.fee_type == "flat":
            return self.flat_fee_centavos
        # percent
        raw = int(amount_centavos * self.percent_fee)
        return max(raw, self.min_fee_centavos)

    def fee_label(self, amount_centavos: int) -> str:
        fee = self.fee_centavos(amount_centavos)
        return f"\u20b1{fee / 100:,.2f}"

    def total_centavos(self, amount_centavos: int) -> int:
        return amount_centavos + self.fee_centavos(amount_centavos)


PLANS: dict[str, ProtectionPlan] = {
    "basic": ProtectionPlan(
        id="basic",
        name="Basic",
        icon="\U0001f6e1\ufe0f",
        tagline="Simple protection for small, trusted deals",
        perks=(
            "3 evidence photos required",
            "48-hour buyer review window",
            "Liveness-verified photos",
            "\u20b115 flat service fee",
        ),
        min_photos=3,
        review_hours=48,
        requires_tracking=False,
        requires_gps=False,
        fee_type="flat",
        flat_fee_centavos=1_500,
        percent_fee=0.0,
        min_fee_centavos=0,
        badge_cls="tier-badge tier-standard",
        badge_icon="\U0001f6e1\ufe0f",
        recommended_above_centavos=0,
    ),
    "standard": ProtectionPlan(
        id="standard",
        name="Standard",
        icon="\U0001f512",
        tagline="Stronger evidence chain with courier tracking",
        perks=(
            "5 liveness-verified photos",
            "Courier tracking number required",
            "72-hour buyer review window",
            "Flat \u20b129 service fee",
        ),
        min_photos=5,
        review_hours=72,
        requires_tracking=True,
        requires_gps=False,
        fee_type="flat",
        flat_fee_centavos=2_900,
        percent_fee=0.0,
        min_fee_centavos=0,
        badge_cls="tier-badge tier-enhanced",
        badge_icon="\U0001f512",
        recommended_above_centavos=100_000,   # ₱1,000
    ),
    "premium": ProtectionPlan(
        id="premium",
        name="Premium",
        icon="\U0001f3e6",
        tagline="Maximum protection for high-value or critical deals",
        perks=(
            "7 GPS-verified liveness photos",
            "Courier tracking required",
            "96-hour buyer review window (4 days)",
            "Priority dispute resolution",
            "1.5% service fee",
        ),
        min_photos=7,
        review_hours=96,
        requires_tracking=True,
        requires_gps=True,
        fee_type="percent",
        flat_fee_centavos=0,
        percent_fee=0.015,
        min_fee_centavos=4_900,   # ₱49 minimum
        badge_cls="tier-badge tier-highvalue",
        badge_icon="\U0001f3e6",
        recommended_above_centavos=500_000,   # ₱5,000
    ),
}

DEFAULT_PLAN = PLANS["basic"]


def get_plan(plan_id: str) -> ProtectionPlan:
    return PLANS.get(plan_id, DEFAULT_PLAN)


def suggested_plan(amount_centavos: int) -> str:
    """Return the plan ID we'd recommend for a given amount."""
    if amount_centavos >= PLANS["premium"].recommended_above_centavos:
        return "premium"
    if amount_centavos >= PLANS["standard"].recommended_above_centavos:
        return "standard"
    return "basic"


# Backward-compat alias used by deal_detail / verification
def get_tier(amount_centavos: int) -> ProtectionPlan:
    """Return the suggested plan for an amount (used when no explicit plan stored)."""
    return PLANS[suggested_plan(amount_centavos)]

import io
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from PIL import Image
from PIL.ExifTags import TAGS

from core.exceptions import VerificationFailed
from core.tiers import get_tier

logger = logging.getLogger(__name__)

# Editing software that proves the image was post-processed
_EDITING_SOFTWARE = {
    "adobe photoshop", "lightroom", "gimp", "affinity photo",
    "snapseed", "vsco", "facetune", "meitu", "picsart",
    "canva", "pixlr", "fotor", "photodirector",
}

# Camera firmware keywords that prove a real phone/camera took this
_CAMERA_FIRMWARE_HINTS = {
    "samsung", "apple", "huawei", "xiaomi", "oppo", "vivo",
    "realme", "oneplus", "sony", "canon", "nikon", "fujifilm",
}


# ── Liveness result ────────────────────────────────────────────────────────

@dataclass
class LivenessResult:
    passed: bool
    score: int                   # 0–100; higher = more trustworthy
    flags: list[str] = field(default_factory=list)    # rejection reasons
    signals: list[str] = field(default_factory=list)  # positive signals found

    def __str__(self) -> str:
        if self.passed:
            return f"Liveness OK (score={self.score}) — {', '.join(self.signals) or 'basic checks passed'}"
        return f"Liveness FAIL (score={self.score}) — {'; '.join(self.flags)}"


# ── Core liveness check ────────────────────────────────────────────────────

def check_photo_liveness(
    image_bytes: bytes,
    transaction_created_at: datetime,
    *,
    require_gps: bool = False,
    require_camera_model: bool = False,
    max_age_hours: int = 24,
) -> LivenessResult:
    """
    Analyse an image's EXIF metadata to score how likely it was taken live
    on a real camera, right now — not downloaded from the internet or taken years ago.

    Returns a LivenessResult. Does NOT raise; callers decide what to do with score.
    """
    flags: list[str] = []
    signals: list[str] = []
    score = 0

    # ── 1. Can we open and read EXIF? ─────────────────────────────────────
    try:
        img = Image.open(io.BytesIO(image_bytes))
        raw_exif = img._getexif()  # type: ignore[attr-defined]
    except Exception as e:
        return LivenessResult(passed=False, score=0,
                              flags=[f"Cannot read image file: {e}"])

    if not raw_exif:
        return LivenessResult(
            passed=False, score=0,
            flags=["No EXIF data — photo was likely downloaded from the internet or screenshot taken"],
        )

    exif: dict = {TAGS.get(k, k): v for k, v in raw_exif.items()}
    score += 10  # has EXIF at all
    signals.append("has EXIF")

    # ── 2. Timestamp freshness ─────────────────────────────────────────────
    date_str: str | None = exif.get("DateTimeOriginal") or exif.get("DateTime")

    if not date_str:
        flags.append("EXIF timestamp missing — cannot verify when photo was taken")
    else:
        try:
            photo_taken = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S").replace(
                tzinfo=timezone.utc
            )
            created_at = transaction_created_at.replace(tzinfo=timezone.utc)
            age_hours = abs((photo_taken - created_at).total_seconds()) / 3600

            if age_hours <= max_age_hours:
                score += 40
                signals.append(f"taken {age_hours:.1f}h ago (within window)")
            elif age_hours <= max_age_hours * 2:
                score += 10
                flags.append(f"photo is {age_hours:.1f}h old — outside the {max_age_hours}h window")
            else:
                flags.append(
                    f"photo taken {age_hours / 24:.1f} days ago — "
                    f"must be within {max_age_hours}h of deal creation"
                )
        except ValueError:
            flags.append(f"EXIF timestamp format unreadable: '{date_str}'")

    # ── 3. Camera make / model ─────────────────────────────────────────────
    make  = str(exif.get("Make",  "") or "").strip()
    model = str(exif.get("Model", "") or "").strip()

    if make or model:
        score += 20
        signals.append(f"camera: {make} {model}".strip())

        # Check for real phone/camera brand
        combo = (make + " " + model).lower()
        if any(hint in combo for hint in _CAMERA_FIRMWARE_HINTS):
            score += 5
            signals.append("recognised device brand")
    else:
        if require_camera_model:
            flags.append("Camera make/model missing — screenshots and web images usually lack this")

    # ── 4. Editing software detection ─────────────────────────────────────
    software = str(exif.get("Software", "") or "").lower()
    if software:
        matched = next((s for s in _EDITING_SOFTWARE if s in software), None)
        if matched:
            score -= 30
            flags.append(f"Image edited with '{matched}' — post-processed photos not accepted")
        else:
            signals.append(f"software: {software[:40]}")

    # ── 5. GPS presence ───────────────────────────────────────────────────
    gps_info = exif.get("GPSInfo")
    if gps_info:
        score += 15
        signals.append("GPS location embedded")
    else:
        if require_gps:
            flags.append(
                "GPS location missing — enable location access in your camera app and retake the photo"
            )

    # ── 6. Camera technical fields (ISO, flash, focal length) ─────────────
    technical = [k for k in ("ISOSpeedRatings", "Flash", "FocalLength", "ExposureTime") if exif.get(k) is not None]
    if len(technical) >= 2:
        score += 10
        signals.append(f"camera metadata ({', '.join(technical)})")

    # ── Clamp score ────────────────────────────────────────────────────────
    score = max(0, min(100, score))

    # A photo passes if: timestamp check passed AND no hard flags (editing software)
    timestamp_ok = not any("days ago" in f or "outside the" in f or "missing" in f.lower() and "timestamp" in f.lower() for f in flags)
    edited = any("edited with" in f for f in flags)
    gps_missing = any("GPS location missing" in f for f in flags)
    model_missing = any("make/model missing" in f for f in flags)

    hard_fail = edited or (require_gps and gps_missing) or (require_camera_model and model_missing) or not timestamp_ok
    passed = not hard_fail and score >= 30

    logger.info(
        "Liveness check score=%d passed=%s flags=%s signals=%s",
        score, passed, flags, signals,
    )
    return LivenessResult(passed=passed, score=score, flags=flags, signals=signals)


# ── Tier-aware photo verification ─────────────────────────────────────────

def verify_photo_liveness(
    image_bytes: bytes,
    transaction_created_at: datetime,
    amount_centavos: int,
) -> LivenessResult:
    """
    Run liveness check with requirements scaled to the deal's security tier.

    Tier 1 (< ₱5k):   EXIF + timestamp required
    Tier 2 (₱5k-₱25k): + camera make/model required
    Tier 3 (> ₱25k):   + GPS required
    """
    tier = get_tier(amount_centavos)

    result = check_photo_liveness(
        image_bytes,
        transaction_created_at,
        require_gps=(tier.tier >= 3),
        require_camera_model=(tier.tier >= 2),
        max_age_hours=24,
    )

    if not result.passed:
        raise VerificationFailed(
            f"[{tier.label}] Photo failed liveness check — {'; '.join(result.flags)}"
        )

    return result


# ── Legacy alias (kept for callers that already import this) ───────────────

def verify_photo_exif(image_bytes: bytes, transaction_created_at: datetime) -> None:
    """Backward-compatible wrapper — runs Tier 1 liveness check."""
    check_photo_liveness(
        image_bytes,
        transaction_created_at,
        require_gps=False,
        require_camera_model=False,
        max_age_hours=24,
    )


# ── Unboxing video gate ────────────────────────────────────────────────────

def verify_unboxing_video(video_url: str | None) -> None:
    if not video_url or not video_url.strip():
        raise VerificationFailed("Unboxing video URL is missing — cannot release funds")


# ── Evidence completeness ──────────────────────────────────────────────────

def check_evidence_complete(
    photo_urls: list[str],
    unboxing_video_url: str | None,
    min_photos: int = 3,
) -> None:
    """Gate check before escrow release: photos + unboxing video."""
    if len(photo_urls) < min_photos:
        raise VerificationFailed(
            f"Only {len(photo_urls)} photo(s) submitted — {min_photos} required"
        )
    verify_unboxing_video(unboxing_video_url)


# ── Tier-aware release gate ────────────────────────────────────────────────

def check_release_gate(
    photo_urls: list[str],
    unboxing_video_url: str | None,
    delivery_tracking_id: str | None,
    amount_centavos: int,
) -> None:
    """
    Tier-aware release gate. Raises VerificationFailed if any requirement unmet.
    Call this before release_escrow().
    """
    tier = get_tier(amount_centavos)

    if len(photo_urls) < tier.min_photos:
        raise VerificationFailed(
            f"[{tier.label}] {len(photo_urls)} photo(s) uploaded — "
            f"{tier.min_photos} required for deals this size"
        )

    verify_unboxing_video(unboxing_video_url)

    if tier.requires_tracking and not delivery_tracking_id:
        raise VerificationFailed(
            f"[{tier.label}] A courier tracking number is required "
            f"for deals above ₱5,000"
        )

import io
from datetime import datetime, timezone

from PIL import Image
from PIL.ExifTags import TAGS

from core.exceptions import VerificationFailed

# Maximum age of a photo's EXIF timestamp to be considered "live"
_MAX_PHOTO_AGE_HOURS = 24


def verify_photo_exif(image_bytes: bytes, transaction_created_at: datetime) -> None:
    """
    Validate that a seller's evidence photo:
    - Contains EXIF data (not a stock/downloaded image)
    - Was taken within _MAX_PHOTO_AGE_HOURS of the transaction creation
    Raises VerificationFailed on any check failure.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        exif_data = img._getexif()  # type: ignore[attr-defined]
    except Exception as e:
        raise VerificationFailed(f"Could not read image: {e}") from e

    if not exif_data:
        raise VerificationFailed("Image has no EXIF data — likely a downloaded/stock photo")

    exif = {TAGS.get(k, k): v for k, v in exif_data.items()}
    date_str: str | None = exif.get("DateTimeOriginal") or exif.get("DateTime")

    if not date_str:
        raise VerificationFailed("EXIF data missing DateTimeOriginal — cannot verify photo age")

    try:
        photo_taken = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S").replace(
            tzinfo=timezone.utc
        )
    except ValueError as e:
        raise VerificationFailed(f"Could not parse EXIF date '{date_str}': {e}") from e

    created_at = transaction_created_at.replace(tzinfo=timezone.utc)
    age_hours = abs((photo_taken - created_at).total_seconds()) / 3600

    if age_hours > _MAX_PHOTO_AGE_HOURS:
        raise VerificationFailed(
            f"Photo is {age_hours:.1f}h old — must be taken within {_MAX_PHOTO_AGE_HOURS}h of transaction"
        )


def verify_unboxing_video(video_url: str | None) -> None:
    """
    Confirm an unboxing video URL is present before releasing escrow.
    """
    if not video_url or not video_url.strip():
        raise VerificationFailed("Unboxing video URL is missing — cannot release funds")


def check_evidence_complete(
    photo_urls: list[str],
    unboxing_video_url: str | None,
    min_photos: int = 3,
) -> None:
    """
    Gate check before triggering escrow release:
    - At least `min_photos` evidence photos submitted
    - Unboxing video present
    """
    if len(photo_urls) < min_photos:
        raise VerificationFailed(
            f"Only {len(photo_urls)} photo(s) submitted — {min_photos} required"
        )
    verify_unboxing_video(unboxing_video_url)

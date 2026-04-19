"""
Supabase Storage helpers for evidence photos and unboxing videos.

Bucket setup (run once in Supabase dashboard or via migration):
  - Bucket name: evidence  (or set STORAGE_BUCKET env var)
  - Public bucket: yes  (read access for everyone)
  - Allowed MIME types: image/jpeg, image/png, image/webp, video/mp4, video/quicktime
  - Max file size: 50 MB
"""
import logging
import mimetypes
import uuid
from pathlib import Path

from lib.config import get_config
from lib.supabase_client import get_supabase_admin

logger = logging.getLogger(__name__)

# Allowed MIME types per upload category
_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm"}


def _content_type(filename: str, allowed: set[str], fallback: str) -> str:
    ext = Path(filename).suffix.lower()
    ct  = mimetypes.types_map.get(ext, fallback)
    if ct not in allowed:
        raise ValueError(
            f"File '{filename}' has unsupported type '{ct}'. "
            f"Allowed: {', '.join(sorted(allowed))}"
        )
    return ct


async def upload_evidence_photo(
    file_bytes: bytes,
    filename: str,
    tx_id: str,
) -> str:
    """Upload one evidence photo. Returns the public URL (mock or real)."""
    cfg = get_config()

    ext = Path(filename).suffix.lower() or ".jpg"
    storage_path = f"{tx_id}/photos/{uuid.uuid4().hex}{ext}"

    if cfg.mock_uploads:
        url = f"https://mock-storage.teluka.dev/{storage_path}"
        logger.info("[MOCK] Evidence photo tx=%s url=%s", tx_id, url)
        return url

    ct = _content_type(filename, _PHOTO_TYPES, "image/jpeg")
    supabase = await get_supabase_admin()
    await supabase.storage.from_(cfg.storage_bucket).upload(
        storage_path,
        file_bytes,
        file_options={"content-type": ct, "upsert": "false"},
    )
    url = supabase.storage.from_(cfg.storage_bucket).get_public_url(storage_path)
    logger.info("Uploaded evidence photo tx=%s path=%s", tx_id, storage_path)
    return url


async def upload_unboxing_video(
    file_bytes: bytes,
    filename: str,
    tx_id: str,
) -> str:
    """Upload an unboxing video. Returns the public URL (mock or real)."""
    cfg = get_config()

    ext = Path(filename).suffix.lower() or ".mp4"
    storage_path = f"{tx_id}/unboxing{ext}"

    if cfg.mock_uploads:
        url = f"https://mock-storage.teluka.dev/{storage_path}"
        logger.info("[MOCK] Unboxing video tx=%s url=%s", tx_id, url)
        return url

    ct = _content_type(filename, _VIDEO_TYPES, "video/mp4")
    supabase = await get_supabase_admin()
    await supabase.storage.from_(cfg.storage_bucket).upload(
        storage_path,
        file_bytes,
        file_options={"content-type": ct, "upsert": "true"},
    )
    url = supabase.storage.from_(cfg.storage_bucket).get_public_url(storage_path)
    logger.info("Uploaded unboxing video tx=%s path=%s", tx_id, storage_path)
    return url

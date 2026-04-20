"""
Supabase Storage helpers for evidence photos and unboxing videos.

Bucket setup (run once in Supabase dashboard or via migration):
  - Bucket name: evidence  (or set STORAGE_BUCKET env var)
  - Public bucket: yes  (read access for everyone)
  - Allowed MIME types: image/jpeg, image/png, image/webp, video/mp4, video/quicktime
  - Max file size: 50 MB
"""
import asyncio
import io
import logging
import mimetypes
import uuid
from pathlib import Path

from lib.config import get_config
from lib.supabase_client import get_supabase_admin

logger = logging.getLogger(__name__)


def _sanitize_image_sync(file_bytes: bytes, max_px: int) -> bytes:
    """
    Re-render image pixel-by-pixel through PIL and save as plain JPEG.
    This destroys polyglot payloads, malicious EXIF, and ImageTragick-style
    exploits — only raw RGB pixel values survive the transcode.
    Runs in a thread (CPU-bound).
    """
    from PIL import Image
    img = Image.open(io.BytesIO(file_bytes))
    img.verify()                            # raises on corrupt/malicious headers
    img = Image.open(io.BytesIO(file_bytes))  # reopen — verify() closes the file
    img = img.convert("RGB")               # strip alpha channel + normalise mode
    if max(img.size) > max_px:
        img.thumbnail((max_px, max_px), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=85, optimize=True)
    return out.getvalue()


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


async def upload_avatar(file_bytes: bytes, user_id: str) -> str:
    """
    Upload/replace a profile avatar.
    Always re-encodes to JPEG 600px max — no malicious payload survives.
    Returns the public URL.
    """
    cfg = get_config()
    if len(file_bytes) > 2 * 1024 * 1024:
        raise ValueError("Avatar must be under 2 MB.")
    clean = await asyncio.to_thread(_sanitize_image_sync, file_bytes, 600)
    path = f"avatars/{user_id}.jpg"
    if cfg.mock_uploads:
        logger.info("[MOCK] Avatar upload user=%s", user_id)
        return f"https://mock-storage.teluka.dev/{path}"
    supabase = await get_supabase_admin()
    await supabase.storage.from_("avatars").upload(
        path, clean,
        file_options={"content-type": "image/jpeg", "upsert": "true"},
    )
    url = supabase.storage.from_("avatars").get_public_url(path)
    logger.info("Avatar uploaded user=%s", user_id)
    return url


async def upload_trust_photo(file_bytes: bytes, user_id: str) -> str:
    """
    Upload a real-time trust photo captured from the device camera.
    Re-encodes to JPEG 800px max. Returns the public URL.
    """
    cfg = get_config()
    if len(file_bytes) > 5 * 1024 * 1024:
        raise ValueError("Trust photo must be under 5 MB.")
    clean = await asyncio.to_thread(_sanitize_image_sync, file_bytes, 800)
    path = f"trust-photos/{user_id}/{uuid.uuid4().hex}.jpg"
    if cfg.mock_uploads:
        logger.info("[MOCK] Trust photo upload user=%s", user_id)
        return f"https://mock-storage.teluka.dev/{path}"
    supabase = await get_supabase_admin()
    await supabase.storage.from_("trust-photos").upload(
        path, clean,
        file_options={"content-type": "image/jpeg", "upsert": "false"},
    )
    url = supabase.storage.from_("trust-photos").get_public_url(path)
    logger.info("Trust photo uploaded user=%s", user_id)
    return url

"""Image compression utility — resizes and compresses uploaded images to WebP."""

from PIL import Image
import io
import os
import logging

logger = logging.getLogger(__name__)

MAX_DIMENSION = 800  # Max width or height in pixels
QUALITY = 82         # WebP quality (0-100)


def compress_and_save(file_obj, dest_dir: str, base_name: str, max_dim: int = MAX_DIMENSION, quality: int = QUALITY) -> str:
    """
    Read an uploaded file, resize if larger than max_dim, save as compressed WebP.
    Returns the saved filename (with .webp extension).
    """
    os.makedirs(dest_dir, exist_ok=True)

    try:
        img = Image.open(file_obj)

        # Convert RGBA → RGB (WebP supports alpha, but JPEG-sourced images are RGB)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Resize if too large
        w, h = img.size
        if w > max_dim or h > max_dim:
            ratio = min(max_dim / w, max_dim / h)
            new_size = (int(w * ratio), int(h * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            logger.info(f"🖼️ Resized {w}x{h} → {new_size[0]}x{new_size[1]}")

        # Save as WebP
        filename = f"{base_name}.webp"
        filepath = os.path.join(dest_dir, filename)
        img.save(filepath, "WEBP", quality=quality, optimize=True)

        file_size_kb = os.path.getsize(filepath) / 1024
        logger.info(f"🖼️ Compressed → {filename} ({file_size_kb:.0f} KB)")

        return filename

    except Exception as e:
        logger.warning(f"🖼️ Compression failed, saving raw: {e}")
        # Fallback: save raw file
        filename = f"{base_name}.jpg"
        filepath = os.path.join(dest_dir, filename)
        file_obj.seek(0)
        with open(filepath, "wb") as f:
            f.write(file_obj.read())
        return filename

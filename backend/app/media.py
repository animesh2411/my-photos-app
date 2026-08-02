"""
Media handling for PhotoBridge.
Generates thumbnails and streams files with HTTP range request support.
"""

import os
import hashlib
import mimetypes
from io import BytesIO
from fastapi import HTTPException
from fastapi.responses import StreamingResponse, FileResponse

try:
    from PIL import Image
except ImportError:
    Image = None

# Register pillow-heif to handle HEIC/HEIF files
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass  # pillow-heif not installed

# Thumbnail cache directory
THUMB_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.thumbcache')


def _thumb_cache_path(file_path: str, width: int) -> str:
    """Get the cache file path for a thumbnail."""
    mtime = os.path.getmtime(file_path)
    key = f"{file_path}|{width}|{mtime}"
    digest = hashlib.md5(key.encode()).hexdigest()
    return os.path.join(THUMB_CACHE_DIR, digest[:2], f"{digest}.jpg")


def generate_thumbnail(file_path: str, width: int = 300) -> bytes:
    """
    Generate a JPEG thumbnail with disk caching.
    Cached thumbnails are served directly from disk on subsequent requests.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if Image is None:
        raise ValueError("Pillow not installed")

    # Check cache first
    cache_path = _thumb_cache_path(file_path, width)
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            return f.read()

    try:
        img = Image.open(file_path)
        img.thumbnail((width, width), Image.Resampling.LANCZOS)

        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (0, 0, 0))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img

        output = BytesIO()
        img.save(output, format='JPEG', quality=80)
        thumb_data = output.getvalue()

        # Save to cache
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, 'wb') as f:
            f.write(thumb_data)

        return thumb_data
    except Exception as e:
        print(f"Warning: Failed to generate thumbnail for {file_path}: {e}")
        with open(file_path, 'rb') as f:
            return f.read()


def clear_thumb_cache():
    """
    Delete all generated thumbnails in .thumbcache directory.
    Automatically called when server stops to keep disk clean.
    """
    if os.path.exists(THUMB_CACHE_DIR):
        try:
            import shutil
            shutil.rmtree(THUMB_CACHE_DIR, ignore_errors=True)
            print("[INFO] Cleaned up .thumbcache directory.")
        except Exception as e:
            print(f"[WARNING] Could not clear thumbcache: {e}")


def get_range_response(file_path: str, range_header: str | None) -> StreamingResponse | FileResponse:
    """
    Stream a file, supporting HTTP range requests for seeking in videos.

    Args:
        file_path: Absolute path to the file
        range_header: The Range header value (if present), e.g. "bytes=1000-2000"

    Returns:
        StreamingResponse or FileResponse with appropriate headers
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = os.path.getsize(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'

    # If no range header, return the full file
    if not range_header:
        return FileResponse(
            file_path,
            media_type=mime_type,
            headers={
                'Accept-Ranges': 'bytes',
                'Cache-Control': 'private, no-store, must-revalidate'
            }
        )

    # Parse range header (e.g. "bytes=0-999" or "bytes=1000-")
    try:
        if not range_header.startswith('bytes='):
            raise ValueError("Invalid range format")

        range_spec = range_header[6:]

        if '-' not in range_spec:
            raise ValueError("Invalid range format")

        start, end = range_spec.split('-', 1)

        start = int(start) if start else 0
        end = int(end) if end else file_size - 1

        if start < 0 or end >= file_size or start > end:
            raise ValueError("Invalid range values")

        # Return 206 Partial Content
        def file_iterator():
            with open(file_path, 'rb') as f:
                f.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk_size = min(8192, remaining)
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        return StreamingResponse(
            file_iterator(),
            status_code=206,
            media_type=mime_type,
            headers={
                'Content-Range': f'bytes {start}-{end}/{file_size}',
                'Content-Length': str(end - start + 1),
                'Accept-Ranges': 'bytes',
                'Cache-Control': 'private, no-store, must-revalidate'
            }
        )
    except (ValueError, IndexError):
        # Fall back to full file on invalid range
        return FileResponse(
            file_path,
            media_type=mime_type,
            headers={
                'Accept-Ranges': 'bytes',
                'Cache-Control': 'private, no-store, must-revalidate'
            }
        )


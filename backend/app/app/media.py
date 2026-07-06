"""
Media handling for PhotoBridge.
Generates thumbnails and streams files with HTTP range request support.
"""

import os
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


def generate_thumbnail(file_path: str, width: int = 300) -> bytes:
    """
    Generate a JPEG thumbnail for an image.

    Args:
        file_path: Absolute path to the image file
        width: Longer side dimension in pixels (default 300)

    Returns:
        JPEG bytes, or the original file if thumbnail generation fails

    Raises:
        FileNotFoundError: if file doesn't exist
        ValueError: if not an image
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if Image is None:
        raise ValueError("Pillow not installed")

    try:
        img = Image.open(file_path)

        # Calculate thumbnail size
        img.thumbnail((width, width), Image.Resampling.LANCZOS)

        # Convert to RGB if necessary (e.g. for RGBA or palette images)
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (0, 0, 0))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img

        # Save as JPEG
        output = BytesIO()
        img.save(output, format='JPEG', quality=85)
        output.seek(0)
        return output.getvalue()
    except Exception as e:
        # Fall back to original file if thumbnail generation fails
        print(f"Warning: Failed to generate thumbnail for {file_path}: {e}")
        with open(file_path, 'rb') as f:
            return f.read()


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
                'Cache-Control': 'public, max-age=3600'
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
                'Cache-Control': 'public, max-age=3600'
            }
        )
    except (ValueError, IndexError):
        # Fall back to full file on invalid range
        return FileResponse(
            file_path,
            media_type=mime_type,
            headers={
                'Accept-Ranges': 'bytes',
                'Cache-Control': 'public, max-age=3600'
            }
        )


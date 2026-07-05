"""
FastAPI backend for PhotoBridge.
Serves the photo grid API and static frontend files.
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
import os
import socket
import mimetypes

from app.config import get_config, set_photos_dir, get_port_from_env
from app.scanner import MediaIndex, decode_id
from app.media import generate_thumbnail, get_range_response


app = FastAPI(title="PhotoBridge")

# Global media index
media_index = MediaIndex()


# ============================================================================
# Pydantic models
# ============================================================================

class ConfigRequest(BaseModel):
    photos_dir: str


class ConfigResponse(BaseModel):
    photos_dir: str | None
    port: int
    configured: bool


# ============================================================================
# Utility functions
# ============================================================================

def get_laptop_lan_ip() -> str:
    """
    Get the LAN IP address of this machine for local network access.
    Returns "localhost" if unable to determine.
    """
    try:
        # Connect to a public DNS to figure out our LAN IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


def print_startup_banner():
    """Print the startup banner with local and LAN URLs."""
    port = get_port_from_env()
    config = get_config()

    lan_ip = get_laptop_lan_ip()

    photos_folder_status = (
        f"not yet configured — open the app and complete setup"
        if not config["configured"]
        else f"{config['photos_dir']}"
    )

    print("\n" + "=" * 70)
    print("PhotoBridge running!")
    print(f"Local:  http://localhost:{port}")
    print(f"Phone:  http://{lan_ip}:{port}   (same WiFi)")
    print(f"Photos folder: {photos_folder_status}")
    print("=" * 70 + "\n")


# ============================================================================
# API Endpoints: Configuration
# ============================================================================

@app.get("/api/config", response_model=ConfigResponse)
async def api_get_config():
    """Get the current configuration (photos_dir and port)."""
    config = get_config()
    return ConfigResponse(
        photos_dir=config["photos_dir"],
        port=config["port"],
        configured=config["configured"]
    )


@app.post("/api/config", response_model=ConfigResponse)
async def api_set_config(request: ConfigRequest):
    """
    Set the photos directory.
    Validates that the path exists, saves to config.json, and rescans.
    """
    try:
        config = set_photos_dir(request.photos_dir)

        # Rescan the new directory
        media_index.photos_dir = request.photos_dir
        media_index.rescan()

        return ConfigResponse(
            photos_dir=config["photos_dir"],
            port=config["port"],
            configured=config["configured"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# API Endpoints: Media
# ============================================================================

@app.get("/api/media")
async def api_get_media():
    """Get the full list of media objects (photos and videos)."""
    return media_index.get_all_media()


@app.post("/api/rescan")
async def api_rescan():
    """Rescan the photos directory and rebuild the index."""
    config = get_config()
    if not config["configured"]:
        raise HTTPException(
            status_code=400,
            detail="Photos directory not configured yet"
        )

    media_index.rescan()
    return {"count": len(media_index.media)}


# ============================================================================
# API Endpoints: Media Files
# ============================================================================

@app.get("/api/thumb/{media_id}")
async def api_thumbnail(media_id: str, w: int = 300):
    """
    Get a thumbnail for a media file.
    For images: returns JPEG thumbnail resized to w pixels on the longer side.
    For videos: returns 204 No Content (frontend shows placeholder).
    """
    media = media_index.get_media_by_id(media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    # Videos don't get thumbnails
    if media["type"] == "video":
        return StreamingResponse(b'', status_code=204)

    file_path = media_index.get_file_path(media_id)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        thumbnail_data = generate_thumbnail(file_path, w)
        return StreamingResponse(
            iter([thumbnail_data]),
            media_type="image/jpeg",
            headers={
                "Cache-Control": "public, max-age=86400",
                "Content-Length": str(len(thumbnail_data))
            }
        )
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate thumbnail")


@app.get("/api/full/{media_id}")
async def api_full_media(media_id: str, range: str = Header(None)):
    """
    Stream the original media file.
    Supports HTTP range requests for video seeking.
    """
    media = media_index.get_media_by_id(media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    file_path = media_index.get_file_path(media_id)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return get_range_response(file_path, range)


@app.get("/api/download/{media_id}")
async def api_download_media(media_id: str, range: str = Header(None)):
    """
    Download/stream the media file with attachment disposition.
    Supports HTTP range requests.
    Used by the "Save to Photos" button in the viewer.
    """
    media = media_index.get_media_by_id(media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    file_path = media_index.get_file_path(media_id)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    response = get_range_response(file_path, range)
    response.headers["Content-Disposition"] = f'attachment; filename="{media["filename"]}"'
    return response


# ============================================================================
# Static files
# ============================================================================

# Mount static files (frontend) at the root, with index.html as the default
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


# ============================================================================
# Startup event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    On startup:
    1. Initialize media index with configured photos_dir
    2. Print startup banner with LAN URL
    """
    from app.config import ensure_config_exists
    ensure_config_exists()

    config = get_config()
    if config["configured"]:
        media_index.photos_dir = config["photos_dir"]
        media_index.rescan()

    print_startup_banner()




"""
FastAPI backend for PhotoBridge.
Serves the photo grid API and static frontend files.
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
import os
import socket
import mimetypes
import asyncio
import tkinter as tk
from tkinter import filedialog

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
    access_pin: str | None = None


class ConfigResponse(BaseModel):
    photos_dir: str | None
    port: int
    configured: bool
    pin_required: bool


# ============================================================================
# Utility functions
# ============================================================================

def get_lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


from fastapi import Request, Header, HTTPException, status
from app.config import set_access_pin

def verify_local_request(request: Request):
    """Ensure configuration endpoints are only called from localhost."""
    client_host = request.client.host
    if client_host not in ("127.0.0.1", "localhost", "::1"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Configuration changes are only allowed from the host laptop (localhost)"
        )

def verify_access_pin(x_photobridge_pin: str = Header(None), pin: str = None):
    """Validate access PIN if configured, supporting both custom header and query string."""
    config = get_config()
    if config["pin_required"]:
        expected = config["access_pin"]
        provided = x_photobridge_pin or pin
        if not provided or provided != expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing Access PIN"
            )


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
        configured=config["configured"],
        pin_required=config["pin_required"]
    )


@app.post("/api/config", response_model=ConfigResponse)
async def api_set_config(request: ConfigRequest, req: Request):
    """
    Set the photos directory and optional access PIN.
    Validates that the path exists, saves to config.json, and rescans.
    """
    verify_local_request(req)
    try:
        config = set_photos_dir(request.photos_dir)
        config = set_access_pin(request.access_pin)

        # Rescan the new directory
        media_index.photos_dir = request.photos_dir
        media_index.rescan()

        return ConfigResponse(
            photos_dir=config["photos_dir"],
            port=config["port"],
            configured=config["configured"],
            pin_required=config["pin_required"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _open_folder_dialog() -> str | None:
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        root.focus_force()
        selected_dir = filedialog.askdirectory(title="Select Photos Folder")
        root.destroy()
        return selected_dir if selected_dir else None
    except Exception as e:
        print("Error in native folder dialog:", e)
        return None


@app.post("/api/select-folder")
async def api_select_folder(req: Request):
    """
    Open a native folder selection dialog on the server (laptop)
    and return the selected path.
    """
    verify_local_request(req)
    try:
        selected_dir = await asyncio.to_thread(_open_folder_dialog)
        if selected_dir:
            return {"path": os.path.abspath(selected_dir)}
        return {"path": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open folder picker: {str(e)}")


# ============================================================================
# API Endpoints: Media
# ============================================================================

@app.get("/api/albums")
async def api_get_albums(dependencies=Depends(verify_access_pin)):
    """Get the list of albums (top-level subfolders) with their file counts."""
    return media_index.get_albums()


@app.get("/api/media")
async def api_get_media(
    album: str = None,
    offset: int = 0,
    limit: int = 100,
    dependencies=Depends(verify_access_pin)
):
    """
    Get media objects with pagination.
    - ?album=<name>&offset=0&limit=100 → paginated results for that album (lazy scan on first call).
    - Without album param → scans All Photos album.
    Returns: {items: [...], total: int, has_more: bool, offset: int}
    """
    album_name = album if album else "All Photos"
    return media_index.get_album_page(album_name, offset=offset, limit=limit)


@app.post("/api/rescan")
async def api_rescan(album: str = None, dependencies=Depends(verify_access_pin)):
    """
    Rescan the photos directory.
    - If ?album=<name>, clears cache for that album only (fast).
    - Without param, re-indexes all album folders (still fast — no file scanning).
    """
    config = get_config()
    if not config["configured"]:
        raise HTTPException(
            status_code=400,
            detail="Photos directory not configured yet"
        )
    if album:
        media_index.rescan_album(album)
        return {"album": album, "status": "cache cleared"}
    media_index.rescan()
    return {"albums": len(media_index._albums)}


# ============================================================================
# API Endpoints: Media Files
# ============================================================================

@app.get("/api/thumb/{media_id}")
async def api_thumbnail(media_id: str, w: int = 300, dependencies=Depends(verify_access_pin)):
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
async def api_full_media(media_id: str, range: str = Header(None), dependencies=Depends(verify_access_pin)):
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
async def api_download_media(media_id: str, range: str = Header(None), dependencies=Depends(verify_access_pin)):
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
static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


# ============================================================================
# Startup event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    On startup: quickly index album folders only (no file scanning).
    Actual file scanning happens lazily per-album on demand.
    """
    from app.config import ensure_config_exists
    ensure_config_exists()

    config = get_config()
    if config["configured"]:
        media_index.photos_dir = config["photos_dir"]
        # _index_albums() is fast — just reads folder names, no file stat
        media_index._index_albums()




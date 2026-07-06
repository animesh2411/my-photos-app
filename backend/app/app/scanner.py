"""
Filesystem scanner for PhotoBridge.
Walks the photos directory, extracts metadata, and builds an in-memory index.
"""

import os
import base64
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    Image = None
    TAGS = None

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass


# Accepted file types
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".gif", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v"}


def encode_id(rel_path: str) -> str:
    """
    Encode a relative path as a URL-safe base64 string to use as a media ID.
    """
    return base64.urlsafe_b64encode(rel_path.encode()).decode().rstrip("=")


def decode_id(encoded_id: str) -> str:
    """
    Decode a base64-encoded ID back to a relative path.
    """
    # Add back padding if needed
    padding = 4 - (len(encoded_id) % 4)
    if padding != 4:
        encoded_id += "=" * padding
    return base64.urlsafe_b64decode(encoded_id).decode()


def get_exif_date(image_path: str) -> Optional[str]:
    """
    Extract EXIF DateTimeOriginal from an image, with fallbacks.
    Returns ISO 8601 datetime string, or None if unable to read.
    """
    if Image is None:
        return None

    try:
        img = Image.open(image_path)
        exif_data = img._getexif() if hasattr(img, '_getexif') else None

        if exif_data:
            # Try DateTimeOriginal first, then DateTime
            for tag_id, tag_name in TAGS.items():
                if tag_name in ["DateTimeOriginal", "DateTime"]:
                    if tag_id in exif_data:
                        dt_str = exif_data[tag_id]
                        # Convert "2026:07:05 14:30:45" to ISO 8601
                        if isinstance(dt_str, str):
                            try:
                                dt = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                                return dt.isoformat()
                            except:
                                pass

        return None
    except Exception:
        return None


def get_file_date(file_path: str) -> str:
    """
    Get file's modification time as ISO 8601 string (fallback for EXIF or videos).
    """
    try:
        mtime = os.path.getmtime(file_path)
        dt = datetime.fromtimestamp(mtime)
        return dt.isoformat()
    except Exception:
        return datetime.now().isoformat()


def get_media_date(file_path: str, media_type: str) -> str:
    """
    Get the date for a media file (image or video).
    For images: try EXIF, then file mtime.
    For videos: use file mtime.
    """
    if media_type == "image":
        exif_date = get_exif_date(file_path)
        if exif_date:
            return exif_date

    return get_file_date(file_path)


def scan_directory(photos_dir: str) -> List[Dict]:
    """
    Recursively scan the photos directory and build a list of media objects.

    Args:
        photos_dir: Absolute path to the photos directory

    Returns:
        List of media dicts, sorted newest-first by date_taken
    """
    if not os.path.isdir(photos_dir):
        return []

    media_list = []

    for root, dirs, files in os.walk(photos_dir):
        # Determine album name: subdirectory name, or "All Photos" if in root
        if root == photos_dir:
            album = "All Photos"
        else:
            album = os.path.basename(root)

        for filename in files:
            file_path = os.path.join(root, filename)
            file_ext = os.path.splitext(filename)[1].lower()

            # Determine media type
            media_type = None
            if file_ext in IMAGE_EXTENSIONS:
                media_type = "image"
            elif file_ext in VIDEO_EXTENSIONS:
                media_type = "video"
            else:
                continue  # Skip unsupported files

            try:
                # Get file size
                size_bytes = os.path.getsize(file_path)

                # Get media date
                date_taken = get_media_date(file_path, media_type)

                # Compute relative path and ID
                rel_path = os.path.relpath(file_path, photos_dir)
                media_id = encode_id(rel_path)

                media_list.append({
                    "id": media_id,
                    "rel_path": rel_path,
                    "filename": filename,
                    "album": album,
                    "type": media_type,
                    "date_taken": date_taken,
                    "size_bytes": size_bytes
                })
            except Exception as e:
                # Log and skip corrupt/inaccessible files
                print(f"Warning: Could not process {file_path}: {e}")
                continue

    # Pass 2: Identify Live Photos by pairing images with corresponding video files
    # Create a map of video file relative directory + uppercase base name -> video media ID
    videos_by_base = {}
    for item in media_list:
        if item["type"] == "video":
            dir_path = os.path.dirname(item["rel_path"])
            base_name = os.path.splitext(item["filename"])[0].upper()
            videos_by_base[(dir_path, base_name)] = item["id"]

    # Link images to their matching video ID if it exists
    for item in media_list:
        if item["type"] == "image":
            dir_path = os.path.dirname(item["rel_path"])
            base_name = os.path.splitext(item["filename"])[0].upper()
            if (dir_path, base_name) in videos_by_base:
                item["live_video_id"] = videos_by_base[(dir_path, base_name)]

    # Sort newest-first by date_taken
    media_list.sort(key=lambda x: x["date_taken"], reverse=True)

    return media_list


class MediaIndex:
    """
    In-memory index of media files.
    Can be rebuilt on demand to pick up new files.
    """

    def __init__(self, photos_dir: Optional[str] = None):
        self.photos_dir = photos_dir
        self.media = []
        if photos_dir:
            self.rescan()

    def rescan(self):
        """Rebuild the media index from the current photos_dir."""
        if self.photos_dir and os.path.isdir(self.photos_dir):
            self.media = scan_directory(self.photos_dir)
        else:
            self.media = []

    def get_all_media(self) -> List[Dict]:
        """Return the full list of media objects."""
        return self.media

    def get_media_by_id(self, media_id: str) -> Optional[Dict]:
        """Find a media object by its encoded ID."""
        try:
            for media in self.media:
                if media["id"] == media_id:
                    return media
        except Exception:
            pass
        return None

    def get_file_path(self, media_id: str) -> Optional[str]:
        """
        Get the absolute filesystem path for a media ID.
        Returns None if not found or photos_dir not configured.
        """
        if not self.photos_dir:
            return None

        try:
            rel_path = decode_id(media_id)
            file_path = os.path.join(self.photos_dir, rel_path)

            # Ensure the path is actually under photos_dir (security check)
            real_path = os.path.realpath(file_path)
            real_photos_dir = os.path.realpath(self.photos_dir)
            if real_path.startswith(real_photos_dir):
                return file_path
        except Exception:
            pass

        return None

    def get_albums(self) -> List[str]:
        """Return a sorted list of unique album names."""
        albums = set()
        for media in self.media:
            albums.add(media["album"])
        return sorted(albums)

    def filter_by_album(self, album: str) -> List[Dict]:
        """Return all media in a given album."""
        return [m for m in self.media if m["album"] == album]

    def filter_by_filename(self, search: str) -> List[Dict]:
        """Return all media whose filename contains the search string (case-insensitive)."""
        search_lower = search.lower()
        return [m for m in self.media if search_lower in m["filename"].lower()]


"""
Filesystem scanner for PhotoBridge.
Lazy-loading design:
  - Startup: only reads top-level folder names (milliseconds).
  - Per-album: recursively scans one folder tree on first request, caches result.
  - Pagination: caller passes offset+limit to get a page of results.
"""

import os
import base64
from datetime import datetime
from typing import List, Dict, Optional, Tuple

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
MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


def encode_id(rel_path: str) -> str:
    return base64.urlsafe_b64encode(rel_path.encode()).decode().rstrip("=")


def decode_id(encoded_id: str) -> str:
    padding = 4 - (len(encoded_id) % 4)
    if padding != 4:
        encoded_id += "=" * padding
    return base64.urlsafe_b64decode(encoded_id).decode()


def get_exif_date(image_path: str) -> Optional[str]:
    if Image is None:
        return None
    try:
        img = Image.open(image_path)
        exif_data = img._getexif() if hasattr(img, '_getexif') else None
        if exif_data:
            for tag_id, tag_name in TAGS.items():
                if tag_name in ["DateTimeOriginal", "DateTime"]:
                    if tag_id in exif_data:
                        dt_str = exif_data[tag_id]
                        if isinstance(dt_str, str):
                            try:
                                dt = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                                return dt.isoformat()
                            except Exception:
                                pass
        return None
    except Exception:
        return None


def get_file_date(file_path: str) -> str:
    try:
        mtime = os.path.getmtime(file_path)
        return datetime.fromtimestamp(mtime).isoformat()
    except Exception:
        return datetime.now().isoformat()


def get_media_date(file_path: str, media_type: str) -> str:
    if media_type == "image":
        exif_date = get_exif_date(file_path)
        if exif_date:
            return exif_date
    return get_file_date(file_path)


def scan_folder_recursive(photos_dir: str, folder_path: str, album_name: str) -> List[Dict]:
    """
    Recursively scan a folder and all its subfolders.
    Returns a list of media dicts sorted newest-first.
    This is the core scanning function — called lazily per album on first request.
    """
    media_list = []

    for root, dirs, files in os.walk(folder_path):
        # Sort dirs in-place so os.walk visits them in alphabetical order
        dirs.sort()
        for filename in files:
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in IMAGE_EXTENSIONS:
                media_type = "image"
            elif file_ext in VIDEO_EXTENSIONS:
                media_type = "video"
            else:
                continue

            file_path = os.path.join(root, filename)
            try:
                size_bytes = os.path.getsize(file_path)
                date_taken = get_media_date(file_path, media_type)
                rel_path = os.path.relpath(file_path, photos_dir)
                media_id = encode_id(rel_path)

                media_list.append({
                    "id": media_id,
                    "rel_path": rel_path,
                    "filename": filename,
                    "album": album_name,
                    "type": media_type,
                    "date_taken": date_taken,
                    "size_bytes": size_bytes
                })
            except Exception as e:
                print(f"Warning: Could not process {file_path}: {e}")
                continue

    # Link Live Photos (matching image + video by base name)
    videos_by_key = {}
    for item in media_list:
        if item["type"] == "video":
            key = (os.path.dirname(item["rel_path"]), os.path.splitext(item["filename"])[0].upper())
            videos_by_key[key] = item["id"]

    for item in media_list:
        if item["type"] == "image":
            key = (os.path.dirname(item["rel_path"]), os.path.splitext(item["filename"])[0].upper())
            if key in videos_by_key:
                item["live_video_id"] = videos_by_key[key]

    media_list.sort(key=lambda x: x["date_taken"], reverse=True)
    return media_list


def count_media_recursive(folder_path: str) -> int:
    """
    Count media files in a folder tree without reading EXIF.
    Fast — used only for album list counts.
    """
    count = 0
    try:
        for root, dirs, files in os.walk(folder_path):
            for f in files:
                if os.path.splitext(f)[1].lower() in MEDIA_EXTENSIONS:
                    count += 1
    except Exception:
        pass
    return count


class MediaIndex:
    """
    Lazy per-album media index with pagination support.

    Usage:
      - get_albums()                    → instant list of top-level folders + counts
      - get_album_page(name, 0, 100)    → lazily scans folder on first call, returns page
    """

    def __init__(self, photos_dir: Optional[str] = None):
        self.photos_dir = photos_dir
        self._albums: Dict[str, str] = {}          # album_name -> folder abs path
        self._album_cache: Dict[str, List[Dict]] = {}  # album_name -> full sorted list
        self._album_counts: Dict[str, int] = {}    # album_name -> file count (fast estimate)
        self.media: List[Dict] = []                # kept for backward compat

        if photos_dir:
            self._index_albums()

    # ------------------------------------------------------------------
    # Startup: index folder structure only
    # ------------------------------------------------------------------

    def _index_albums(self):
        """
        Read top-level folder names only. O(n_folders), no file I/O.
        Completes in milliseconds even for huge libraries.
        """
        self._albums = {}
        self._album_cache = {}
        self._album_counts = {}
        self.media = []

        if not self.photos_dir or not os.path.isdir(self.photos_dir):
            return

        # Root files → "All Photos" virtual album
        self._albums["All Photos"] = self.photos_dir

        # Each immediate subfolder → its own album
        try:
            for entry in sorted(os.scandir(self.photos_dir), key=lambda e: e.name.lower()):
                if entry.is_dir():
                    self._albums[entry.name] = entry.path
        except PermissionError:
            pass

    # ------------------------------------------------------------------
    # Albums list (with fast recursive counts)
    # ------------------------------------------------------------------

    def get_albums(self) -> List[Dict]:
        """
        Return album list with media counts.
        Counts are cached after first call per album.
        """
        result = []
        for album_name, folder_path in self._albums.items():
            if album_name not in self._album_counts:
                self._album_counts[album_name] = count_media_recursive(folder_path)
            result.append({
                "name": album_name,
                "path": folder_path,
                "count": self._album_counts[album_name]
            })
        return result

    # ------------------------------------------------------------------
    # Per-album lazy scan + pagination
    # ------------------------------------------------------------------

    def _ensure_album_loaded(self, album_name: str):
        """Scan album folder if not already cached."""
        if album_name in self._album_cache:
            return
        if album_name not in self._albums:
            self._album_cache[album_name] = []
            return
        folder_path = self._albums[album_name]
        self._album_cache[album_name] = scan_folder_recursive(
            self.photos_dir, folder_path, album_name
        )

    def get_album_page(self, album_name: str, offset: int = 0, limit: int = 100) -> Dict:
        """
        Return a paginated slice of an album's media.
        Scans the folder tree on first call; subsequent calls use cache.
        Returns: {items: [...], total: int, has_more: bool, offset: int}
        """
        self._ensure_album_loaded(album_name)
        full = self._album_cache.get(album_name, [])
        total = len(full)
        page = full[offset: offset + limit]
        return {
            "items": page,
            "total": total,
            "has_more": (offset + limit) < total,
            "offset": offset
        }

    def get_album_media(self, album_name: str) -> List[Dict]:
        """Return full album media list (backward compat / small albums)."""
        self._ensure_album_loaded(album_name)
        return self._album_cache.get(album_name, [])

    # ------------------------------------------------------------------
    # Rescan
    # ------------------------------------------------------------------

    def rescan(self):
        """Clear all caches and re-index folder structure."""
        self._index_albums()

    def rescan_album(self, album_name: str):
        """Clear cache for one album so it re-scans on next request."""
        self._album_cache.pop(album_name, None)
        self._album_counts.pop(album_name, None)

    # ------------------------------------------------------------------
    # Lookup by ID (for thumbnail/full/download endpoints)
    # ------------------------------------------------------------------

    def get_media_by_id(self, media_id: str) -> Optional[Dict]:
        """
        Find a media object by ID.
        Checks cached albums first, then decodes the ID to find the right folder.
        """
        for media_list in self._album_cache.values():
            for m in media_list:
                if m["id"] == media_id:
                    return m

        if not self.photos_dir:
            return None

        try:
            rel_path = decode_id(media_id)
            file_path = os.path.join(self.photos_dir, rel_path)
            folder_path = os.path.dirname(file_path)

            for album_name, album_path in self._albums.items():
                album_real = os.path.realpath(album_path)
                folder_real = os.path.realpath(folder_path)
                # Match if the file is inside this album's folder tree
                if folder_real.startswith(album_real):
                    self._ensure_album_loaded(album_name)
                    for m in self._album_cache.get(album_name, []):
                        if m["id"] == media_id:
                            return m
        except Exception:
            pass

        return None

    def get_file_path(self, media_id: str) -> Optional[str]:
        if not self.photos_dir:
            return None
        try:
            rel_path = decode_id(media_id)
            file_path = os.path.join(self.photos_dir, rel_path)
            real_path = os.path.realpath(file_path)
            real_photos_dir = os.path.realpath(self.photos_dir)
            if real_path.startswith(real_photos_dir):
                return file_path
        except Exception:
            pass
        return None

    def get_all_media(self) -> List[Dict]:
        """Loads all albums — use only for small libraries."""
        all_media = []
        for album_name in self._albums:
            all_media.extend(self.get_album_media(album_name))
        all_media.sort(key=lambda x: x["date_taken"], reverse=True)
        return all_media

    def filter_by_filename(self, search: str) -> List[Dict]:
        search_lower = search.lower()
        results = []
        for media_list in self._album_cache.values():
            for m in media_list:
                if search_lower in m["filename"].lower():
                    results.append(m)
        return results

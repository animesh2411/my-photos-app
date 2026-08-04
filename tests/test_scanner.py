import os
import pytest
from unittest.mock import patch
from app.scanner import (
    encode_id,
    decode_id,
    scan_folder_recursive,
    count_media_flat,
    MediaIndex
)

def test_id_encoding_decoding():
    original = "subfolder/image_file.heic"
    encoded = encode_id(original)
    assert isinstance(encoded, str)
    assert "=" not in encoded  # should be stripped
    
    decoded = decode_id(encoded)
    assert decoded == original

def test_count_media_flat(tmp_path):
    assert count_media_flat(str(tmp_path)) == 0
    
    # Create valid files
    with open(tmp_path / "img1.jpg", "w") as f: f.write("")
    with open(tmp_path / "vid1.mov", "w") as f: f.write("")
    with open(tmp_path / "other.txt", "w") as f: f.write("")
    
    # Create subfolder
    os.makedirs(tmp_path / "sub")
    with open(tmp_path / "sub" / "img2.png", "w") as f: f.write("")
    
    # Flat count should only count valid files in the root folder, not subdirectories
    assert count_media_flat(str(tmp_path)) == 2

def test_scan_folder_recursive(tmp_path):
    # Setup folders
    photos_dir = str(tmp_path)
    album_path = str(tmp_path / "Album1")
    os.makedirs(album_path)
    
    # Create live photo pair
    with open(tmp_path / "Album1" / "IMG_1234.HEIC", "w") as f: f.write("img")
    with open(tmp_path / "Album1" / "IMG_1234.MOV", "w") as f: f.write("vid")
    
    # Create standard video
    with open(tmp_path / "Album1" / "VID_8888.MP4", "w") as f: f.write("vid")
    
    media = scan_folder_recursive(photos_dir, album_path, "Album1")
    assert len(media) == 3
    
    # Verify live photo pairing
    images = [m for m in media if m["type"] == "image"]
    videos = [m for m in media if m["type"] == "video"]
    assert len(images) == 1
    assert len(videos) == 2
    
    live_image = images[0]
    live_video = [v for v in videos if v["filename"] == "IMG_1234.MOV"][0]
    
    assert live_image["live_video_id"] == live_video["id"]
    assert "live_video_id" not in live_video

def test_media_index_albums(tmp_path):
    photos_dir = str(tmp_path)
    
    # Create directories
    os.makedirs(tmp_path / "Summer 2026")
    os.makedirs(tmp_path / "Winter 2026")
    
    # Add files
    with open(tmp_path / "root_img.jpg", "w") as f: f.write("")
    with open(tmp_path / "Summer 2026" / "s1.png", "w") as f: f.write("")
    with open(tmp_path / "Winter 2026" / "w1.mp4", "w") as f: f.write("")
    
    index = MediaIndex(photos_dir)
    albums = index.get_albums()
    
    # Should have 'All Photos', 'Summer 2026', 'Winter 2026'
    assert len(albums) == 3
    names = [a["name"] for a in albums]
    assert "All Photos" in names
    assert "Summer 2026" in names
    assert "Winter 2026" in names
    
    # Initially counts are uncalculated (-1)
    assert albums[0]["count"] == -1
    
    # Run sync count
    index.count_albums_sync()
    albums = index.get_albums()
    
    all_photos_album = [a for a in albums if a["name"] == "All Photos"][0]
    summer_album = [a for a in albums if a["name"] == "Summer 2026"][0]
    
    assert summer_album["count"] == 1
    assert all_photos_album["count"] == 3  # 1 root + 2 subfolder media

def test_media_index_pagination_and_cache(tmp_path):
    photos_dir = str(tmp_path)
    album_path = tmp_path / "Album"
    os.makedirs(album_path)
    
    for i in range(15):
        with open(album_path / f"img_{i:02d}.jpg", "w") as f:
            f.write("")
            
    index = MediaIndex(photos_dir)
    
    # Verify paginated reading
    page1 = index.get_album_page("Album", offset=0, limit=10)
    assert len(page1["items"]) == 10
    assert page1["total"] == 15
    assert page1["has_more"] is True
    assert page1["offset"] == 0
    
    page2 = index.get_album_page("Album", offset=10, limit=10)
    assert len(page2["items"]) == 5
    assert page2["has_more"] is False
    assert page2["offset"] == 10
    
    # Check full album fetch
    all_media = index.get_album_media("Album")
    assert len(all_media) == 15
    
    # Filter by filename
    results = index.filter_by_filename("img_0")
    assert len(results) == 10  # img_00 to img_09
    
    # Rescan checks
    index.rescan_album("Album")
    assert "Album" not in index._album_cache
    
    index.rescan()
    assert len(index.get_albums()) == 2  # 'All Photos' and 'Album'

def test_media_index_id_lookup(tmp_path):
    photos_dir = str(tmp_path)
    os.makedirs(tmp_path / "Dir")
    img_path = tmp_path / "Dir" / "picture.jpg"
    with open(img_path, "w") as f: f.write("")
    
    index = MediaIndex(photos_dir)
    media_id = encode_id(os.path.normpath("Dir/picture.jpg"))
    
    # Retrieve media item directly by ID
    media_item = index.get_media_by_id(media_id)
    assert media_item is not None
    assert media_item["filename"] == "picture.jpg"
    
    # Test cache hit (media_id already in loaded _album_cache)
    media_item_cached = index.get_media_by_id(media_id)
    assert media_item_cached == media_item
    
    # Retrieve path safely (checking bounds)
    resolved_path = index.get_file_path(media_id)
    assert resolved_path is not None
    assert os.path.normpath(resolved_path) == os.path.normpath(str(img_path))
    
    # Attempt lookup with directory traversal (should yield None)
    traversal_id = encode_id("../../../Windows/System32/cmd.exe")
    assert index.get_file_path(traversal_id) is None

def test_media_index_unconfigured():
    index = MediaIndex(None)
    assert index.get_media_by_id("some_id") is None
    assert index.get_file_path("some_id") is None
    assert index.get_all_media() == []

def test_media_index_get_all_media(tmp_path):
    photos_dir = str(tmp_path)
    os.makedirs(tmp_path / "Dir")
    with open(tmp_path / "Dir" / "img1.jpg", "w") as f: f.write("")
    
    index = MediaIndex(photos_dir)
    all_media = index.get_all_media()
    assert len(all_media) == 2  # Dir/img1.jpg in 'All Photos' and in 'Dir'

def test_media_index_scandir_permission_error(tmp_path):
    photos_dir = str(tmp_path)
    
    with patch("os.scandir", side_effect=PermissionError("Permission Denied")):
        index = MediaIndex(photos_dir)
        # Should complete without throwing exception, simply skipping folders
        assert len(index.get_albums()) == 1  # only 'All Photos' is registered


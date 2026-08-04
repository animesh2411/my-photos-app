import os
import pytest
from io import BytesIO
from unittest.mock import patch, MagicMock
from fastapi.responses import StreamingResponse, FileResponse
from PIL import Image

from app.media import (
    _thumb_cache_path,
    generate_thumbnail,
    clear_thumb_cache,
    get_range_response
)

@pytest.fixture
def mock_thumb_cache(tmp_path):
    cache_dir = str(tmp_path / "thumb_cache")
    with patch("app.media.THUMB_CACHE_DIR", cache_dir):
        yield cache_dir

def test_thumb_cache_path(mock_thumb_cache):
    # Setup dummy file
    dummy = os.path.join(mock_thumb_cache, "dummy.jpg")
    os.makedirs(mock_thumb_cache, exist_ok=True)
    with open(dummy, "w") as f: f.write("test")
    
    path = _thumb_cache_path(dummy, 300)
    assert path.startswith(mock_thumb_cache)
    assert path.endswith(".jpg")

def test_generate_thumbnail_not_found(mock_thumb_cache):
    with pytest.raises(FileNotFoundError):
        generate_thumbnail("does_not_exist.jpg")

def test_generate_thumbnail_pil_none(mock_thumb_cache, tmp_path):
    img_path = str(tmp_path / "img.jpg")
    with open(img_path, "w") as f: f.write("dummy")
    
    with patch("app.media.Image", None):
        with pytest.raises(ValueError, match="Pillow not installed"):
            generate_thumbnail(img_path)

def test_generate_thumbnail_creation(mock_thumb_cache, tmp_path):
    img_path = str(tmp_path / "img.jpg")
    # Create actual small white image
    img = Image.new("RGB", (100, 100), color="white")
    img.save(img_path)
    
    # 1. First run generates thumbnail
    data = generate_thumbnail(img_path, width=50)
    assert len(data) > 0
    
    # 2. Verify cache folder is populated
    cache_path = _thumb_cache_path(img_path, 50)
    assert os.path.exists(cache_path)
    
    # 3. Second run retrieves from cache
    data2 = generate_thumbnail(img_path, width=50)
    assert data == data2

def test_generate_thumbnail_rgba_transparency(mock_thumb_cache, tmp_path):
    img_path = str(tmp_path / "rgba.png")
    # Create RGBA image to cover pasting / opacity code path
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    img.save(img_path)
    
    data = generate_thumbnail(img_path, width=50)
    assert len(data) > 0
    
    # Verify cached image is JPEG
    cache_path = _thumb_cache_path(img_path, 50)
    cached_img = Image.open(cache_path)
    assert cached_img.format == "JPEG"

def test_clear_thumb_cache(mock_thumb_cache):
    os.makedirs(mock_thumb_cache, exist_ok=True)
    with open(os.path.join(mock_thumb_cache, "cache.jpg"), "w") as f:
        f.write("test")
        
    assert os.path.exists(mock_thumb_cache)
    clear_thumb_cache()
    assert not os.path.exists(mock_thumb_cache)

def test_get_range_response_not_found():
    with pytest.raises(FileNotFoundError):
        get_range_response("non_existent_video.mp4", None)

def test_get_range_response_full_file(tmp_path):
    vid_path = str(tmp_path / "video.mp4")
    with open(vid_path, "wb") as f:
        f.write(b"0123456789")
        
    # No range header -> returns FileResponse
    response = get_range_response(vid_path, None)
    assert isinstance(response, FileResponse)
    assert response.headers["accept-ranges"] == "bytes"

async def consume_async_gen(async_gen):
    chunks = []
    async for chunk in async_gen:
        chunks.append(chunk)
    return b"".join(chunks)

def test_get_range_response_partial_seek(tmp_path):
    vid_path = str(tmp_path / "video.mp4")
    content = b"0123456789abcdef"
    with open(vid_path, "wb") as f:
        f.write(content)
        
    # Valid range: bytes=4-10
    response = get_range_response(vid_path, "bytes=4-10")
    assert isinstance(response, StreamingResponse)
    assert response.status_code == 206
    assert response.headers["content-range"] == "bytes 4-10/16"
    assert response.headers["content-length"] == "7"
    
    # Read streamed content
    import asyncio
    streamed_data = asyncio.run(consume_async_gen(response.body_iterator))
    assert streamed_data == b"456789a"

def test_get_range_response_partial_seek_no_end(tmp_path):
    vid_path = str(tmp_path / "video.mp4")
    content = b"0123456789abcdef"
    with open(vid_path, "wb") as f:
        f.write(content)
        
    # Valid range: bytes=10-
    response = get_range_response(vid_path, "bytes=10-")
    assert isinstance(response, StreamingResponse)
    assert response.status_code == 206
    assert response.headers["content-range"] == "bytes 10-15/16"
    assert response.headers["content-length"] == "6"
    
    # Read streamed content
    import asyncio
    streamed_data = asyncio.run(consume_async_gen(response.body_iterator))
    assert streamed_data == b"abcdef"

def test_get_range_response_invalid_range_fallback(tmp_path):
    vid_path = str(tmp_path / "video.mp4")
    with open(vid_path, "wb") as f:
        f.write(b"0123456789")
        
    # Invalid range specs -> falls back to full FileResponse
    for invalid in ["bytes=10-50", "bytes=5-2", "not_bytes=0-5", "bytes=", "bytes=abc-"]:
        response = get_range_response(vid_path, invalid)
        assert isinstance(response, FileResponse)

def test_get_range_response_unknown_mimetype(tmp_path):
    file_path = str(tmp_path / "file.xyz_unknown")
    with open(file_path, "wb") as f:
        f.write(b"test")
    response = get_range_response(file_path, None)
    assert isinstance(response, FileResponse)
    assert response.media_type == "application/octet-stream"

def test_generate_thumbnail_pil_exception(mock_thumb_cache, tmp_path):
    img_path = str(tmp_path / "img.jpg")
    with open(img_path, "wb") as f:
        f.write(b"corrupt image data")
    # This should fail parsing and fallback to reading raw data
    data = generate_thumbnail(img_path, 50)
    assert data == b"corrupt image data"

def test_clear_thumb_cache_exception(mock_thumb_cache):
    with patch("shutil.rmtree", side_effect=Exception("Failed")):
        # Should not raise exception
        clear_thumb_cache()


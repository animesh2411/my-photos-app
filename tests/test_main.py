import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi.responses import StreamingResponse
from fastapi import status

# Mock dependencies before importing app to avoid disk I/O on real app config
with patch("app.config.user_data_dir", return_value="mock_user_dir"):
    from app.main import app, get_lan_ip, media_index

@pytest.fixture
def client():
    return TestClient(app, client=("127.0.0.1", 50000))

@pytest.fixture
def mock_config():
    with patch("app.main.get_config") as m:
        m.return_value = {
            "photos_dir": "/mock/photos",
            "port": 8000,
            "access_pin": None,
            "pin_required": False,
            "configured": True
        }
        yield m

def test_get_lan_ip():
    ip = get_lan_ip()
    assert isinstance(ip, str)
    assert len(ip.split(".")) == 4

def test_api_get_config(mock_config, client):
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert data["photos_dir"] == "/mock/photos"
    assert data["configured"] is True
    assert data["pin_required"] is False

def test_api_set_config_forbidden(mock_config):
    # Simulate a client connecting from an external LAN IP
    external_client = TestClient(app, client=("192.168.1.50", 50000))
    response = external_client.post("/api/config", json={"photos_dir": "/some/path"})
    assert response.status_code == 403
    assert "only allowed from the host laptop" in response.json()["detail"]

def test_api_set_config_local_success(mock_config, client, tmp_path):
    target_dir = str(tmp_path / "photos")
    os.makedirs(target_dir, exist_ok=True)
    
    with patch("app.main.set_photos_dir") as mock_set_dir, \
         patch.object(media_index, "rescan") as mock_rescan:
        
        mock_set_dir.return_value = {
            "photos_dir": target_dir,
            "port": 8000,
            "configured": True,
            "pin_required": False
        }
        
        # Test client uses loopback 127.0.0.1 by default
        response = client.post("/api/config", json={"photos_dir": target_dir})
        assert response.status_code == 200
        data = response.json()
        assert data["photos_dir"] == target_dir
        assert data["pin_required"] is False

def test_api_select_folder_local(mock_config, client):
    with patch("app.main._open_folder_dialog", return_value="/selected/path"):
        response = client.post("/api/select-folder")
        assert response.status_code == 200
        assert response.json()["path"] is not None

def test_api_select_folder_forbidden(mock_config):
    external_client = TestClient(app, client=("192.168.1.50", 50000))
    response = external_client.post("/api/select-folder")
    assert response.status_code == 403

def test_verify_access_pin_required(client):
    # Enable PIN verification in config mock
    with patch("app.main.get_config", return_value={
        "photos_dir": "/mock/photos",
        "port": 8000,
        "access_pin": "9999",
        "pin_required": True,
        "configured": True
    }):
        # 1. Access without PIN should fail
        response = client.get("/api/albums")
        assert response.status_code == 401
        
        # 2. Access with wrong PIN should fail
        response = client.get("/api/albums", headers={"x-photobridge-pin": "1111"})
        assert response.status_code == 401
        
        # 3. Access with correct PIN header should succeed
        with patch.object(media_index, "get_albums", return_value=[]):
            response = client.get("/api/albums", headers={"x-photobridge-pin": "9999"})
            assert response.status_code == 200

def test_api_get_logs(mock_config, client):
    with patch("app.main.get_logs", return_value=[{"level": "INFO", "message": "Test"}]):
        response = client.get("/api/logs")
        assert response.status_code == 200
        assert len(response.json()) == 1

def test_api_clear_logs(mock_config, client):
    with patch("app.main.clear_logs") as mock_clear:
        response = client.delete("/api/logs")
        assert response.status_code == 200
        assert response.json() == {"status": "cleared"}
        mock_clear.assert_called_once()

def test_api_get_media(mock_config, client):
    mock_page = {
        "items": [{"id": "xyz", "filename": "p1.jpg"}],
        "total": 1,
        "has_more": False,
        "offset": 0
    }
    with patch.object(media_index, "get_album_page", return_value=mock_page) as mock_get_page:
        response = client.get("/api/media?album=Summer&offset=0&limit=50")
        assert response.status_code == 200
        assert response.json()["total"] == 1
        mock_get_page.assert_called_with("Summer", offset=0, limit=50)

def test_api_rescan(mock_config, client):
    with patch.object(media_index, "rescan_album") as mock_rescan_album:
        response = client.post("/api/rescan?album=Summer")
        assert response.status_code == 200
        assert "cache cleared" in response.json()["status"]
        mock_rescan_album.assert_called_with("Summer")
        
    with patch.object(media_index, "rescan") as mock_rescan:
        response = client.post("/api/rescan")
        assert response.status_code == 200
        mock_rescan.assert_called_once()

def test_api_thumbnail_serving(mock_config, client):
    # Media not found
    with patch.object(media_index, "get_media_by_id", return_value=None):
        response = client.get("/api/thumb/unknown")
        assert response.status_code == 404

    media_obj = {"id": "abc", "type": "image"}
    # Video type thumbnail returns 204
    with patch.object(media_index, "get_media_by_id", return_value={"id": "abc", "type": "video"}):
        response = client.get("/api/thumb/abc")
        assert response.status_code == 204

    # Valid image thumbnail serving
    with patch.object(media_index, "get_media_by_id", return_value=media_obj), \
         patch.object(media_index, "get_file_path", return_value="/mock/photos/pic.jpg"), \
         patch("os.path.exists", return_value=True), \
         patch("app.main.generate_thumbnail", return_value=b"thumb_bytes"):
        
        response = client.get("/api/thumb/abc?w=200")
        assert response.status_code == 200
        assert response.content == b"thumb_bytes"

def test_api_preview_serving(mock_config, client):
    media_obj = {"id": "abc", "type": "image"}
    with patch.object(media_index, "get_media_by_id", return_value=media_obj), \
         patch.object(media_index, "get_file_path", return_value="/mock/photos/pic.jpg"), \
         patch("os.path.exists", return_value=True), \
         patch("app.main.generate_thumbnail", return_value=b"preview_bytes"):
        
        response = client.get("/api/preview/abc")
        assert response.status_code == 200
        assert response.content == b"preview_bytes"

def test_api_full_media_serving(mock_config, client):
    media_obj = {"id": "abc", "type": "video"}
    with patch.object(media_index, "get_media_by_id", return_value=media_obj), \
         patch.object(media_index, "get_file_path", return_value="/mock/photos/vid.mp4"), \
         patch("os.path.exists", return_value=True), \
         patch("app.main.get_range_response", return_value=StreamingResponse(iter([b"chunk"]), status_code=206)):
        
        response = client.get("/api/full/abc")
        assert response.status_code == 206
        assert response.content == b"chunk"

def test_api_download_media(mock_config, client):
    media_obj = {"id": "abc", "type": "image", "filename": "pic.jpg"}
    with patch.object(media_index, "get_media_by_id", return_value=media_obj), \
         patch.object(media_index, "get_file_path", return_value="/mock/photos/pic.jpg"), \
         patch("os.path.exists", return_value=True), \
         patch("app.main.get_range_response", return_value=StreamingResponse(iter([b"data"]), status_code=200)):
        
        response = client.get("/api/download/abc")
        assert response.status_code == 200
        assert "attachment; filename=\"pic.jpg\"" in response.headers["content-disposition"]

def test_api_get_media_default_album(mock_config, client):
    mock_page = {
        "items": [],
        "total": 0,
        "has_more": False,
        "offset": 0
    }
    with patch.object(media_index, "get_album_page", return_value=mock_page) as mock_get_page:
        response = client.get("/api/media")
        assert response.status_code == 200
        mock_get_page.assert_called_with("All Photos", offset=0, limit=100)

def test_api_rescan_unconfigured(client):
    with patch("app.main.get_config", return_value={"configured": False, "pin_required": False}):
        response = client.post("/api/rescan")
        assert response.status_code == 400
        assert "not configured yet" in response.json()["detail"]

def test_api_thumbnail_file_not_found(mock_config, client):
    media_obj = {"id": "abc", "type": "image"}
    with patch.object(media_index, "get_media_by_id", return_value=media_obj), \
         patch.object(media_index, "get_file_path", return_value="/mock/photos/pic.jpg"), \
         patch("os.path.exists", return_value=False):
        
        response = client.get("/api/thumb/abc")
        assert response.status_code == 404

def test_api_preview_video_fallback(mock_config, client):
    media_obj = {"id": "abc", "type": "video"}
    with patch.object(media_index, "get_media_by_id", return_value=media_obj), \
         patch.object(media_index, "get_file_path", return_value="/mock/photos/vid.mp4"), \
         patch("os.path.exists", return_value=True), \
         patch("app.main.get_range_response", return_value=StreamingResponse(iter([b"video_bytes"]), status_code=206)):
        
        response = client.get("/api/preview/abc")
        assert response.status_code == 206
        assert response.content == b"video_bytes"

def test_api_preview_exception_fallback(mock_config, client):
    media_obj = {"id": "abc", "type": "image"}
    with patch.object(media_index, "get_media_by_id", return_value=media_obj), \
         patch.object(media_index, "get_file_path", return_value="/mock/photos/pic.jpg"), \
         patch("os.path.exists", return_value=True), \
         patch("app.main.generate_thumbnail", side_effect=Exception("Failed")), \
         patch("app.main.get_range_response", return_value=StreamingResponse(iter([b"original_bytes"]), status_code=200)):
        
        response = client.get("/api/preview/abc")
        assert response.status_code == 200
        assert response.content == b"original_bytes"

def test_log_middleware_warning_and_error(mock_config, client):
    # Triggers warning (404) in middleware logs
    with patch.object(media_index, "get_media_by_id", return_value=None):
        response = client.get("/api/thumb/unknown")
        assert response.status_code == 404

def test_startup_and_shutdown_events():
    # Directly invoke the events to ensure full code coverage
    from app.main import startup_event, shutdown_event
    
    with patch("app.config.ensure_config_exists") as mock_ensure, \
         patch("app.main.get_config", return_value={"configured": True, "photos_dir": "/mock/photos"}), \
         patch.object(media_index, "_index_albums") as mock_index_albums, \
         patch("threading.Thread") as mock_thread:
        
        import asyncio
        asyncio.run(startup_event())
        mock_ensure.assert_called_once()
        mock_index_albums.assert_called_once()
        mock_thread.assert_called_once()
        
    with patch("app.media.clear_thumb_cache") as mock_clear:
        shutdown_event()
        mock_clear.assert_called_once()


def test_verify_access_pin_rate_limiting(client):
    from app.main import pin_limiter
    # Reset limiter for this test
    pin_limiter.record_success("192.168.1.200")
    
    with patch("app.main.get_config", return_value={
        "photos_dir": "/mock/photos",
        "port": 8000,
        "access_pin": "9999",  # legacy plaintext fallback verified in tests too
        "pin_required": True,
        "configured": True
    }):
        # Run 5 failed attempts from custom client IP 192.168.1.200
        custom_client = TestClient(app, client=("192.168.1.200", 50000))
        for _ in range(5):
            response = custom_client.get("/api/albums", headers={"x-photobridge-pin": "wrong"})
            assert response.status_code == 401
            
        # The 6th request should trigger a 429 lockout
        response = custom_client.get("/api/albums", headers={"x-photobridge-pin": "wrong"})
        assert response.status_code == 429
        assert "Too many failed PIN attempts" in response.json()["detail"]
        
        # A successful PIN should still be locked out if the IP is currently locked
        response = custom_client.get("/api/albums", headers={"x-photobridge-pin": "9999"})
        assert response.status_code == 429
        
        # Success from a DIFFERENT IP should not be locked out
        other_client = TestClient(app, client=("192.168.1.201", 50000))
        with patch.object(media_index, "get_albums", return_value=[]):
            response = other_client.get("/api/albums", headers={"x-photobridge-pin": "9999"})
            assert response.status_code == 200


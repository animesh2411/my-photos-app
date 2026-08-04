import os
import json
import pytest
from unittest.mock import patch
from app.config import (
    get_config_path,
    ensure_config_exists,
    get_config,
    set_access_pin,
    set_photos_dir,
    get_port_from_env
)

@pytest.fixture
def mock_user_dir(tmp_path):
    user_dir = str(tmp_path / "user_data")
    os.makedirs(user_dir, exist_ok=True)
    with patch("app.config.user_data_dir", return_value=user_dir):
        yield user_dir

def test_get_config_path(mock_user_dir):
    path = get_config_path()
    assert path.startswith(mock_user_dir)
    assert path.endswith("config.json")

def test_ensure_config_exists(mock_user_dir):
    config_path = get_config_path()
    assert not os.path.exists(config_path)
    
    ensure_config_exists()
    assert os.path.exists(config_path)
    
    with open(config_path, "r") as f:
        data = json.load(f)
    assert data["port"] == 8000
    assert data["photos_dir"] is None
    assert data["access_pin"] is None

def test_get_config_not_configured(mock_user_dir):
    config = get_config()
    assert config["configured"] is False
    assert config["port"] == 8000
    assert config["pin_required"] is False

def test_get_config_configured(mock_user_dir, tmp_path):
    photos_dir = str(tmp_path / "photos")
    os.makedirs(photos_dir, exist_ok=True)
    
    set_photos_dir(photos_dir)
    
    config = get_config()
    assert config["configured"] is True
    assert config["photos_dir"] == photos_dir

def test_set_access_pin(mock_user_dir):
    config = get_config()
    assert config["pin_required"] is False
    
    set_access_pin("1234")
    config = get_config()
    assert config["pin_required"] is True
    assert config["access_pin"] == "1234"
    
    set_access_pin(None)
    config = get_config()
    assert config["pin_required"] is False
    assert config["access_pin"] is None

def test_set_photos_dir_validation(mock_user_dir, tmp_path):
    non_existent = str(tmp_path / "does_not_exist")
    with pytest.raises(ValueError, match="folder doesn't exist"):
        set_photos_dir(non_existent)
        
    some_file = str(tmp_path / "file.txt")
    with open(some_file, "w") as f:
        f.write("test")
    with pytest.raises(ValueError, match="path is not a folder"):
        set_photos_dir(some_file)

def test_get_port_from_env(mock_user_dir):
    with patch.dict(os.environ, {"PORT": "9000"}):
        assert get_port_from_env() == 9000
        
    with patch.dict(os.environ, {"PORT": "invalid"}):
        assert get_port_from_env() == 8000

    # Ensure port fallback works
    with patch.dict(os.environ, {}, clear=True):
        config_path = get_config_path()
        ensure_config_exists()
        with open(config_path, "r") as f:
            config = json.load(f)
        config["port"] = 8080
        with open(config_path, "w") as f:
            json.dump(config, f)
            
        assert get_port_from_env() == 8080

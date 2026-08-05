"""
Configuration management for PhotoBridge.
Reads and writes config.json with photos_dir and port settings.
"""

import json
import os
from pathlib import Path


CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "photos_dir": None,
    "port": 8000,
    "access_pin": None
}

from app.paths import user_data_dir


def get_config_path() -> str:
    """Get the absolute path to config.json in the user data directory."""
    return os.path.join(user_data_dir(), CONFIG_FILE)


def ensure_config_exists():
    """Create config.json if it doesn't exist, with default values."""
    config_path = get_config_path()
    if not os.path.exists(config_path):
        with open(config_path, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)


def get_config() -> dict:
    """
    Read and return the current configuration.
    Returns a dict with 'photos_dir', 'port', and 'configured' keys.
    'configured' is True if photos_dir is set and the path exists.
    """
    ensure_config_exists()

    config_path = get_config_path()
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Check if directory is actually configured and exists
    photos_dir = config.get("photos_dir")
    is_configured = photos_dir is not None and os.path.isdir(photos_dir)
    access_pin = config.get("access_pin")

    # Migrate legacy plaintext PIN to hash in-place
    if access_pin is not None and access_pin != "" and "$" not in access_pin:
        from app.security import hash_pin, obfuscate_pin
        hashed = hash_pin(access_pin)
        obfuscated = obfuscate_pin(access_pin)
        config["access_pin"] = hashed
        config["access_pin_local"] = obfuscated
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            access_pin = hashed
        except Exception:
            pass

    return {
        "photos_dir": photos_dir,
        "port": config.get("port", 8000),
        "access_pin": access_pin,
        "access_pin_local": config.get("access_pin_local"),
        "pin_required": access_pin is not None and access_pin != "",
        "configured": is_configured
    }


def set_access_pin(pin: str | None) -> dict:
    """Set or clear the access PIN in configuration."""
    ensure_config_exists()
    config_path = get_config_path()
    with open(config_path, 'r') as f:
        config = json.load(f)

    from app.security import hash_pin, obfuscate_pin
    config["access_pin"] = hash_pin(pin)
    config["access_pin_local"] = obfuscate_pin(pin)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    return get_config()


def set_photos_dir(path: str) -> dict:
    """
    Validate and set the photos directory.

    Args:
        path: Absolute path to the photos folder

    Returns:
        dict with updated config

    Raises:
        ValueError: if path doesn't exist or isn't a directory
    """
    # Validate the path exists and is a directory
    if not os.path.exists(path):
        raise ValueError(f"That folder doesn't exist on this laptop: {path}")

    if not os.path.isdir(path):
        raise ValueError(f"That path is not a folder: {path}")

    # Load current config
    ensure_config_exists()
    config_path = get_config_path()
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Update and save
    config["photos_dir"] = path
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    # Return updated config
    return get_config()


def get_port_from_env() -> int:
    """
    Get port from PORT environment variable, or return the configured port from config.json.
    Environment variable takes precedence.
    """
    env_port = os.getenv("PORT")
    if env_port:
        try:
            return int(env_port)
        except ValueError:
            pass

    # Fall back to config.json
    config = get_config()
    return config.get("port", 8000)


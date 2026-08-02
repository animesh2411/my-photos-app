"""
Resource path utilities for PhotoBridge.
Handles both regular Python execution and PyInstaller frozen executables.
When running as a frozen PyInstaller exe, bundled resources are extracted to sys._MEIPASS.
"""

import sys
import os


def resource_path(relative_path: str) -> str:
    """
    Get the absolute path to a resource, handling both regular Python and frozen PyInstaller executables.

    Args:
        relative_path: Path relative to the project root (e.g., "frontend" or "frontend/index.html")

    Returns:
        Absolute path to the resource
    """
    # When running as a frozen PyInstaller exe, sys._MEIPASS contains the temp extracted folder.
    # Use getattr to avoid NameError and use os.path.join for safe path construction.
    base_path = getattr(sys, "_MEIPASS", None)
    if base_path is None:
        # Project root is two levels up from this file (backend/app -> project root)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    return os.path.join(base_path, relative_path)


def get_user_data_dir() -> str:
    r"""
    Get the user data directory for PhotoBridge.
    On Windows: %LOCALAPPDATA%\PhotoBridge
    Creates the directory if it doesn't exist.

    Returns:
        Absolute path to the user data directory
    """
    if sys.platform == "win32":
        base_dir = os.path.expandvars("%LOCALAPPDATA%")
    else:
        base_dir = os.path.expanduser("~/.local/share")

    data_dir = os.path.join(base_dir, "PhotoBridge")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir




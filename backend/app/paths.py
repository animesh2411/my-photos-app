"""
Central path resolution for PhotoBridge.
Handles both development mode (running from source) and frozen mode
(running as a PyInstaller-bundled .exe).
"""

import sys
import os


def is_frozen() -> bool:
    """Return True when running inside a PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def resource_path(relative_path: str) -> str:
    """
    Resolve a path to a bundled read-only asset (frontend/, icons/, etc.).

    In dev mode:  resolves relative to the project root (parent of backend/).
    In frozen mode: resolves relative to sys._MEIPASS (PyInstaller temp dir).
    """
    if is_frozen():
        base_path = sys._MEIPASS
    else:
        # backend/app/paths.py -> backend/app -> backend -> project_root
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, relative_path)


def user_data_dir() -> str:
    """
    Return a user-writable data directory for config, logs, and cache.

    Returns %LOCALAPPDATA%/PhotoBridge on Windows.
    Falls back to ~/.PhotoBridge on other platforms.
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~")
    d = os.path.join(base, "PhotoBridge")
    os.makedirs(d, exist_ok=True)
    return d


def project_root() -> str:
    """
    Return the project root directory.

    In dev mode:  the actual project root on disk.
    In frozen mode: the directory containing the .exe.
    """
    if is_frozen():
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_app_version() -> str:
    """Read the version number from the bundled VERSION file."""
    try:
        v_path = resource_path("VERSION")
        if os.path.exists(v_path):
            with open(v_path, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        pass
    return "1.0.2"

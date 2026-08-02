"""
Application logger for PhotoBridge.
Maintains a persistent, process-safe log file (backend/app.log).
"""

import os
import time
from typing import List, Dict

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.log")


def log_event(level: str, message: str):
    """Add a log entry to disk log file."""
    entry_line = f"[{time.strftime('%H:%M:%S')}] [{level.upper()}] {message}\n"
    print(entry_line.strip())
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry_line)
    except Exception:
        pass


def get_logs(max_lines: int = 300) -> List[Dict]:
    """Return recent log entries from app.log."""
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-max_lines:]

        logs = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                parts = line.split(" ", 2)
                timestamp = parts[0].strip("[]")
                level = parts[1].strip("[]")
                msg = parts[2] if len(parts) > 2 else ""
                logs.append({"timestamp": timestamp, "level": level, "message": msg})
            except Exception:
                logs.append({"timestamp": "", "level": "INFO", "message": line})
        return logs
    except Exception as e:
        return [{"timestamp": "", "level": "ERROR", "message": f"Failed to read logs: {e}"}]


def clear_logs():
    """Truncate the log file."""
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] [INFO] Logs cleared.\n")
    except Exception:
        pass


# Initialize log file if not present
if not os.path.exists(LOG_FILE):
    log_event("INFO", "PhotoBridge Logger initialized.")

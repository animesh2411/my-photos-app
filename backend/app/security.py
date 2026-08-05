"""
Security helpers for PhotoBridge.
Implements PBKDF2-HMAC-SHA256 PIN hashing and a sliding-window rate limiter.
"""

import hashlib
import os
import secrets
import time
from collections import defaultdict
from threading import Lock

OBFUSCATION_KEY = b"PhotoBridgePinKey"


def obfuscate_pin(pin: str | None) -> str | None:
    """Obfuscate the PIN for local storage to prevent plaintext viewing."""
    if pin is None or pin == "":
        return None
    try:
        # XOR with key
        pin_bytes = pin.encode('utf-8')
        obfuscated = bytearray()
        for i, b in enumerate(pin_bytes):
            obfuscated.append(b ^ OBFUSCATION_KEY[i % len(OBFUSCATION_KEY)])
        return obfuscated.hex()
    except Exception:
        return None


def deobfuscate_pin(obfuscated_hex: str | None) -> str | None:
    """Restore the plaintext PIN from obfuscated format."""
    if obfuscated_hex is None or obfuscated_hex == "":
        return None
    try:
        obfuscated_bytes = bytes.fromhex(obfuscated_hex)
        plain = bytearray()
        for i, b in enumerate(obfuscated_bytes):
            plain.append(b ^ OBFUSCATION_KEY[i % len(OBFUSCATION_KEY)])
        return plain.decode('utf-8')
    except Exception:
        return None


def hash_pin(pin: str | None, salt: bytes = None, iterations: int = 100_000) -> str | None:
    """Hash a PIN using PBKDF2-HMAC-SHA256."""
    if pin is None or pin == "":
        return None
    if salt is None:
        salt = secrets.token_bytes(16)
    # Perform the PBKDF2 hash
    h = hashlib.pbkdf2_hmac('sha256', pin.encode('utf-8'), salt, iterations)
    # Format: salt.hex() + "$" + h.hex()
    return f"{salt.hex()}${h.hex()}"


def verify_hash(pin: str | None, hashed_pin: str | None, iterations: int = 100_000) -> bool:
    """Verify a PIN against a hashed representation. Supports plaintext fallback."""
    if pin is None or hashed_pin is None:
        return False
    
    # Plaintext fallback if not hashed format (does not contain '$')
    if "$" not in hashed_pin:
        return secrets.compare_digest(pin, hashed_pin)
        
    try:
        parts = hashed_pin.split('$')
        if len(parts) != 2:
            return False
        salt_hex, hash_hex = parts
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        
        actual = hashlib.pbkdf2_hmac('sha256', pin.encode('utf-8'), salt, iterations)
        return secrets.compare_digest(actual, expected)
    except Exception:
        return False


class PinRateLimiter:
    """Thread-safe sliding-window rate limiter for PIN verification attempts."""
    def __init__(self, limit: int = 5, window_seconds: float = 60.0):
        self.limit = limit
        self.window_seconds = window_seconds
        self.attempts = defaultdict(list)  # client_ip -> list of timestamps
        self.lock = Lock()

    def is_locked_out(self, client_ip: str) -> bool:
        """Check if client_ip is currently locked out."""
        with self.lock:
            now = time.time()
            # Clean up old timestamps
            self.attempts[client_ip] = [t for t in self.attempts[client_ip] if now - t < self.window_seconds]
            return len(self.attempts[client_ip]) >= self.limit

    def record_failure(self, client_ip: str):
        """Record a failed PIN attempt for client_ip."""
        with self.lock:
            self.attempts[client_ip].append(time.time())

    def record_success(self, client_ip: str):
        """Reset failed attempts on a successful verification."""
        with self.lock:
            self.attempts.pop(client_ip, None)

    def get_remaining_lock_time(self, client_ip: str) -> int:
        """Get remaining lockout time in seconds."""
        with self.lock:
            now = time.time()
            valid_attempts = [t for t in self.attempts[client_ip] if now - t < self.window_seconds]
            if len(valid_attempts) < self.limit:
                return 0
            # Lock ends when the oldest of the limit-hitting attempts is outside the window
            oldest_relevant = valid_attempts[-self.limit]
            return int(max(0.0, self.window_seconds - (now - oldest_relevant)))

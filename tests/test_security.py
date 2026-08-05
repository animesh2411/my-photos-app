import pytest
import time
from app.security import (
    obfuscate_pin,
    deobfuscate_pin,
    hash_pin,
    verify_hash,
    PinRateLimiter
)

def test_obfuscate_deobfuscate_none():
    assert obfuscate_pin(None) is None
    assert obfuscate_pin("") is None
    assert deobfuscate_pin(None) is None
    assert deobfuscate_pin("") is None

def test_obfuscate_exception():
    # Pass an integer instead of string to trigger Exception block
    assert obfuscate_pin(1234) is None

def test_deobfuscate_exception():
    # Pass non-hex string to trigger Exception block
    assert deobfuscate_pin("invalid-hex-characters") is None

def test_hash_pin_none():
    assert hash_pin(None) is None
    assert hash_pin("") is None

def test_verify_hash_none():
    assert verify_hash(None, "hash") is False
    assert verify_hash("pin", None) is False

def test_verify_hash_malformed():
    # Split count != 2 (triggering len(parts) != 2 check)
    assert verify_hash("1234", "salt$hash$extra") is False
    # Invalid hex string to trigger split Exception block
    assert verify_hash("1234", "invalidsalt$invalidhash") is False

def test_rate_limiter_remaining_lock():
    limiter = PinRateLimiter(limit=2, window_seconds=10.0)
    # Not locked out yet, remaining time should be 0
    assert limiter.get_remaining_lock_time("192.168.1.50") == 0
    
    limiter.record_failure("192.168.1.50")
    limiter.record_failure("192.168.1.50")
    
    # Locked out now, remaining time should be > 0
    remaining = limiter.get_remaining_lock_time("192.168.1.50")
    assert remaining > 0
    assert remaining <= 10

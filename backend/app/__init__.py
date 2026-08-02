"""
PhotoBridge - Local network Photos app for iPhone.
"""
import sys

# Convenience flag used by packaging/frozen builds to detect running from a bundled exe.
# Other modules (or frozen build code) may expect IS_FROZEN to exist.
IS_FROZEN = getattr(sys, "frozen", False)

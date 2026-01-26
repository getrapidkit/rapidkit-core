"""Sync probe file for staging sync test.

This file is intentionally minimal and safe.
"""

from datetime import datetime as _dt

# A simple marker that changes when committed, used to verify distribution sync
SYNC_PROBE_TIMESTAMP = _dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

"""Database health helpers for runtime testing."""

from __future__ import annotations

from .postgres import register_postgres_health

__all__ = ["register_postgres_health"]

import sys as _sys

_module = _sys.modules[__name__]
_sys.modules.setdefault("src.health.database", _module)
_sys.modules.setdefault("core.health.database", _module)

del _module

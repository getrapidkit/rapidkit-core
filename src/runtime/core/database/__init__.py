"""Database integrations shared across generated modules."""

from . import postgres

__all__ = ["postgres"]

import sys as _sys

_sys.modules.setdefault("src.core.database", _sys.modules[__name__])
_sys.modules.setdefault("core.database", _sys.modules[__name__])

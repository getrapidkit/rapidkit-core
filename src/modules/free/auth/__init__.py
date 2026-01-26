"""RapidKit free authentication modules package."""

from __future__ import annotations

from importlib import import_module
from typing import Dict

__all__ = [
    "AVAILABLE_AUTH_MODULES",
    "load_module",
]

AVAILABLE_AUTH_MODULES: Dict[str, str] = {
    "core": "modules.free.auth.core",
    "oauth": "modules.free.auth.oauth",
    "session": "modules.free.auth.session",
    "passwordless": "modules.free.auth.passwordless",
}


def load_module(module_name: str) -> object:
    """Dynamically import a free authentication module."""
    dotted_path = AVAILABLE_AUTH_MODULES.get(module_name)
    if dotted_path is None:
        raise KeyError(f"Unknown authentication module: {module_name}")
    return import_module(dotted_path)

"""Core utilities and services for Rapidkit CLI.

Exposes high-level registries or version info in future; kept minimal now.
"""

from types import ModuleType
from typing import List as _List

__all__: _List[str] = []

# Ensure signing helpers are registered on the package for CLI tests.
from . import module_sign  # noqa: F401


def __getattr__(name: str) -> ModuleType:
    """Lazy-load optional helpers while keeping attribute access predictable."""

    if name == "module_sign":
        import importlib

        mod = importlib.import_module("core.module_sign")
        globals()[name] = mod
        return mod
    raise AttributeError(f"module 'core' has no attribute '{name}'")

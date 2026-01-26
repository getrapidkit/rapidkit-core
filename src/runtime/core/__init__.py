"""Core runtime modules shared across generated kits."""

from importlib import import_module
from typing import Any

__all__ = [
    "database",
    "logging",
    "logging_health",
    "deployment",
    "middleware",
    "_logging_fallback",
]


def __getattr__(name: str) -> Any:  # pragma: no cover - compatibility shim
    if name in __all__:
        return import_module(f"runtime.core.{name}")
    raise AttributeError(name)


def __dir__() -> list[str]:
    return sorted(__all__)

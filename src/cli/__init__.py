"""CLI package exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

__all__ = ["global_cli"]

if TYPE_CHECKING:  # pragma: no cover - type hints only
    global_cli: Any


def __getattr__(name: str) -> Any:
    if name != "global_cli":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    try:
        module = importlib.import_module(".global_cli", __name__)
    except ModuleNotFoundError:
        module = importlib.import_module(".main", __name__)
    globals()[name] = module
    return module


def __dir__() -> list[str]:
    return sorted({*globals().keys(), *__all__})

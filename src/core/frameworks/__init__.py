"""Framework adapter interfaces and plugin registry.

This layer lets rapidkit support multiple target frameworks (FastAPI, NestJS, Rust, etc.)
by defining a minimal contract that concrete adapters must implement.
"""

from __future__ import annotations

from typing import Dict, Type

from .base import FrameworkAdapter

_registry: Dict[str, Type[FrameworkAdapter]] = {}


def register(name: str, adapter_cls: Type[FrameworkAdapter]) -> None:
    key = name.lower()
    _registry[key] = adapter_cls


def get(name: str) -> Type[FrameworkAdapter]:
    key = name.lower()
    if key not in _registry:
        raise KeyError(f"Framework adapter '{name}' not registered")
    return _registry[key]


def available() -> Dict[str, Type[FrameworkAdapter]]:
    return dict(_registry)


# Lazy import of built-in adapters (can be expanded dynamically via entry points later)
try:  # pragma: no cover - defensive
    from .fastapi_adapter import FastAPIFrameworkAdapter  # noqa: E402
except (ImportError, OSError):  # pragma: no cover - ignore adapter load errors
    pass  # adapter not available
else:  # only register if import succeeded
    register("fastapi", FastAPIFrameworkAdapter)

try:  # pragma: no cover - defensive
    from .django_adapter import DjangoFrameworkAdapter  # noqa: E402
except (ImportError, OSError):  # pragma: no cover - ignore adapter load errors
    pass  # adapter not available
else:  # only register if import succeeded
    register("django", DjangoFrameworkAdapter)

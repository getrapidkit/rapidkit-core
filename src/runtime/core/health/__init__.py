"""Health package aggregator for RapidKit runtime modules used in tests."""

from __future__ import annotations

import pkgutil
import sys as _sys
from importlib import import_module
from typing import Any, Callable, Dict, Iterable, List, Set, Tuple

_FALLBACK_IMPORTS: Tuple[Tuple[str, str], ...] = (
    ("runtime.core.logging_health", "register_logging_health"),
    ("runtime.core.health.deployment", "register_deployment_health"),
    ("runtime.core.health.database.postgres", "register_postgres_health"),
    ("runtime.core.health.middleware", "register_middleware_health"),
)

DEFAULT_HEALTH_PREFIX = "/api/health"
DEFAULT_MODULE_SEGMENT = "module"


def _iter_candidate_imports() -> List[Tuple[str, str]]:
    discovered: List[Tuple[str, str]] = list(_FALLBACK_IMPORTS)
    seen: Set[Tuple[str, str]] = set(discovered)
    package_prefix = f"{__name__}."
    dynamic: List[Tuple[str, str]] = []
    for module_info in pkgutil.walk_packages(__path__, prefix=package_prefix):
        module_path = module_info.name
        slug = module_path.rsplit(".", 1)[-1]
        attribute = f"register_{slug}_health"
        candidate = (module_path, attribute)
        if candidate in seen:
            continue
        seen.add(candidate)
        dynamic.append(candidate)
    dynamic.sort(key=lambda item: item[0])
    discovered.extend(dynamic)
    return discovered


def _resolve_health_modules() -> List[Tuple[str, Callable[[Any], None], str]]:
    resolved: List[Tuple[str, Callable[[Any], None], str]] = []
    for module_path, attribute in _iter_candidate_imports():
        try:
            module = import_module(module_path)
            registrar = getattr(module, attribute)
        except (ImportError, AttributeError):
            continue
        if callable(registrar):
            slug = module_path.rsplit(".", 1)[-1]
            resolved.append((module_path, registrar, slug))
    return resolved


def _discover_registrars() -> List[Callable[[Any], None]]:
    registrars: List[Callable[[Any], None]] = []
    for _module_path, registrar, _slug in _resolve_health_modules():
        registrars.append(registrar)
    return registrars


def iter_health_registrars() -> Iterable[Callable[[Any], None]]:
    """Yield available health registrar callables."""

    yield from _discover_registrars()


def register_health_routes(app: Any) -> None:
    """Register all detected health routers against the provided FastAPI app."""

    for registrar in _discover_registrars():
        registrar(app)


def _build_module_path(prefix: str, slug: str) -> str:
    cleaned_prefix = prefix.rstrip("/") or "/"
    cleaned_slug = slug.replace("_", "-")
    return f"{cleaned_prefix}/{DEFAULT_MODULE_SEGMENT}/{cleaned_slug}"


def list_health_routes(prefix: str = DEFAULT_HEALTH_PREFIX) -> List[Dict[str, str]]:
    """Return metadata about available module health endpoints."""

    routes: List[Dict[str, str]] = []
    for module_path, _registrar, slug in _resolve_health_modules():
        routes.append(
            {
                "module_path": module_path,
                "slug": slug,
                "path": _build_module_path(prefix, slug),
            }
        )
    return routes


__all__ = [
    "iter_health_registrars",
    "register_health_routes",
    "list_health_routes",
]

_module = _sys.modules[__name__]
_sys.modules.setdefault("src.health", _module)
_sys.modules.setdefault("core.health", _module)

del _module

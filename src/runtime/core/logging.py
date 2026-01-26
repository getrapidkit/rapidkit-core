"""Project-facing wrapper around the RapidKit vendor logging runtime."""

from __future__ import annotations

import importlib.util
import os
import sys
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, cast

_VENDOR_MODULE = "logging"
_VENDOR_VERSION = "1.0.0"
_VENDOR_RELATIVE_PATH = "src/modules/free/essentials/logging/logging.py"
_VENDOR_ROOT_ENV = "RAPIDKIT_VENDOR_ROOT"
_CACHE_PREFIX = "rapidkit_vendor_"
_REQUEST_CONTEXT_ENABLED = True
_FALLBACK_MODULE: ModuleType | None = None


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _vendor_root() -> Path:
    override = os.getenv(_VENDOR_ROOT_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return _project_root() / ".rapidkit" / "vendor"


def _vendor_base_dir() -> Path:
    root = _vendor_root()
    module_dir = root / _VENDOR_MODULE
    preferred = module_dir / _VENDOR_VERSION if _VENDOR_VERSION else None
    if preferred and preferred.exists():
        return preferred
    candidates = sorted((p for p in module_dir.glob("*") if p.is_dir()), reverse=True)
    if candidates:
        return candidates[0]
    raise RuntimeError(
        "RapidKit vendor payload for '{module}' not found under {root}. "
        "Re-run `rapidkit modules install {module}`.".format(module=_VENDOR_MODULE, root=root)
    )


def _vendor_file() -> Path:
    return _vendor_base_dir() / _VENDOR_RELATIVE_PATH


@lru_cache(maxsize=1)
def _load_vendor_module() -> ModuleType:
    try:
        vendor_path = _vendor_file()
    except RuntimeError:
        return _load_fallback_module()

    if not vendor_path.exists():
        return _load_fallback_module()

    module_name = _CACHE_PREFIX + _VENDOR_MODULE.replace("/", "_") + "_logging"

    spec = importlib.util.spec_from_file_location(module_name, vendor_path)
    if spec is None or spec.loader is None:
        return _load_fallback_module()

    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(module_name, module)
    try:
        spec.loader.exec_module(module)
    except Exception:  # noqa: BLE001 - fallback when vendor execution fails
        return _load_fallback_module()
    return module


def _load_fallback_module() -> ModuleType:
    global _FALLBACK_MODULE  # noqa: PLW0603
    if _FALLBACK_MODULE is None:
        from . import _logging_fallback

        _FALLBACK_MODULE = _logging_fallback
    return _FALLBACK_MODULE


def _resolve_export(name: str) -> Any:
    vendor = _load_vendor_module()
    try:
        return getattr(vendor, name)
    except AttributeError as exc:  # pragma: no cover - defensive against drift
        raise RuntimeError(f"Vendor module missing attribute '{name}'") from exc


def refresh_vendor_module() -> None:
    """Clear vendor import caches (useful after module upgrades)."""

    _load_vendor_module.cache_clear()
    global _FALLBACK_MODULE  # noqa: PLW0603
    _FALLBACK_MODULE = None


set_request_context: Callable[..., None]
RequestContextMiddleware: Any


# Exported APIs delegated to vendor implementation
get_logger = _resolve_export("get_logger")
LoggingConfig = _resolve_export("LoggingConfig")
OTelBridgeHandler = _resolve_export("OTelBridgeHandler")
MetricsBridgeHandler = _resolve_export("MetricsBridgeHandler")
NoiseFilter = _resolve_export("NoiseFilter")
RedactionFilter = _resolve_export("RedactionFilter")
ContextEnricher = _resolve_export("ContextEnricher")
JsonFormatter = _resolve_export("JsonFormatter")
ColoredFormatter = _resolve_export("ColoredFormatter")
create_stream_handler = _resolve_export("create_stream_handler")
create_file_handler = _resolve_export("create_file_handler")
create_syslog_handler = _resolve_export("create_syslog_handler")
create_queue_handler = _resolve_export("create_queue_handler")
setup_queue_listeners = _resolve_export("setup_queue_listeners")
shutdown_queue = _resolve_export("shutdown_queue")


if _REQUEST_CONTEXT_ENABLED:
    set_request_context = cast(Callable[..., None], _resolve_export("set_request_context"))
    RequestContextMiddleware = _resolve_export("RequestContextMiddleware")
else:  # pragma: no cover - defensive stub when overrides disable middleware

    def _disabled_set_request_context(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("Request context propagation disabled via generator overrides.")

    class _DisabledRequestContextMiddleware:
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
            raise RuntimeError("Request context middleware disabled via generator overrides.")

    set_request_context = _disabled_set_request_context
    RequestContextMiddleware = _DisabledRequestContextMiddleware


def get_logging_metadata() -> Dict[str, Any]:
    """Return vendor metadata for observability dashboards."""

    vendor = _load_vendor_module()
    return {
        "module": _VENDOR_MODULE,
        "version": _VENDOR_VERSION,
        "available": sorted(getattr(vendor, "__all__", [])),
    }


ApplyOverridesFn = Callable[[ModuleType, str], Any]
_apply_module_overrides: ApplyOverridesFn | None


try:  # Optional override contracts (used by enterprise deployments)
    from core.services.override_contracts import apply_module_overrides as _apply_module_overrides
except ImportError:  # pragma: no cover - override system optional
    _apply_module_overrides = None

if _apply_module_overrides is not None:  # pragma: no branch - tiny guard
    _apply_module_overrides(sys.modules[__name__], "logging")


__all__ = [
    "get_logger",
    "set_request_context",
    "RequestContextMiddleware",
    "LoggingConfig",
    "OTelBridgeHandler",
    "MetricsBridgeHandler",
    "NoiseFilter",
    "RedactionFilter",
    "ContextEnricher",
    "JsonFormatter",
    "ColoredFormatter",
    "create_stream_handler",
    "create_file_handler",
    "create_syslog_handler",
    "create_queue_handler",
    "setup_queue_listeners",
    "shutdown_queue",
    "get_logging_metadata",
    "refresh_vendor_module",
]

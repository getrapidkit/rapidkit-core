"""Fallback logging runtime used when vendor payloads are unavailable."""

from __future__ import annotations

import contextvars
import json
import logging
import logging.handlers
import os
import queue
import re
import socket
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional, TypedDict, cast

try:  # Prefer project settings when available
    from core.settings import settings as _settings  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional integration
    _settings = None

BaseHTTPMiddleware: Any
Request: Any
Response: Any
RequestContextMiddleware: Any

try:  # Optional FastAPI dependency for request context middleware
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response
except ImportError:  # pragma: no cover - middleware guarded at runtime
    BaseHTTPMiddleware = None
    Request = None
    Response = None


class _LoggingDefaults(TypedDict):
    level: str
    format: str
    sinks: List[str]
    async_queue: bool
    file_path: str
    sampling_rate: float
    otel_bridge_enabled: bool
    metrics_bridge_enabled: bool
    enable_redaction: bool


_DEFAULTS: _LoggingDefaults = {
    "level": "INFO",
    "format": "json",
    "sinks": ["stderr"],
    "async_queue": True,
    "file_path": "logs/app.log",
    "sampling_rate": 1.0,
    "otel_bridge_enabled": False,
    "metrics_bridge_enabled": False,
    "enable_redaction": True,
}


def _is_redaction_enabled() -> bool:
    if _settings is not None:
        return bool(getattr(_settings, "LOG_ENABLE_REDACTION", _DEFAULTS["enable_redaction"]))
    value = os.getenv("LOG_ENABLE_REDACTION")
    if value is None:
        return _DEFAULTS["enable_redaction"]
    return value.strip().lower() in {"1", "true", "yes", "on"}


request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)
user_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("user_id", default=None)


def set_request_context(request_id: str, user_id: Optional[str] = None) -> None:
    """Store correlation identifiers for later log records."""

    request_id_var.set(request_id)
    if user_id is not None:
        user_id_var.set(user_id)


class NoiseFilter(logging.Filter):
    """Filter out overly chatty libraries by default."""

    noisy_loggers: Iterable[str] = (
        "uvicorn.access",
        "sqlalchemy.engine",
        "asyncio",
        "http.client",
    )

    def filter(self, record: logging.LogRecord) -> bool:
        return record.name not in self.noisy_loggers


SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(api[_-]?key|secret|token|passwd|password)=[^&\s]+"),
)


class RedactionFilter(logging.Filter):
    """Mask common secret patterns in log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not _is_redaction_enabled():
            return True

        message = record.getMessage()
        for pattern in SECRET_PATTERNS:
            message = pattern.sub(r"\1=***", message)
        record.msg = message
        return True


class ContextEnricher(logging.Filter):
    """Inject correlation identifiers into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.user_id = user_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    """Emit structured JSON payloads for log records."""

    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - formatting heavy
        payload: Dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "lvl": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "user_id": getattr(record, "user_id", None),
            "host": socket.gethostname(),
            "env": os.getenv("ENVIRONMENT", os.getenv("ENV", "development")),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        extra = getattr(record, "extra", None)
        if isinstance(extra, dict):
            payload.update(extra)

        indent = int(os.getenv("LOG_JSON_INDENT", "0") or 0)
        return json.dumps(payload, ensure_ascii=False, indent=indent)


class ColoredFormatter(logging.Formatter):  # pragma: no cover - cosmetic output
    """Colourise log output for interactive use."""

    _COLOR_MAP = {
        "DEBUG": "\x1b[36m",
        "INFO": "\x1b[32m",
        "WARNING": "\x1b[33m",
        "ERROR": "\x1b[31m",
        "CRITICAL": "\x1b[35m",
    }
    _RESET = "\x1b[0m"

    def format(self, record: logging.LogRecord) -> str:
        rendered = super().format(record)
        tint = self._COLOR_MAP.get(record.levelname, "")
        if not tint:
            return rendered
        return f"{tint}{rendered}{self._RESET}"


def _build_formatter(style: str) -> logging.Formatter:
    normalized = style.lower()
    if normalized == "json":
        return JsonFormatter()
    if normalized == "colored":
        return ColoredFormatter(
            fmt=(
                "%(asctime)s | %(levelname)s | %(name)s | "
                "[req:%(request_id)s user:%(user_id)s] %(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    return logging.Formatter(
        fmt=(
            "%(asctime)s | %(levelname)s | %(name)s | "
            "[req:%(request_id)s user:%(user_id)s] %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _attach_filters(handler: logging.Handler) -> logging.Handler:
    handler.addFilter(NoiseFilter())
    handler.addFilter(RedactionFilter())
    handler.addFilter(ContextEnricher())
    return handler


def create_stream_handler(style: str) -> logging.Handler:
    handler = logging.StreamHandler()
    handler.setFormatter(_build_formatter(style))
    return _attach_filters(handler)


def create_file_handler(style: str, file_path: str) -> logging.Handler:
    target_path = Path(file_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    handler: logging.Handler = logging.handlers.RotatingFileHandler(
        target_path,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(_build_formatter(style))
    return _attach_filters(handler)


def create_syslog_handler(style: str) -> logging.Handler:
    if os.path.exists("/dev/log"):
        address: str | tuple[str, int] = "/dev/log"
    else:
        host = os.getenv("SYSLOG_HOST", "localhost")
        port = int(os.getenv("SYSLOG_PORT", "514"))
        address = (host, port)
    handler = logging.handlers.SysLogHandler(address=address)
    handler.setFormatter(_build_formatter(style))
    return _attach_filters(handler)


_QUEUE: queue.Queue[Any] | None = None
_LISTENER: logging.handlers.QueueListener | None = None


def setup_queue_listeners(style: str, sinks: Iterable[str], file_path: str) -> None:
    """Initialise a background listener for async logging."""

    global _QUEUE, _LISTENER  # noqa: PLW0603
    if _LISTENER is not None:
        return

    _QUEUE = queue.Queue()
    handlers: List[logging.Handler] = []
    for sink in (sink.lower() for sink in sinks):
        if sink == "stderr":
            handlers.append(create_stream_handler(style))
        elif sink == "file":
            handlers.append(create_file_handler(style, file_path))
        elif sink == "syslog":
            with suppress(Exception):  # pragma: no cover - optional
                handlers.append(create_syslog_handler(style))

    _LISTENER = logging.handlers.QueueListener(_QUEUE, *handlers, respect_handler_level=True)
    _LISTENER.start()


def create_queue_handler() -> logging.handlers.QueueHandler:
    if _QUEUE is None:
        raise RuntimeError("Queue listener not initialised; call setup_queue_listeners first")
    return logging.handlers.QueueHandler(_QUEUE)


def shutdown_queue() -> None:  # pragma: no cover - rarely exercised
    global _LISTENER  # noqa: PLW0603
    if _LISTENER is not None:
        _LISTENER.stop()
        _LISTENER = None


class OTelBridgeHandler(logging.Handler):  # pragma: no cover - stub
    def emit(self, record: logging.LogRecord) -> None:
        return None


class MetricsBridgeHandler(logging.Handler):  # pragma: no cover - stub
    def emit(self, record: logging.LogRecord) -> None:
        return None


@dataclass(frozen=True)
class LoggingConfig:
    level: str
    format: str
    sinks: List[str]
    async_queue: bool
    file_path: str
    sampling_rate: float
    otel_bridge_enabled: bool
    metrics_bridge_enabled: bool


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _list_env(name: str, default: Iterable[str]) -> List[str]:
    value = os.getenv(name)
    if value is None:
        return list(default)
    if value.strip().startswith("[") and value.strip().endswith("]"):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:  # pragma: no cover - defensive
            parsed = []
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    return [part.strip() for part in value.split(",") if part.strip()]


def _resolve_config() -> LoggingConfig:
    defaults = _DEFAULTS
    if _settings is not None:
        format_style = cast(str, getattr(_settings, "LOG_FORMAT", defaults["format"]))
        sinks = list(cast(Iterable[str], getattr(_settings, "LOG_SINKS", defaults["sinks"])))
        level_name = cast(str, getattr(_settings, "LOG_LEVEL", defaults["level"]))
        async_queue_enabled = bool(getattr(_settings, "LOG_ASYNC_QUEUE", defaults["async_queue"]))
        file_path = cast(str, getattr(_settings, "LOG_FILE_PATH", defaults["file_path"]))
        sampling = float(getattr(_settings, "LOG_SAMPLING_RATE", defaults["sampling_rate"]))
        otel_bridge = bool(
            getattr(_settings, "OTEL_BRIDGE_ENABLED", defaults["otel_bridge_enabled"])
        )
        metrics_bridge = bool(
            getattr(_settings, "METRICS_BRIDGE_ENABLED", defaults["metrics_bridge_enabled"])
        )
    else:
        format_style = os.getenv("LOG_FORMAT", defaults["format"])
        sinks = _list_env("LOG_SINKS", defaults["sinks"])
        level_name = os.getenv("LOG_LEVEL", defaults["level"])
        async_queue_enabled = _bool_env("LOG_ASYNC_QUEUE", defaults["async_queue"])
        file_path = os.getenv("LOG_FILE_PATH", defaults["file_path"])
        sampling = float(
            os.getenv("LOG_SAMPLING_RATE", str(defaults["sampling_rate"]))
            or defaults["sampling_rate"]
        )
        otel_bridge = _bool_env("OTEL_BRIDGE_ENABLED", defaults["otel_bridge_enabled"])
        metrics_bridge = _bool_env("METRICS_BRIDGE_ENABLED", defaults["metrics_bridge_enabled"])

    return LoggingConfig(
        level=str(level_name).upper(),
        format=str(format_style).lower(),
        sinks=[sink.lower() for sink in sinks],
        async_queue=async_queue_enabled,
        file_path=str(file_path),
        sampling_rate=float(sampling),
        otel_bridge_enabled=otel_bridge,
        metrics_bridge_enabled=metrics_bridge,
    )


_LOGGER_CACHE: Dict[str, logging.Logger] = {}


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a configured logger enriched with RapidKit defaults."""

    cache_key = name or "app"
    if cache_key in _LOGGER_CACHE:
        return _LOGGER_CACHE[cache_key]

    cfg = _resolve_config()
    level = getattr(logging, cfg.level.upper(), logging.INFO)

    logger = logging.getLogger(cache_key)
    logger.setLevel(level)
    logger.propagate = False

    if cfg.async_queue:
        setup_queue_listeners(cfg.format, cfg.sinks, cfg.file_path)
        logger.addHandler(create_queue_handler())
    else:
        if "stderr" in cfg.sinks:
            logger.addHandler(create_stream_handler(cfg.format))
        if "file" in cfg.sinks:
            logger.addHandler(create_file_handler(cfg.format, cfg.file_path))
        if "syslog" in cfg.sinks:
            with suppress(Exception):  # pragma: no cover - optional
                logger.addHandler(create_syslog_handler(cfg.format))

    if cfg.otel_bridge_enabled:
        logger.addHandler(OTelBridgeHandler())
    if cfg.metrics_bridge_enabled:
        logger.addHandler(MetricsBridgeHandler())

    _LOGGER_CACHE[cache_key] = logger
    return logger


def get_logging_metadata() -> Dict[str, Any]:
    return {
        "module": "logging",
        "version": "fallback",
        "available": sorted(__all__),
    }


def refresh_vendor_module() -> None:
    """No-op for fallback implementation."""


if BaseHTTPMiddleware is not None:

    class _StarletteRequestContextMiddleware(BaseHTTPMiddleware):
        """Populate request context variables for FastAPI / Starlette."""

        async def dispatch(self, request: Any, call_next: Callable[[Any], Awaitable[Any]]) -> Any:
            set_request_context(
                request.headers.get("X-Request-ID", "unknown"),
                request.headers.get("X-User-ID"),
            )
            response = await call_next(request)
            response.headers.setdefault("X-Request-ID", request_id_var.get() or "unknown")
            return response

    RequestContextMiddleware = _StarletteRequestContextMiddleware

else:  # pragma: no cover - starlette unavailable

    class _FallbackRequestContextMiddleware:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("Starlette is required for RequestContextMiddleware")

    RequestContextMiddleware = _FallbackRequestContextMiddleware


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

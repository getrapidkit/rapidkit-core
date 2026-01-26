import asyncio
import logging
import os
import sys
from types import SimpleNamespace

import pytest

from runtime.core import _logging_fallback as fallback


@pytest.fixture(autouse=True)
def reset_fallback_state(monkeypatch):
    # Ensure globals do not leak between tests
    monkeypatch.setattr(fallback, "_settings", None)
    monkeypatch.setattr(fallback, "_LOGGER_CACHE", {})
    monkeypatch.setattr(fallback, "_QUEUE", None)
    monkeypatch.setattr(fallback, "_LISTENER", None)
    fallback.request_id_var.set(None)
    fallback.user_id_var.set(None)
    for var in (
        "LOG_ENABLE_REDACTION",
        "LOG_FORMAT",
        "LOG_SINKS",
        "LOG_ASYNC_QUEUE",
        "LOG_FILE_PATH",
        "LOG_SAMPLING_RATE",
        "OTEL_BRIDGE_ENABLED",
        "METRICS_BRIDGE_ENABLED",
    ):
        monkeypatch.delenv(var, raising=False)
    yield
    fallback.request_id_var.set(None)
    fallback.user_id_var.set(None)
    fallback.shutdown_queue()


def _make_record(message: str) -> logging.LogRecord:
    return logging.LogRecord("unit", logging.INFO, __file__, 123, message, (), None)


def test_redaction_filter_masks_secret(monkeypatch):
    monkeypatch.setenv("LOG_ENABLE_REDACTION", "1")
    record = _make_record("token=my-secret")
    redactor = fallback.RedactionFilter()
    assert redactor.filter(record)
    assert record.getMessage() == "token=***"


def test_redaction_filter_disabled_via_settings(monkeypatch):
    monkeypatch.setattr(fallback, "_settings", SimpleNamespace(LOG_ENABLE_REDACTION=False))
    record = _make_record("token=my-secret")
    redactor = fallback.RedactionFilter()
    assert redactor.filter(record)
    assert record.getMessage() == "token=my-secret"


def test_is_redaction_enabled_env_default(monkeypatch):
    monkeypatch.setattr(fallback, "_settings", None)
    monkeypatch.delenv("LOG_ENABLE_REDACTION", raising=False)
    assert fallback._is_redaction_enabled()


def test_is_redaction_enabled_env_false(monkeypatch):
    monkeypatch.setattr(fallback, "_settings", None)
    monkeypatch.setenv("LOG_ENABLE_REDACTION", "off")
    assert not fallback._is_redaction_enabled()


def test_context_enricher_attaches_request_metadata():
    fallback.set_request_context("req-123", "user-456")
    record = _make_record("plain message")
    enricher = fallback.ContextEnricher()
    assert enricher.filter(record)
    assert record.request_id == "req-123"
    assert record.user_id == "user-456"


def test_set_request_context_without_user():
    fallback.set_request_context("req-abc")
    record = _make_record("payload")
    fallback.ContextEnricher().filter(record)
    assert record.request_id == "req-abc"
    assert record.user_id is None


def test_resolve_config_prefers_settings_object(monkeypatch):
    dummy_settings = SimpleNamespace(
        LOG_FORMAT="colored",
        LOG_SINKS=["stderr"],
        LOG_LEVEL="debug",
        LOG_ASYNC_QUEUE=False,
        LOG_FILE_PATH="/tmp/custom.log",
        LOG_SAMPLING_RATE=0.5,
        OTEL_BRIDGE_ENABLED=True,
        METRICS_BRIDGE_ENABLED=True,
    )
    monkeypatch.setattr(fallback, "_settings", dummy_settings)

    cfg = fallback._resolve_config()

    assert cfg.format == "colored"
    assert cfg.sinks == ["stderr"]
    assert cfg.level == "DEBUG"
    assert not cfg.async_queue
    assert cfg.file_path == "/tmp/custom.log"
    assert cfg.sampling_rate == pytest.approx(0.5)
    assert cfg.otel_bridge_enabled
    assert cfg.metrics_bridge_enabled


def test_get_logger_uses_configured_sinks(tmp_path, monkeypatch):
    monkeypatch.setenv("LOG_ASYNC_QUEUE", "0")
    monkeypatch.setenv("LOG_SINKS", "stderr,file")
    monkeypatch.setenv("LOG_FILE_PATH", str(tmp_path / "app.log"))
    monkeypatch.setenv("LOG_LEVEL", "warning")

    logger = fallback.get_logger("unit-test")

    assert logger.level == logging.WARNING
    assert not logger.propagate
    assert any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers)
    assert any(
        isinstance(handler, logging.handlers.RotatingFileHandler) for handler in logger.handlers
    )

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def test_setup_queue_listeners_initialises_once(monkeypatch):
    created_listeners = []

    class DummyListener:
        def __init__(self, queue, *handlers, respect_handler_level):
            self.queue = queue
            self.handlers = handlers
            self.started = False
            created_listeners.append(self)

        def start(self):
            self.started = True

        def stop(self):
            self.started = False

    monkeypatch.setattr(logging.handlers, "QueueListener", DummyListener)

    fallback.setup_queue_listeners("json", ["stderr"], "logs/app.log")
    assert fallback._QUEUE is not None
    assert fallback._LISTENER is created_listeners[0]
    assert created_listeners[0].started

    # Second invocation should not create a new listener
    fallback.setup_queue_listeners("json", ["stderr"], "logs/app.log")
    assert len(created_listeners) == 1


def test_setup_queue_listeners_supports_file_and_syslog(monkeypatch, tmp_path):
    created = []

    def fake_file_handler(style, path):
        created.append(("file", style, path))
        return logging.StreamHandler()

    def fake_syslog_handler(style):
        created.append(("syslog", style))
        return logging.StreamHandler()

    class DummyListener:
        def __init__(self, queue, *handlers, respect_handler_level):
            self.queue = queue
            self.handlers = handlers

        def start(self):
            return None

        def stop(self):
            return None

    monkeypatch.setattr(fallback, "create_file_handler", fake_file_handler)
    monkeypatch.setattr(fallback, "create_syslog_handler", fake_syslog_handler)
    monkeypatch.setattr(logging.handlers, "QueueListener", DummyListener)

    fallback.setup_queue_listeners("json", ["file", "syslog"], str(tmp_path / "logs/app.log"))

    assert ("file", "json", str(tmp_path / "logs/app.log")) in created
    assert ("syslog", "json") in created


def test_create_queue_handler_without_initialisation():
    with pytest.raises(RuntimeError):
        fallback.create_queue_handler()


def test_create_queue_handler_after_setup(monkeypatch):
    class DummyListener:
        def __init__(self, queue, *handlers, respect_handler_level):
            self.queue = queue

        def start(self):
            return None

        def stop(self):
            return None

    monkeypatch.setattr(logging.handlers, "QueueListener", DummyListener)
    fallback.setup_queue_listeners("json", ["stderr"], "logs/app.log")
    handler = fallback.create_queue_handler()
    assert isinstance(handler, logging.handlers.QueueHandler)


def test_get_logger_with_async_queue(monkeypatch):
    monkeypatch.setenv("LOG_ASYNC_QUEUE", "1")
    monkeypatch.setenv("LOG_SINKS", "stderr")

    class DummyListener:
        def __init__(self, queue, *handlers, respect_handler_level):
            self.queue = queue
            self.handlers = handlers

        def start(self):
            return None

        def stop(self):
            return None

    monkeypatch.setattr(logging.handlers, "QueueListener", DummyListener)

    logger = fallback.get_logger("async")
    queue_handlers = [h for h in logger.handlers if isinstance(h, logging.handlers.QueueHandler)]
    assert queue_handlers

    for handler in list(logger.handlers):
        logger.removeHandler(handler)


def test_get_logger_caches_and_adds_optional_bridges(monkeypatch):
    monkeypatch.setenv("LOG_ASYNC_QUEUE", "0")
    monkeypatch.setenv("LOG_SINKS", "stderr")
    monkeypatch.setenv("OTEL_BRIDGE_ENABLED", "1")
    monkeypatch.setenv("METRICS_BRIDGE_ENABLED", "true")

    logger = fallback.get_logger("bridged")
    assert any(isinstance(handler, fallback.OTelBridgeHandler) for handler in logger.handlers)
    assert any(isinstance(handler, fallback.MetricsBridgeHandler) for handler in logger.handlers)

    same_logger = fallback.get_logger("bridged")
    assert same_logger is logger

    for handler in list(logger.handlers):
        logger.removeHandler(handler)


def test_get_logging_metadata_and_refresh():
    metadata = fallback.get_logging_metadata()
    assert metadata["module"] == "logging"
    fallback.refresh_vendor_module()  # should be a no-op without raising


def test_json_formatter_includes_exception():
    formatter = fallback.JsonFormatter()

    try:
        raise ValueError("boom")
    except ValueError:
        record = _make_record("failed")
    record.exc_info = sys.exc_info()

    rendered = formatter.format(record)
    assert '"exception"' in rendered


def test_colored_formatter_applies_tint():
    formatter = fallback.ColoredFormatter(fmt="%(levelname)s %(message)s")
    record = _make_record("hello")
    record.levelname = "ERROR"
    tinted = formatter.format(record)
    assert tinted.startswith("\x1b[31m")


def test_build_formatter_handles_colored_style():
    formatter = fallback._build_formatter("colored")
    assert isinstance(formatter, fallback.ColoredFormatter)


def test_get_logger_includes_syslog_sink(monkeypatch):
    monkeypatch.setenv("LOG_ASYNC_QUEUE", "0")
    monkeypatch.setenv("LOG_SINKS", "syslog")

    added_handlers = []

    def dummy_syslog_handler(style):
        handler = logging.StreamHandler()
        added_handlers.append((style, handler))
        return handler

    monkeypatch.setattr(fallback, "create_syslog_handler", dummy_syslog_handler)

    logger = fallback.get_logger("syslog")
    assert added_handlers and added_handlers[0][0] == fallback._DEFAULTS["format"]
    assert any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers)

    for handler in list(logger.handlers):
        logger.removeHandler(handler)


def test_get_logger_syslog_handler_failure(monkeypatch):
    monkeypatch.setenv("LOG_ASYNC_QUEUE", "0")
    monkeypatch.setenv("LOG_SINKS", "syslog")

    def failing_syslog_handler(_style):
        raise RuntimeError("syslog down")

    monkeypatch.setattr(fallback, "create_syslog_handler", failing_syslog_handler)

    logger = fallback.get_logger("syslog-failure")

    # ensure failure path does not attach handlers or raise
    assert not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers)

    for handler in list(logger.handlers):
        logger.removeHandler(handler)


def test_create_syslog_handler(monkeypatch):
    created = {}

    class DummySysLog:
        def __init__(self, address):
            created["address"] = address
            self.formatter = None

        def setFormatter(self, formatter):
            created["formatter"] = formatter

        def addFilter(self, _filter):
            return None

    monkeypatch.setattr(os.path, "exists", lambda _path: False)
    monkeypatch.setattr(logging.handlers, "SysLogHandler", DummySysLog)

    handler = fallback.create_syslog_handler("json")
    assert created["address"][0] == os.getenv("SYSLOG_HOST", "localhost")
    assert handler is not None


def test_create_syslog_handler_dev_log(monkeypatch):
    created = {}

    class DummySysLog:
        def __init__(self, address):
            created["address"] = address

        def setFormatter(self, formatter):
            created["formatter"] = formatter

        def addFilter(self, _filter):
            return None

    monkeypatch.setattr(os.path, "exists", lambda _path: True)
    monkeypatch.setattr(logging.handlers, "SysLogHandler", DummySysLog)

    handler = fallback.create_syslog_handler("json")
    assert created["address"] == "/dev/log"
    assert handler is not None


def test_list_env_parses_json(monkeypatch):
    monkeypatch.setenv("LOG_SINKS", '["stderr", "syslog"]')
    result = fallback._list_env("LOG_SINKS", ["stderr"])
    assert result == ["stderr", "syslog"]


def test_request_context_middleware_dispatch():
    if not isinstance(fallback.BaseHTTPMiddleware, type):
        pytest.skip("Starlette not available")

    middleware = fallback.RequestContextMiddleware(lambda app: app)

    async def _run_dispatch():
        async def call_next(_request):
            return fallback.Response("ok", status_code=200)

        async def receive():
            return {"type": "http.request"}

        scope = {
            "type": "http",
            "headers": [(b"x-request-id", b"req-999"), (b"x-user-id", b"user-1")],
        }
        request = fallback.Request(scope, receive)
        return await middleware.dispatch(request, call_next)

    response = asyncio.run(_run_dispatch())

    assert response.headers["X-Request-ID"] == "req-999"

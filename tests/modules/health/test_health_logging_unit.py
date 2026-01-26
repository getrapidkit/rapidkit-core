import importlib

import pytest

from runtime.core import logging_health

fastapi = pytest.importorskip("fastapi")
FastAPI = fastapi.FastAPI


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_logging_health_check_returns_metadata(monkeypatch):
    calls = []

    def fake_get_logger(name):
        class DummyLogger:
            def __init__(self, logger_name):
                self.name = logger_name

            def debug(self, message, *, extra=None):
                calls.append((self.name, message, extra))

        return DummyLogger(name)

    monkeypatch.setattr(logging_health, "get_logger", fake_get_logger)
    monkeypatch.setattr(
        logging_health,
        "get_logging_metadata",
        lambda: {"module": "logging", "version": "9.9.9"},
    )
    logging_health.logger = fake_get_logger("logging.health")

    result = await logging_health.logging_health_check()

    assert result["status"] == "ok"
    assert result["module"] == "logging"
    assert result["version"] == "9.9.9"
    assert calls == [
        (
            "logging.health",
            "Logging health endpoint invoked",
            {"payload": result},
        )
    ]


def test_register_logging_health_mounts_router():
    app = FastAPI()
    # importlib.reload ensures router state is initialised for FastAPI path resolution
    importlib.reload(logging_health)

    logging_health.register_logging_health(app)

    paths = {route.path for route in app.routes}
    assert "/api/health/module/logging" in paths


def test_register_logging_health_requires_fastapi(monkeypatch):
    monkeypatch.setattr(logging_health, "_FASTAPI_AVAILABLE", False)

    with pytest.raises(RuntimeError):
        logging_health.register_logging_health(object())

"""Integration tests for the Middleware module runtime."""

from __future__ import annotations

import importlib.util
from importlib import import_module

import pytest

try:
    from fastapi import FastAPI, status
    from fastapi.testclient import TestClient
except (RuntimeError, ModuleNotFoundError) as exc:  # pragma: no cover - optional dependency
    message = str(exc).lower()
    missing_name = getattr(exc, "name", "")
    if "httpx" in message or missing_name == "httpx":
        pytest.skip("httpx is required for FastAPI TestClient", allow_module_level=True)
    raise


MIDDLEWARE_AVAILABLE = importlib.util.find_spec("runtime.core.middleware") is not None

pytestmark = [
    pytest.mark.integration,
    pytest.mark.core_integration,
    pytest.mark.skipif(
        not MIDDLEWARE_AVAILABLE,
        reason="Middleware module is not present in the core runtime",
    ),
]


def _build_app() -> FastAPI:
    module = import_module("runtime.core.middleware")
    register_middleware = module.register_middleware

    app = FastAPI(title="Middleware Integration Test")
    register_middleware(app)
    return app


def test_exports_available() -> None:
    module = import_module("runtime.core.middleware")
    process_middleware = module.ProcessTimeMiddleware
    service_middleware = module.ServiceHeaderMiddleware
    register_middleware = module.register_middleware

    from starlette.middleware.base import BaseHTTPMiddleware

    assert issubclass(process_middleware, BaseHTTPMiddleware)
    assert issubclass(service_middleware, BaseHTTPMiddleware)
    assert callable(register_middleware)


def test_register_middleware_adds_expected_headers() -> None:
    app = _build_app()
    client = TestClient(app)

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"status": "ok"}

    response = client.get("/ping")

    assert response.status_code == status.HTTP_200_OK
    assert "X-Process-Time" in response.headers
    assert response.headers.get("X-Service") == "Middleware Integration Test"
    assert response.headers.get("X-Custom-Header") == "RapidKit"


def test_service_header_can_be_overridden() -> None:
    module = import_module("runtime.core.middleware")
    service_middleware = module.ServiceHeaderMiddleware

    app = FastAPI(title="Default Title")
    app.add_middleware(service_middleware, service_name="Override Service")

    @app.get("/value")
    def value() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)
    response = client.get("/value")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("X-Service") == "Override Service"


def test_register_middleware_health_route() -> None:
    health_spec = importlib.util.find_spec("src.health.middleware")
    if health_spec is None:
        pytest.skip("Middleware health module not present in runtime")

    health_module = import_module("src.health.middleware")
    register_middleware_health = health_module.register_middleware_health

    app = FastAPI(title="Health Test")
    register_middleware_health(app)

    client = TestClient(app)
    # CMS uses the canonical public prefix for module-level health routes
    # (e.g. /api/health/module/<module>). Accept that path.
    response = client.get("/api/health/module/middleware")

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload.get("status") == "ok"
    assert payload.get("module") == "middleware"

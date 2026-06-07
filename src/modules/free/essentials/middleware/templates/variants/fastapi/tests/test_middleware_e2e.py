"""End-to-end smoke tests for the generated FastAPI middleware module."""

from __future__ import annotations

import pytest

SUCCESS_STATUS_CODE = 200

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
except (RuntimeError, ModuleNotFoundError) as exc:  # pragma: no cover - optional dependency
    message = str(exc).lower()
    missing_name = getattr(exc, "name", "")
    if "httpx" in message or missing_name == "httpx":
        pytest.skip("httpx is required for FastAPI TestClient", allow_module_level=True)
    raise

pytestmark = [pytest.mark.e2e, pytest.mark.template_e2e]


def _build_app(config=None) -> FastAPI:
    from src.modules.free.essentials.middleware.middleware import (
        MiddlewareConfig,
        register_middleware,
    )

    app = FastAPI(title="Middleware E2E")
    runtime_config = config or MiddlewareConfig(service_name="Middleware E2E")
    register_middleware(app, config=runtime_config)

    @app.get("/middleware-e2e")
    def middleware_e2e() -> dict[str, str]:
        return {"status": "ok"}

    return app


def test_middleware_headers_are_applied_end_to_end() -> None:
    client = TestClient(_build_app())

    response = client.get("/middleware-e2e")

    assert response.status_code == SUCCESS_STATUS_CODE
    assert response.json() == {"status": "ok"}
    assert "X-Process-Time" in response.headers
    assert response.headers["X-Service"] == "Middleware E2E"
    assert response.headers["X-Custom-Header"] == "RapidKit"
    assert response.headers["X-Powered-By"] == "RapidKit"


def test_middleware_can_be_disabled_end_to_end() -> None:
    from src.modules.free.essentials.middleware.middleware import MiddlewareConfig

    client = TestClient(_build_app(MiddlewareConfig(enabled=False)))

    response = client.get("/middleware-e2e")

    assert response.status_code == SUCCESS_STATUS_CODE
    assert "X-Process-Time" not in response.headers
    assert "X-Service" not in response.headers
    assert "X-Custom-Header" not in response.headers

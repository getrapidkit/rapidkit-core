"""FastAPI adapter integration tests for Security Headers."""

from __future__ import annotations

from http import HTTPStatus

import pytest

fastapi = pytest.importorskip("fastapi")
testclient = pytest.importorskip("fastapi.testclient")

FastAPI = fastapi.FastAPI
TestClient = testclient.TestClient


def test_register_fastapi_applies_headers(fastapi_adapter) -> None:
    runtime_module, _ = fastapi_adapter

    app = FastAPI()

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"status": "ok"}

    runtime_module.register_fastapi(app)

    client = TestClient(app)
    response = client.get("/ping")
    assert response.status_code == HTTPStatus.OK
    assert response.headers["X-Frame-Options"] == "DENY"
    assert app.state.security_headers_enabled is True


def test_settings_override_csp(fastapi_adapter) -> None:
    runtime_module, _ = fastapi_adapter
    app = FastAPI()
    settings = runtime_module.SecurityHeadersSettings(
        content_security_policy="default-src 'self' https://cdn.example",  # noqa: S105 - test data
    )
    runtime_module.register_fastapi(app, config=settings)

    client = TestClient(app)
    response = client.get("/security-headers/headers")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["Content-Security-Policy"] == "default-src 'self' https://cdn.example"


def test_invalid_configuration_raises(fastapi_adapter) -> None:
    runtime_module, _ = fastapi_adapter
    with pytest.raises(TypeError):
        runtime_module.configure_security_headers(config=object())


def test_routes_expose_health(fastapi_adapter) -> None:
    runtime_module, routes_module = fastapi_adapter
    app = FastAPI()
    runtime_module.register_fastapi(app)
    app.include_router(routes_module.build_router())

    client = TestClient(app)
    response = client.get("/security-headers/health")
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["metrics"]["header_count"] > 0

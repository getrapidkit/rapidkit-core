"""Integration coverage for the Auth Core module."""

from __future__ import annotations

import importlib
import importlib.util

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.template_integration]

from src.modules.free.auth.core.auth.core import (  # type: ignore[import]
    AuthCoreRuntime,
    describe_auth_core,
    list_auth_core_features,
    load_settings,
)
from src.health.auth_core import register_auth_core_health  # type: ignore[import]


PEPPER_VALUE = "integration-test-static-pepper"


def _prepare_runtime(monkeypatch: pytest.MonkeyPatch) -> AuthCoreRuntime:
    monkeypatch.setenv("RAPIDKIT_AUTH_CORE_PEPPER", PEPPER_VALUE)
    settings = load_settings()
    return AuthCoreRuntime(settings)


def test_describe_auth_core_contains_features(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = _prepare_runtime(monkeypatch)
    payload = describe_auth_core(runtime.settings)

    assert payload["module"] == "auth_core"
    assert payload["pepper_configured"] is True
    assert set(payload["features"]).issuperset({"password_hashing", "token_signing"})


def test_list_auth_core_features() -> None:
    features = list_auth_core_features()
    assert "password_hashing" in features
    assert "policy_enforcement" in features


def test_password_hash_and_verify(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = _prepare_runtime(monkeypatch)
    encoded = runtime.hash_password("ValidPassword123")

    assert runtime.verify_password("ValidPassword123", encoded) is True
    assert runtime.verify_password("other", encoded) is False


def test_issue_and_verify_token(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = _prepare_runtime(monkeypatch)

    token = runtime.issue_token("user-123", scopes=("read",), ttl_seconds=5)
    payload = runtime.verify_token(token)

    assert payload["sub"] == "user-123"
    assert payload["scopes"] == ["read"]


@pytest.mark.skipif(
    importlib.util.find_spec("fastapi") is None,
    reason="FastAPI not installed",
)
def test_auth_core_health_router_registration(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi import FastAPI

    monkeypatch.setenv("RAPIDKIT_AUTH_CORE_PEPPER", PEPPER_VALUE)

    app = FastAPI()
    register_auth_core_health(app)

    paths = {route.path for route in app.routes}
    assert "/api/health/module/auth-core" in paths


@pytest.mark.skipif(
    importlib.util.find_spec("fastapi") is None,
    reason="FastAPI not installed",
)
def test_auth_core_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi import FastAPI, status
    from fastapi.testclient import TestClient

    monkeypatch.setenv("RAPIDKIT_AUTH_CORE_PEPPER", PEPPER_VALUE)

    app = FastAPI()

    from src.modules.free.auth.core.routers.auth_core import router  # type: ignore[import]

    app.include_router(router)
    client = TestClient(app)

    meta_response = client.get("/api/auth/core/metadata")
    assert meta_response.status_code == status.HTTP_200_OK
    metadata = meta_response.json()
    assert metadata["module"] == "auth_core"
    assert metadata["pepper_configured"] is True

    features_response = client.get("/api/auth/core/features")
    assert features_response.status_code == status.HTTP_200_OK
    assert "features" in features_response.json()

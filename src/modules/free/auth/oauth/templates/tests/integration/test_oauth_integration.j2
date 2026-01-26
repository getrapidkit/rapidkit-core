"""Integration coverage for the OAuth module."""

from __future__ import annotations

import urllib.parse

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.template_integration]

ENV_VARS = {
    "GOOGLE_OAUTH_CLIENT_ID": "google-id",
    "GOOGLE_OAUTH_CLIENT_SECRET": "google-secret",
    "GITHUB_OAUTH_CLIENT_ID": "github-id",
    "GITHUB_OAUTH_CLIENT_SECRET": "github-secret",
}


def _prime_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in ENV_VARS.items():
        monkeypatch.setenv(key, value)


def test_runtime_describe_oauth(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.modules.free.auth.oauth.oauth import OAuthRuntime, describe_oauth, load_oauth_settings

    _prime_environment(monkeypatch)

    settings = load_oauth_settings()
    runtime = OAuthRuntime(settings)

    metadata = runtime.metadata()

    assert metadata["provider_count"] >= 2
    assert "google" in metadata["providers"]
    assert "token_exchange_helpers" in metadata["features"]

    described = describe_oauth(settings)
    assert described["redirect_base_url"].startswith("https://")


def test_fastapi_oauth_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi import FastAPI, status
    from fastapi.testclient import TestClient

    from src.modules.free.auth.oauth.routers.oauth import create_router

    _prime_environment(monkeypatch)

    app = FastAPI()
    app.include_router(create_router())
    client = TestClient(app, follow_redirects=False)

    providers_resp = client.get("/oauth/providers")
    assert providers_resp.status_code == status.HTTP_200_OK
    providers = providers_resp.json()
    assert "google" in providers
    assert providers["google"]["authorize_url"].startswith("https://")

    authorize_resp = client.get("/oauth/google/authorize")
    assert authorize_resp.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    location = authorize_resp.headers["location"]
    parsed = urllib.parse.urlparse(location)
    query = urllib.parse.parse_qs(parsed.query)
    state = query["state"][0]

    callback_resp = client.get(f"/oauth/google/callback?state={state}")
    assert callback_resp.status_code == status.HTTP_200_OK
    assert callback_resp.json()["provider"] == "google"

    invalid_state = client.get("/oauth/google/callback?state=invalid-state")
    assert invalid_state.status_code == status.HTTP_400_BAD_REQUEST

    unknown_provider = client.get("/oauth/unknown/authorize")
    assert unknown_provider.status_code == status.HTTP_404_NOT_FOUND


def test_oauth_health_router(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi import FastAPI, status
    from fastapi.testclient import TestClient

    from src.health.oauth import register_oauth_health

    _prime_environment(monkeypatch)

    app = FastAPI()
    register_oauth_health(app)
    client = TestClient(app)

    response = client.get("/api/health/module/oauth")
    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["provider_count"] >= 1

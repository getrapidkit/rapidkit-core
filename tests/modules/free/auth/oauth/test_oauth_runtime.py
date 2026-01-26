"""Tests for the OAuth runtime scaffolding."""

from __future__ import annotations

import importlib.util
import sys
from http import HTTPStatus
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.free.auth.oauth import generate


def _load_module(module_name: str, path: Path):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


@pytest.fixture()
def rendered_modules(tmp_path, monkeypatch):  # type: ignore[no-untyped-def]
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "gid")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "gsecret")
    monkeypatch.setenv("GITHUB_OAUTH_CLIENT_ID", "ghid")
    monkeypatch.setenv("GITHUB_OAUTH_CLIENT_SECRET", "ghsecret")

    config = generate.load_module_config()
    renderer = generate.TemplateRenderer()
    context = generate.build_base_context(config)

    generate.generate_vendor_files(config, tmp_path, renderer, context)
    generate.generate_variant_files(config, "fastapi", tmp_path, renderer, context)

    vendor_root = tmp_path / ".rapidkit" / "vendor" / config["name"] / config["version"]
    vendor_path = vendor_root / "src/modules/free/auth/oauth/oauth.py"
    fastapi_path = tmp_path / "src/modules/free/auth/oauth/oauth.py"

    oauth_vendor = _load_module("generated_oauth_vendor", vendor_path)
    oauth_fastapi = _load_module("generated_oauth_fastapi", fastapi_path)

    # Ensure the FastAPI runtime mirrors the vendor defaults for reuse in tests.
    oauth_fastapi._runtime = oauth_fastapi.OAuthRuntime(oauth_fastapi.load_oauth_settings())

    return oauth_vendor, oauth_fastapi


def test_load_oauth_settings(rendered_modules):  # type: ignore[no-untyped-def]
    oauth_vendor, _ = rendered_modules
    settings = oauth_vendor.load_oauth_settings()

    assert settings.redirect_base_url == "https://example.com/oauth"
    assert set(settings.providers) == {"google", "github"}

    google = settings.providers["google"]
    assert google.client_id == "gid"
    assert google.client_secret == "gsecret"
    assert "openid" in google.scopes


def test_runtime_state_validation(rendered_modules):  # type: ignore[no-untyped-def]
    oauth_vendor, _ = rendered_modules
    settings = oauth_vendor.load_oauth_settings({"state_ttl_seconds": 1})
    runtime = oauth_vendor.OAuthRuntime(settings)

    state = runtime.issue_state("google", {"user_id": "123"})
    metadata = runtime.validate_callback("google", state)
    assert metadata["user_id"] == "123"

    with pytest.raises(ValueError):
        runtime.validate_callback("google", "invalid-state")


def test_fastapi_router_behaviour(rendered_modules):  # type: ignore[no-untyped-def]
    _, oauth_fastapi = rendered_modules

    app = FastAPI()
    app.include_router(oauth_fastapi.create_router())
    client = TestClient(app)

    providers_response = client.get("/oauth/providers")
    assert providers_response.status_code == HTTPStatus.OK
    assert "google" in providers_response.json()

    authorize_response = client.get(
        "/oauth/google/authorize",
        follow_redirects=False,
    )
    assert authorize_response.status_code == HTTPStatus.TEMPORARY_REDIRECT
    target = authorize_response.headers["location"]
    assert target.startswith("https://accounts.google.com/")

    state = oauth_fastapi._runtime.issue_state("google", {"user_id": "abc"})
    callback_response = client.get(f"/oauth/google/callback?state={state}")
    assert callback_response.status_code == HTTPStatus.OK
    assert callback_response.json()["metadata"]["user_id"] == "abc"

    missing_response = client.get("/oauth/unknown/callback?state=test")
    assert missing_response.status_code == HTTPStatus.BAD_REQUEST

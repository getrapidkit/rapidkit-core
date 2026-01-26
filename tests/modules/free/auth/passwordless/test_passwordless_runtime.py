"""Tests for the Passwordless runtime scaffolding."""

from __future__ import annotations

import importlib.util
import sys
from http import HTTPStatus
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.free.auth.passwordless import generate


def _load_module(module_name: str, path: Path):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


@pytest.fixture()
def rendered_modules(tmp_path):  # type: ignore[no-untyped-def]
    config = generate.load_module_config()
    renderer = generate.TemplateRenderer()
    context = generate.build_base_context(config)

    generate.generate_vendor_files(config, tmp_path, renderer, context)
    generate.generate_variant_files(config, "fastapi", tmp_path, renderer, context)

    vendor_root = tmp_path / ".rapidkit" / "vendor" / config["name"] / config["version"]
    vendor_path = vendor_root / "src/modules/free/auth/passwordless/passwordless.py"
    fastapi_path = tmp_path / "src/modules/free/auth/passwordless/passwordless.py"

    passwordless_vendor = _load_module("generated_passwordless_vendor", vendor_path)
    passwordless_fastapi = _load_module("generated_passwordless_fastapi", fastapi_path)

    passwordless_fastapi._runtime = passwordless_fastapi.PasswordlessRuntime(  # type: ignore[attr-defined]
        passwordless_fastapi.load_passwordless_settings()
    )

    return passwordless_vendor, passwordless_fastapi


def test_passwordless_issue_and_verify(monkeypatch, rendered_modules):  # type: ignore[no-untyped-def]
    passwordless_vendor, _ = rendered_modules

    settings = passwordless_vendor.load_passwordless_settings()
    runtime = passwordless_vendor.PasswordlessRuntime(settings)

    token = runtime.issue_code(
        "user@example.com",
        delivery_method="email",
        metadata={"channel": "email"},
    )
    assert token.identifier == "user@example.com"
    assert token.delivery_method == "email"
    assert len(token.code) == settings.token_length
    assert token.metadata["channel"] == "email"

    with pytest.raises(ValueError):
        runtime.issue_code("user@example.com", delivery_method="email")

    verified = runtime.verify_code("user@example.com", token.code)
    assert verified.token_id == token.token_id

    with pytest.raises(ValueError):
        runtime.verify_code("user@example.com", token.code)

    token_expiring = runtime.issue_code("next@example.com", delivery_method="email")
    monkeypatch.setattr(
        passwordless_vendor.time,
        "time",
        lambda: token_expiring.expires_at + 1,
    )
    with pytest.raises(ValueError):
        runtime.verify_code("next@example.com", token_expiring.code)


def test_fastapi_passwordless_endpoints(rendered_modules):  # type: ignore[no-untyped-def]
    _, passwordless_fastapi = rendered_modules

    app = FastAPI()
    app.include_router(passwordless_fastapi.create_router())
    client = TestClient(app)

    issue_resp = client.post(
        "/passwordless/tokens",
        json={"identifier": "test@example.com", "delivery_method": "email"},
    )
    assert issue_resp.status_code == HTTPStatus.CREATED
    payload = issue_resp.json()
    token_id = payload["token_id"]
    code = payload["code"]

    cooldown_resp = client.post(
        "/passwordless/tokens",
        json={"identifier": "test@example.com", "delivery_method": "email"},
    )
    assert cooldown_resp.status_code == HTTPStatus.BAD_REQUEST

    verify_resp = client.post(
        "/passwordless/verify",
        json={
            "identifier": "test@example.com",
            "code": code,
            "delivery_method": "email",
        },
    )
    assert verify_resp.status_code == HTTPStatus.OK
    assert verify_resp.json()["token_id"] == token_id

    replay_resp = client.post(
        "/passwordless/verify",
        json={
            "identifier": "test@example.com",
            "code": code,
            "delivery_method": "email",
        },
    )
    assert replay_resp.status_code == HTTPStatus.BAD_REQUEST

    magic_link_resp = client.post(
        "/passwordless/magic-link",
        json={"identifier": "other@example.com"},
    )
    assert magic_link_resp.status_code == HTTPStatus.CREATED
    assert "url" in magic_link_resp.json()

    invalid_resp = client.post(
        "/passwordless/verify",
        json={"identifier": "missing@example.com", "code": "000000"},
    )
    assert invalid_resp.status_code == HTTPStatus.BAD_REQUEST

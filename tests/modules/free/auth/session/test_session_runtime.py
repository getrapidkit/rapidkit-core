"""Tests for the Session runtime scaffolding."""

from __future__ import annotations

import importlib.util
import sys
from http import HTTPStatus
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.free.auth.session import generate


def _load_module(module_name: str, path: Path):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


@pytest.fixture()
def rendered_modules(tmp_path, monkeypatch):  # type: ignore[no-untyped-def]
    monkeypatch.setenv("RAPIDKIT_SESSION_SECRET", "super-secret")

    config = generate.load_module_config()
    renderer = generate.TemplateRenderer()
    context = generate.build_base_context(config)

    generate.generate_vendor_files(config, tmp_path, renderer, context)
    generate.generate_variant_files(config, "fastapi", tmp_path, renderer, context)

    vendor_root = tmp_path / ".rapidkit" / "vendor" / config["name"] / config["version"]
    vendor_path = vendor_root / "src/modules/free/auth/session/session.py"
    fastapi_path = tmp_path / "src/modules/free/auth/session/session.py"

    session_vendor = _load_module("generated_session_vendor", vendor_path)
    session_fastapi = _load_module("generated_session_fastapi", fastapi_path)

    session_fastapi._runtime = session_fastapi.SessionRuntime(
        session_fastapi.load_session_settings()
    )

    return session_vendor, session_fastapi


def test_session_issue_and_verify(rendered_modules):  # type: ignore[no-untyped-def]
    session_vendor, _ = rendered_modules

    settings = session_vendor.load_session_settings()
    runtime = session_vendor.SessionRuntime(settings)

    envelope = runtime.issue_session("user-123", payload={"role": "admin"})
    assert envelope.cookie["name"] == "rapidkit_session"

    record = runtime.verify_session_token(envelope.token)
    assert record.user_id == "user-123"
    assert record.payload["role"] == "admin"

    runtime.revoke_session(record.session_id)
    with pytest.raises(ValueError):
        runtime.verify_session_token(envelope.token)


def test_fastapi_session_endpoints(rendered_modules):  # type: ignore[no-untyped-def]
    _, session_fastapi = rendered_modules

    app = FastAPI()
    app.include_router(session_fastapi.create_router())
    client = TestClient(app)

    create_resp = client.post("/sessions/", json={"user_id": "99", "claims": {"scope": "rw"}})
    assert create_resp.status_code == HTTPStatus.CREATED
    refresh_token = create_resp.json()["refresh_token"]

    with client:
        token = client.cookies.get("rapidkit_session")
    assert token is not None

    current_resp = client.get("/sessions/current", cookies={"rapidkit_session": token})
    assert current_resp.status_code == HTTPStatus.OK
    assert current_resp.json()["user_id"] == "99"

    refresh_resp = client.post(
        "/sessions/refresh",
        json={"refresh_token": refresh_token},
        cookies={"rapidkit_session": token},
    )
    assert refresh_resp.status_code == HTTPStatus.OK
    new_refresh = refresh_resp.json()["refresh_token"]
    assert new_refresh != refresh_token

    revoke_resp = client.delete(f"/sessions/{create_resp.json()['session_id']}")
    assert revoke_resp.status_code == HTTPStatus.NO_CONTENT

    invalid_resp = client.get("/sessions/current", cookies={"rapidkit_session": token})
    assert invalid_resp.status_code == HTTPStatus.UNAUTHORIZED

    missing_resp = client.post("/sessions/refresh", json={"refresh_token": "bad-token"})
    assert missing_resp.status_code == HTTPStatus.BAD_REQUEST

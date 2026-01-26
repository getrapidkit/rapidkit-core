"""Integration coverage for the Session module."""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.template_integration]


def test_describe_session_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDKIT_SESSION_SECRET", "template-session-secret")

    from src.modules.free.auth.session.session import (
        SessionRuntime,
        describe_session,
        list_session_features,
        load_session_settings,
    )

    settings = load_session_settings()
    runtime = SessionRuntime(settings)
    metadata = runtime.metadata()

    assert metadata["module"] == "session"
    assert metadata["session_ttl_seconds"] == settings.session_ttl_seconds
    assert set(metadata["features"]).issuperset(set(list_session_features()))
    assert metadata["supports_refresh_tokens"] is True

    described = describe_session(settings)
    assert described["cookie"]["name"] == settings.cookie.name


def test_fastapi_session_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDKIT_SESSION_SECRET", "template-session-secret")

    from fastapi import FastAPI, status
    from fastapi.testclient import TestClient

    from src.modules.free.auth.session.routers.session import create_router

    app = FastAPI()
    app.include_router(create_router())
    client = TestClient(app)

    metadata_response = client.get("/sessions/metadata")
    assert metadata_response.status_code == status.HTTP_200_OK
    assert metadata_response.json()["supports_refresh_tokens"] is True

    features_response = client.get("/sessions/features")
    assert features_response.status_code == status.HTTP_200_OK
    assert "signed_tokens" in features_response.json()["features"]

    create_response = client.post(
        "/sessions/",
        json={"user_id": "55", "claims": {"tier": "free"}},
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    payload = create_response.json()
    refresh_token = payload["refresh_token"]

    session_cookie = client.cookies.get("rapidkit_session")
    assert session_cookie is not None

    current_response = client.get("/sessions/current", cookies={"rapidkit_session": session_cookie})
    assert current_response.status_code == status.HTTP_200_OK
    assert current_response.json()["user_id"] == "55"

    refresh_response = client.post(
        "/sessions/refresh",
        json={"refresh_token": refresh_token},
        cookies={"rapidkit_session": session_cookie},
    )
    assert refresh_response.status_code == status.HTTP_200_OK
    assert refresh_response.json()["refresh_token"] != refresh_token

    revoke_response = client.delete(f"/sessions/{payload['session_id']}")
    assert revoke_response.status_code == status.HTTP_204_NO_CONTENT

    missing_response = client.get(
        "/sessions/current",
        cookies={"rapidkit_session": session_cookie},
    )
    assert missing_response.status_code == status.HTTP_401_UNAUTHORIZED


def test_session_health_router(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDKIT_SESSION_SECRET", "template-session-secret")

    from fastapi import FastAPI, status
    from fastapi.testclient import TestClient

    from src.health.session import register_session_health

    app = FastAPI()
    register_session_health(app)
    client = TestClient(app)

    response = client.get("/api/health/module/session")
    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["cookie"]["name"] == "rapidkit_session"

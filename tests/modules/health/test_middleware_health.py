from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest
from core.health import middleware as middleware_health
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

EXPECTED_MIDDLEWARE_COUNT = 3


class _FixedDateTime:
    @staticmethod
    def now(tz: timezone) -> datetime:
        return datetime(2024, 1, 2, 3, 4, 5, tzinfo=tz)


class _BrokenDateTime:
    @staticmethod
    def now(tz: timezone) -> datetime:  # pragma: no cover - invoked via test
        _ = tz
        raise RuntimeError("boom")


def test_register_middleware_health_adds_route() -> None:
    app = FastAPI()
    middleware_health.register_middleware_health(app)

    client = TestClient(app)
    response = client.get("/api/health/module/middleware")
    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["module"] == "middleware"
    assert payload["status"] == "ok"


def test_middleware_health_check_returns_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(middleware_health, "datetime", _FixedDateTime)

    payload = asyncio.run(middleware_health.middleware_health_check())
    assert payload["checked_at"] == "2024-01-02T03:04:05+00:00"
    assert payload["middleware_count"] == EXPECTED_MIDDLEWARE_COUNT


def test_middleware_health_check_handles_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    app = FastAPI()
    middleware_health.register_middleware_health(app)

    monkeypatch.setattr(middleware_health, "datetime", _BrokenDateTime)

    client = TestClient(app)
    response = client.get("/api/health/module/middleware")

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    body = response.json()
    assert body["status"] == "error"
    assert body["detail"]

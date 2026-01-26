"""Adapter integration tests for Observability Core."""

from __future__ import annotations

from http import HTTPStatus

import pytest

fastapi = pytest.importorskip("fastapi")
testclient = pytest.importorskip("fastapi.testclient")

FastAPI = fastapi.FastAPI
TestClient = testclient.TestClient


def test_fastapi_endpoints_expose_runtime_state(generated_observability_modules) -> None:
    modules = generated_observability_modules
    fastapi_module = modules.fastapi_runtime

    fastapi_module.get_runtime(refresh=True)
    config = fastapi_module.ObservabilityCoreConfig.from_mapping(
        {
            "service_name": "fastapi-observability",
            "environment": "test",
        }
    )

    app = FastAPI()
    fastapi_module.register_fastapi(app, config)

    runtime = fastapi_module.get_runtime()
    runtime.emit_event("startup")
    with runtime.span("bootstrap"):
        pass
    runtime.increment_counter("api_requests_total")

    client = TestClient(app)

    health = client.get("/observability-core/health")
    assert health.status_code == HTTPStatus.OK
    assert health.json()["service_name"] == "fastapi-observability"

    metrics = client.get("/observability-core/metrics")
    assert metrics.status_code == HTTPStatus.OK
    payload = metrics.json()
    assert payload["payload"]
    assert payload["content_type"]

    raw_metrics = client.get("/observability-core/metrics/raw")
    assert raw_metrics.status_code == HTTPStatus.OK
    assert raw_metrics.text.strip()

    events = client.get("/observability-core/events?limit=5")
    assert events.status_code == HTTPStatus.OK
    assert any(event["name"] == "startup" for event in events.json())

    created = client.post(
        "/observability-core/events", json={"name": "api.call", "severity": "WARN"}
    )
    assert created.status_code == HTTPStatus.OK
    assert created.json()["name"] == "api.call"

    traces = client.get("/observability-core/traces")
    assert traces.status_code == HTTPStatus.OK
    assert isinstance(traces.json(), list)


def test_router_accepts_mapping_configuration(generated_observability_modules) -> None:
    modules = generated_observability_modules
    fastapi_module = modules.fastapi_runtime
    routes_module = modules.fastapi_routes

    fastapi_module.get_runtime(refresh=True)
    router = routes_module.build_router(
        {
            "service_name": "mapping-app",
            "metrics": {"endpoint": "/custom-metrics"},
        }
    )

    runtime = fastapi_module.get_runtime()
    assert router.prefix == "/observability-core"
    assert runtime.config.service_name == "mapping-app"
    assert runtime.config.metrics.endpoint == "/custom-metrics"

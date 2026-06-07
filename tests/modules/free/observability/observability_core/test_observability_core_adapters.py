"""Adapter integration tests for Observability Core."""

from __future__ import annotations

from http import HTTPStatus

import pytest

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

FastAPI = fastapi.FastAPI
ASGITransport = httpx.ASGITransport
AsyncClient = httpx.AsyncClient


@pytest.mark.asyncio
async def test_fastapi_endpoints_expose_runtime_state(generated_observability_modules) -> None:
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

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        health = await client.get("/observability-core/health")
        metrics = await client.get("/observability-core/metrics")
        raw_metrics = await client.get("/observability-core/metrics/raw")
        events = await client.get("/observability-core/events?limit=5")
        created = await client.post(
            "/observability-core/events", json={"name": "api.call", "severity": "WARN"}
        )
        traces = await client.get("/observability-core/traces")

    assert health.status_code == HTTPStatus.OK
    assert health.json()["service_name"] == "fastapi-observability"

    assert metrics.status_code == HTTPStatus.OK
    payload = metrics.json()
    assert payload["payload"]
    assert payload["content_type"]

    assert raw_metrics.status_code == HTTPStatus.OK
    assert raw_metrics.text.strip()

    assert events.status_code == HTTPStatus.OK
    assert any(event["name"] == "startup" for event in events.json())

    assert created.status_code == HTTPStatus.OK
    assert created.json()["name"] == "api.call"

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

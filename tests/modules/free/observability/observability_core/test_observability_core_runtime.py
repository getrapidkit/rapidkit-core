"""Runtime behaviour tests for the Observability Core vendor payload."""

from __future__ import annotations

from time import sleep


def _fresh_runtime(modules):
    runtime_module = modules.base
    runtime_module.get_runtime(refresh=True)
    return runtime_module


def test_runtime_tracks_metrics_events_and_spans(generated_observability_modules) -> None:
    runtime_module = _fresh_runtime(generated_observability_modules)
    config = runtime_module.ObservabilityCoreConfig.from_mapping(
        {
            "tracing": {
                "enabled": True,
                "sample_ratio": 1.0,
            }
        }
    )
    runtime = runtime_module.ObservabilityCore(config)

    runtime.increment_counter("requests_total")
    runtime.increment_counter("requests_total", value=2, labels={"route": "health"})
    runtime.set_gauge("in_flight_requests", 5)
    runtime.observe_histogram("request_duration_seconds", 0.42)

    with runtime.span("db.query", attributes={"table": "users"}):
        sleep(0.001)

    emitted = runtime.emit_event("user.login", severity="INFO", attributes={"user_id": "123"})
    assert emitted["name"] == "user.login"

    payload, content_type = runtime.export_metrics()
    assert isinstance(payload, str) and payload.strip()
    assert isinstance(content_type, str) and content_type

    spans = runtime.recent_spans(limit=5)
    assert spans and spans[-1]["name"] == "db.query"
    assert spans[-1]["duration_ms"] is None or spans[-1]["duration_ms"] >= 0

    events = runtime.recent_events()
    assert events and events[-1]["name"] == "user.login"

    health = runtime.health_check()
    assert health["module"] == runtime_module.MODULE_NAME
    assert health["metrics"]["endpoint"] == runtime.config.metrics.endpoint
    assert "recent" in health["events"] and health["events"]["recent"]
    assert "recent" in health["tracing"]

    metadata = runtime.metadata()
    assert metadata["module"] == runtime_module.MODULE_NAME
    assert metadata["config"]["retry_attempts"] == runtime.config.retry_attempts


def test_get_runtime_refreshes_configuration(generated_observability_modules) -> None:
    runtime_module = _fresh_runtime(generated_observability_modules)

    custom = runtime_module.ObservabilityCoreConfig.from_mapping(
        {
            "service_name": "payments",
            "environment": "staging",
            "retry_attempts": "7",
            "metrics": {"enabled": False},
        }
    )

    refreshed = runtime_module.get_runtime(custom, refresh=True)
    assert refreshed.config.service_name == "payments"
    assert refreshed.config.environment == "staging"
    assert refreshed.config.retry_attempts == 7
    assert refreshed.config.metrics.enabled is False

    cached = runtime_module.get_runtime()
    assert cached is refreshed

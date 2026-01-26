"""Health helper tests for the Observability Core vendor payload."""

from __future__ import annotations


def test_build_health_payload_validates_summary(generated_observability_modules) -> None:
    modules = generated_observability_modules
    health_module = modules.health
    payload = health_module.build_health_payload(
        service_name="service-a",
        environment="production",
        metrics={"exporter": "prometheus", "endpoint": "/metrics", "sample": "{}"},
        tracing={"enabled": True, "exporter": "console", "recent": []},
        events={"buffer_size": 10, "audit_enabled": False, "recent": []},
    )

    assert payload["module"] == modules.base.MODULE_NAME
    assert payload["service_name"] == "service-a"
    assert payload["environment"] == "production"
    assert payload["metrics"]["endpoint"] == "/metrics"


def test_merge_metrics_combines_payloads(generated_observability_modules) -> None:
    health_module = generated_observability_modules.health

    base = {"module": "observability_core", "metrics": {"exporter": "prometheus"}}
    merged = health_module.merge_metrics(base, {"endpoint": "/internal-metrics"})

    assert merged["metrics"]["exporter"] == "prometheus"
    assert merged["metrics"]["endpoint"] == "/internal-metrics"
    assert base["metrics"].get("endpoint") is None

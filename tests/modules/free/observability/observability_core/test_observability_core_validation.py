"""Validation tests for Observability Core."""

from __future__ import annotations

import pytest
from pydantic import ValidationError


def test_observability_core_config_from_mapping_sanitizes_invalid_shapes(
    generated_observability_modules,
) -> None:
    runtime_module = generated_observability_modules.base

    config = runtime_module.ObservabilityCoreConfig.from_mapping(
        {
            "service_name": "checkout",
            "environment": "production",
            "retry_attempts": "not-an-int",
            "resource_attributes": ["invalid"],
            "metrics": {"default_labels": {"team": "platform"}},
            "logging": {"level": "WARNING"},
            "events": {"buffer_size": 25},
        }
    )

    assert config.service_name == "checkout"
    assert config.environment == "production"
    assert config.retry_attempts == 3
    assert config.resource_attributes == {}
    assert config.metrics.default_labels == {"team": "platform"}
    assert config.logging.level == "WARNING"
    assert config.events.buffer_size == 25


def test_observability_core_event_schema_rejects_lowercase_severity(
    generated_observability_modules,
) -> None:
    types_module = generated_observability_modules.types

    with pytest.raises(ValidationError):
        types_module.ObservabilityEventCreate(name="checkout.failed", severity="warning")


def test_observability_core_metric_snapshot_requires_payload_and_content_type(
    generated_observability_modules,
) -> None:
    types_module = generated_observability_modules.types

    snapshot = types_module.ObservabilityMetricSnapshot(
        payload="requests_total 1",
        content_type="text/plain",
    )

    assert snapshot.payload == "requests_total 1"
    assert snapshot.content_type == "text/plain"

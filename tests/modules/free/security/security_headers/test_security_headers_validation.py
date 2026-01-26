"""Validation tests for Security Headers configuration models."""

from __future__ import annotations

import pytest

pydantic = pytest.importorskip("pydantic")
ValidationError = pydantic.ValidationError

MAX_AGE_OVERRIDE = 123


def test_permissions_policy_accepts_sequences(fastapi_adapter) -> None:
    runtime_module, _ = fastapi_adapter
    settings = runtime_module.SecurityHeadersSettings(
        permissions_policy={"camera": ["self", "https://cdn.example"]},
    )
    config = settings.to_runtime_config()
    assert config.permissions_policy["camera"] == ["self", "https://cdn.example"]


def test_invalid_type_rejected(fastapi_adapter) -> None:
    runtime_module, _ = fastapi_adapter
    with pytest.raises(ValidationError):
        runtime_module.SecurityHeadersSettings(strict_transport_security_max_age="abc")


def test_to_runtime_config_emits_dataclass(fastapi_adapter) -> None:
    runtime_module, _ = fastapi_adapter
    settings = runtime_module.SecurityHeadersSettings(
        strict_transport_security_max_age=MAX_AGE_OVERRIDE,
        permissions_policy={"microphone": "self"},
    )
    config = settings.to_runtime_config()
    assert isinstance(config, runtime_module.SecurityHeadersConfig)
    assert config.strict_transport_security_max_age == MAX_AGE_OVERRIDE
    assert config.permissions_policy["microphone"] == "self"

"""Override behaviour tests for Observability Core."""

from __future__ import annotations

from pathlib import Path

import pytest

from modules.free.observability.core import generate, overrides


def test_override_class_declared(module_root: Path) -> None:
    overrides_source = (module_root / "overrides.py").read_text(encoding="utf-8")
    assert "class ObservabilityCoreOverrides" in overrides_source


def test_env_overrides_mutate_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDKIT_OBSERVABILITY_SERVICE_NAME", "checkout")
    monkeypatch.setenv("RAPIDKIT_OBSERVABILITY_ENVIRONMENT", "staging")
    monkeypatch.setenv("RAPIDKIT_OBSERVABILITY_RETRY_ATTEMPTS", "5")
    monkeypatch.setenv("RAPIDKIT_OBSERVABILITY_METRICS_ENABLED", "false")
    monkeypatch.setenv("RAPIDKIT_OBSERVABILITY_METRICS_ENDPOINT", "/internal")
    monkeypatch.setenv("RAPIDKIT_OBSERVABILITY_METRICS_BUCKETS", "0.1,1,5")

    generator = generate.ObservabilityModuleGenerator()
    config = generator.load_module_config()
    base_context = generator.build_base_context(config)

    applied = overrides.ObservabilityCoreOverrides().apply_base_context(base_context)
    defaults = applied[overrides.DEFAULTS_KEY]

    assert defaults["service_name"] == "checkout"
    assert defaults["environment"] == "staging"
    assert defaults["retry_attempts"] == 5
    assert defaults["metrics"]["enabled"] is False
    assert defaults["metrics"]["endpoint"] == "/internal"
    assert defaults["metrics"]["buckets"] == [0.1, 1.0, 5.0]


def test_override_state_keeps_default_when_env_absent() -> None:
    generator = generate.ObservabilityModuleGenerator()
    config = generator.load_module_config()
    base_context = generator.build_base_context(config)

    applied = overrides.ObservabilityCoreOverrides().apply_base_context(base_context)
    defaults = applied[overrides.DEFAULTS_KEY]

    assert defaults["service_name"] == base_context[overrides.DEFAULTS_KEY]["service_name"]
    assert (
        defaults["metrics"]["endpoint"]
        == base_context[overrides.DEFAULTS_KEY]["metrics"]["endpoint"]
    )

from __future__ import annotations

import importlib
from typing import Any

import pytest

from core.services import override_contracts
from core.services.override_contracts import (
    decorators as decorators_module,
    examples as examples_module,
)
from core.services.override_contracts.mixins import (
    ConfigurableOverrideMixin,
    ValidationOverrideMixin,
)


@pytest.fixture()
def fresh_registry(monkeypatch: pytest.MonkeyPatch) -> decorators_module.OverrideRegistry:
    registry = decorators_module.OverrideRegistry()
    monkeypatch.setattr(decorators_module, "_override_registry", registry)
    monkeypatch.setattr(override_contracts, "_override_registry", registry, raising=False)
    return registry


@pytest.fixture()
def reloaded_examples(fresh_registry: decorators_module.OverrideRegistry) -> Any:
    _ = fresh_registry
    return importlib.reload(examples_module)


def test_custom_debug_mode_honors_environment(
    reloaded_examples: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MYAPP_DEBUG", "true")
    assert reloaded_examples.custom_debug_mode() is True

    monkeypatch.setenv("MYAPP_DEBUG", "false")
    assert reloaded_examples.custom_debug_mode() is False


def test_custom_load_config_injects_additional_settings(reloaded_examples: Any) -> None:
    settings = reloaded_examples.CustomSettings()

    result = reloaded_examples.custom_load_config(settings)

    assert result["custom_feature"] is True
    assert result["environment"] == "production"
    assert result["app_name"] == "MyApp"


def test_custom_service_uses_mixin_for_original_calls(reloaded_examples: Any) -> None:
    service = reloaded_examples.CustomService()

    response = service.make_request("https://example.org")

    assert response["logged"] is True
    assert response["custom_header"] == "X-Custom-Service"
    assert response["status"] == "success"
    assert hasattr(service, "_original_make_request")
    with pytest.raises(AttributeError):
        service.call_original("nonexistent")


def test_configurable_override_mixin_applies_registered_method_overrides(
    fresh_registry: decorators_module.OverrideRegistry,
) -> None:
    _ = fresh_registry

    class BaseRequest:
        def __init__(self) -> None:
            self.base_init_called = True

        def make_request(self, url: str) -> dict[str, Any]:
            return {"url": url, "status": "base", "timeout": 10}

    class DerivedRequest(ConfigurableOverrideMixin, BaseRequest):
        def __init__(self) -> None:
            super().__init__()

    @override_contracts.override_method("DerivedRequest.make_request")
    def patched_request(self: DerivedRequest, url: str) -> dict[str, Any]:
        return {"url": url, "status": "patched", "timeout": getattr(self, "timeout", 999)}

    request = DerivedRequest()

    patched = request.make_request("https://patched.example")
    assert patched == {"url": "https://patched.example", "status": "patched", "timeout": 999}

    original = request.call_original("make_request", "https://patched.example")
    assert original == {"url": "https://patched.example", "status": "base", "timeout": 10}
    assert request.base_init_called is True


def test_validation_override_mixin_detects_signature_mismatch(
    fresh_registry: decorators_module.OverrideRegistry,
) -> None:
    _ = fresh_registry

    class BaseValidated:
        def compute(self, value: int) -> int:
            return value + 1

    class Validated(ValidationOverrideMixin, BaseValidated):
        def __init__(self) -> None:
            super().__init__()

    @override_contracts.override_method("Validated.compute")
    def bad_compute(self: Validated, value: int, extra: int) -> int:
        return self.call_original("compute", value) + extra

    instance = Validated()
    report = instance.validate_overrides()

    assert report["valid"] is True
    assert any("signature changed" in warning for warning in report["warnings"])


def test_get_original_setting_raises_without_override() -> None:
    class PlainSettings(ConfigurableOverrideMixin):
        def __init__(self) -> None:
            self.threshold = 1
            super().__init__()

    plain = PlainSettings()

    with pytest.raises(AttributeError) as excinfo:
        plain.get_original_setting("threshold")

    assert "No original setting 'threshold'" in str(excinfo.value)


def test_settings_manager_reports_setting_overrides(reloaded_examples: Any) -> None:
    override_contracts.override_setting("SettingsManager.features", setting_value=["basic", "pro"])(
        lambda: None
    )

    manager = reloaded_examples.SettingsManager()
    manager._load_setting_overrides()

    assert manager.features == ["basic", "pro"]
    assert manager.get_original_setting("features") == ["basic"]

    info = manager.get_override_info()
    assert {"setting": "features", "has_override": True} in info["setting_overrides"]
    assert any(item.get("method") == "features" for item in info["method_overrides"])


def test_demonstrate_overrides_produces_human_readable_output(
    reloaded_examples: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("MYAPP_DEBUG", "true")

    reloaded_examples.demonstrate_overrides()

    output = capsys.readouterr().out
    assert "Override Contracts Demo" in output
    assert "Custom Settings with decorators" in output
    assert "Custom Service with mixins" in output
    assert "Settings Manager with full overrides" in output

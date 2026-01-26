from __future__ import annotations

import types
from typing import Any

import pytest

from core.services import override_contracts
from core.services.override_contracts import decorators as decorators_module


@pytest.fixture()
def fresh_registry(monkeypatch: pytest.MonkeyPatch) -> decorators_module.OverrideRegistry:
    registry = decorators_module.OverrideRegistry()
    monkeypatch.setattr(decorators_module, "_override_registry", registry)
    monkeypatch.setattr(override_contracts, "_override_registry", registry, raising=False)
    return registry


def test_load_module_overrides_imports_expected_module(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_import(name: str, _package: str | None = None) -> types.ModuleType:
        calls.append(name)
        return types.ModuleType(name)

    monkeypatch.setattr("importlib.import_module", fake_import)

    override_contracts.load_module_overrides("settings")

    assert calls == ["modules.free.essentials.settings.overrides"]


def test_load_module_overrides_swallows_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_missing(name: str, _package: str | None = None) -> None:
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("importlib.import_module", raise_missing)

    override_contracts.load_module_overrides("nonexistent")


def test_load_module_overrides_logs_other_errors(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def raise_value_error(_name: str, _package: str | None = None) -> None:
        raise ValueError("boom")

    monkeypatch.setattr("importlib.import_module", raise_value_error)

    with caplog.at_level("WARNING", logger=override_contracts.LOGGER.name):
        override_contracts.load_module_overrides("faulty")

    assert any("faulty" in message and "boom" in message for message in caplog.messages)


def test_apply_module_overrides_invokes_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, Any] = {"modules": [], "targets": []}

    def fake_loader(module_name: str) -> None:
        calls["modules"].append(module_name)

    def fake_apply(target: Any) -> str:
        calls["targets"].append(target)
        return "wrapped"

    monkeypatch.setattr(override_contracts, "load_module_overrides", fake_loader)
    monkeypatch.setattr(override_contracts, "apply_overrides", fake_apply)

    class Sentinel:
        pass

    result = override_contracts.apply_module_overrides(Sentinel, "alpha")

    assert result == "wrapped"
    assert calls == {"modules": ["alpha"], "targets": [Sentinel]}


def test_apply_module_overrides_returns_module_for_module_targets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = types.ModuleType("sample")
    observed: dict[str, Any] = {"modules": [], "applied": []}

    def fake_loader(name: str) -> None:
        observed["modules"].append(name)

    def fake_apply(target: Any) -> Any:
        observed["applied"].append(target)
        return "should-not-be-returned"

    monkeypatch.setattr(override_contracts, "load_module_overrides", fake_loader)
    monkeypatch.setattr(override_contracts, "apply_overrides", fake_apply)

    result = override_contracts.apply_module_overrides(module, "beta")

    assert result is module
    assert observed["modules"] == ["beta"]
    assert observed["applied"] == []


def test_override_method_registers_and_marks_metadata(
    fresh_registry: decorators_module.OverrideRegistry,
) -> None:
    @override_contracts.override_method("Example.method")
    def replacement() -> str:
        return "patched"

    assert fresh_registry.get_method_override("Example.method") is replacement
    assert replacement._is_override is True  # type: ignore[attr-defined]
    assert replacement._override_target == "Example.method"  # type: ignore[attr-defined]


def test_override_setting_handles_value_and_callable(
    fresh_registry: decorators_module.OverrideRegistry,
) -> None:
    expected_value = 42
    override_contracts.override_setting("Example.VALUE", setting_value=expected_value)(lambda: None)

    @override_contracts.override_setting("Example.dynamic")
    def compute() -> str:
        return "dynamic"

    assert fresh_registry.get_setting_override("Example.VALUE") == expected_value
    stored_callable = fresh_registry.get_setting_override("Example.dynamic")
    assert callable(stored_callable)
    assert compute._is_setting_override is True  # type: ignore[attr-defined]
    assert compute._override_setting == "Example.dynamic"  # type: ignore[attr-defined]


def test_safe_override_validates_method_and_registers(
    fresh_registry: decorators_module.OverrideRegistry,
) -> None:
    class Base:
        def action(self) -> str:
            return "base"

    with pytest.raises(ValueError):
        override_contracts.safe_override(Base, "missing")(lambda *_: None)

    @override_contracts.safe_override(Base)
    def action(_self: Base) -> str:
        return "override"

    key = "Base.action"
    assert fresh_registry.get_method_override(key) is action
    assert action._safe_override_target is Base  # type: ignore[attr-defined]
    assert action._safe_override_method == "action"  # type: ignore[attr-defined]


def test_apply_overrides_applies_methods_and_settings(
    fresh_registry: decorators_module.OverrideRegistry,
) -> None:
    _ = fresh_registry

    class Parent:
        def greet(self) -> str:
            return "hi"

    class Child(Parent):
        MODE = "default"

    @override_contracts.override_method("Child.greet")
    def new_greet(_self: Child) -> str:
        return "hello"

    @override_contracts.override_setting("Child.MODE", setting_value="custom")
    def _unused() -> None:  # pragma: no cover - not called
        raise AssertionError

    mutated = decorators_module.apply_overrides(Child)

    assert mutated is Child
    assert Child.greet(Child()) == "hello"
    original = Child._original_greet  # type: ignore[attr-defined]
    assert original.__get__(Child(), Child)() == "hi"
    assert Child.MODE == "custom"
    assert Child._original_MODE == "default"  # type: ignore[attr-defined]


def test_integration_entrypoint_executes_successfully(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from core.services.override_contracts import integration_test as integration_module

    observed: dict[str, Any] = {}

    def fake_apply(target: Any, module_name: str) -> Any:
        observed["target"] = target
        observed["module"] = module_name
        return target

    monkeypatch.setattr(integration_module, "apply_module_overrides", fake_apply)

    integration_module.test_module_override_integration()

    captured = capsys.readouterr().out
    assert "Module override integration test passed" in captured
    assert observed == {
        "target": integration_module.TestService,
        "module": "settings",
    }

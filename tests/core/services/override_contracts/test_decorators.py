import types

import pytest

from core.services.override_contracts.decorators import (
    apply_overrides,
    get_override_registry,
    override_method,
    override_setting,
    safe_override,
)


@pytest.fixture(autouse=True)
def reset_override_registry():
    registry = get_override_registry()
    registry.method_overrides.clear()
    registry.setting_overrides.clear()


def test_override_method_registers_callable_metadata():
    class Source:
        def target(self) -> str:
            return "source"

    @override_method(Source.target)
    def custom(self):  # type: ignore[override]
        return "custom"

    registry = get_override_registry()
    recorded = registry.get_method_override("target")

    assert recorded is custom
    assert custom._is_override is True
    assert custom._override_target == "target"


def test_override_setting_supports_value_and_callable():
    @override_setting("Example.static", setting_value=42)
    def _unused():
        return -1

    @override_setting("Example.dynamic")
    def dynamic():
        return "dynamic-value"

    registry = get_override_registry()

    assert registry.get_setting_override("Example.static") == 42
    dynamic_override = registry.get_setting_override("Example.dynamic")
    assert callable(dynamic_override)
    assert dynamic_override() == "dynamic-value"
    assert dynamic._is_setting_override is True
    assert dynamic._override_setting == "Example.dynamic"


def test_safe_override_requires_existing_method():
    class Base:
        def greet(self) -> str:
            return "hello"

    with pytest.raises(ValueError):

        @safe_override(Base, "missing")
        def _override(self):  # pragma: no cover - executed via decorator
            return "never"

    @safe_override(Base)
    def greet(self):  # type: ignore[override]
        return "override"

    registry = get_override_registry()
    key = f"{Base.__name__}.greet"
    assert registry.get_method_override(key) is greet
    assert greet._safe_override_target is Base
    assert greet._safe_override_method == "greet"


def test_apply_overrides_replaces_methods_and_settings():
    class Sample:
        value = 1

        @classmethod
        def compute(cls) -> int:
            return cls.value + 1

        def greet(self) -> str:
            return "original"

    @override_method("Sample.greet")
    def new_greet(self):  # type: ignore[override]
        return "overridden"

    @override_setting("Sample.value", setting_value=99)
    def _static_value():
        return -1

    @override_setting("Sample.compute")
    def compute_override(cls):  # type: ignore[override]
        return cls.value * 2

    apply_overrides(Sample)

    instance = Sample()
    assert instance.greet() == "overridden"
    assert isinstance(Sample._original_greet, types.FunctionType)
    assert Sample._original_greet(instance) == "original"

    assert Sample.value == 99
    assert Sample._original_value == 1

    assert Sample.compute() == 198
    original_compute = Sample._original_compute
    assert original_compute() == 100

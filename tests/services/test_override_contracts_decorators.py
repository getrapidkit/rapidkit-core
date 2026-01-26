from __future__ import annotations

from typing import Any, Iterator

import pytest

from core.services.override_contracts.decorators import (
    apply_overrides,
    get_override_registry,
    override_method,
    override_setting,
    safe_override,
)


@pytest.fixture(autouse=True)
def reset_override_registry() -> Iterator[None]:
    registry = get_override_registry()
    original_methods = dict(registry.method_overrides)
    original_settings = dict(registry.setting_overrides)

    registry.method_overrides.clear()
    registry.setting_overrides.clear()

    try:
        yield
    finally:
        registry.method_overrides.clear()
        registry.method_overrides.update(original_methods)
        registry.setting_overrides.clear()
        registry.setting_overrides.update(original_settings)


def test_override_method_applies_and_preserves_original() -> None:
    class Base:
        def greet(self) -> str:
            return "hello"

    class Child(Base):
        pass

    @override_method("Base.greet")
    def patched_greet(_self: Any) -> str:
        return "patched"

    apply_overrides(Child)

    instance = Child()
    assert instance.greet() == "patched"
    original_attr = "_original_greet"
    original = getattr(Child, original_attr)  # type: ignore[attr-defined]  # noqa: SLF001
    assert original(instance) == "hello"


def test_override_setting_replaces_value_and_stores_original() -> None:
    original_timeout = 5
    override_timeout = 10

    class Base:
        TIMEOUT = original_timeout

    class Child(Base):
        pass

    @override_setting("Base.TIMEOUT", override_timeout)
    def _unused() -> None:
        return None

    apply_overrides(Child)

    resolved_timeout = Child.TIMEOUT
    original_attr = "_original_TIMEOUT"
    original_attribute = getattr(Child, original_attr)  # type: ignore[attr-defined]  # noqa: SLF001

    assert resolved_timeout == override_timeout
    assert original_attribute == original_timeout


def test_override_setting_callable_becomes_classmethod() -> None:
    class Base:
        NAME = "core"

        @classmethod
        def api_base(cls) -> str:
            return f"https://{cls.NAME}.rapidkit.top"

    class Child(Base):
        NAME = "module"

    @override_setting("Base.api_base")
    def api_base(cls: type[Base]) -> str:
        return f"https://{cls.NAME}.example.com"

    apply_overrides(Child)

    assert Child.api_base() == "https://module.example.com"
    original_attr = "_original_api_base"
    original = getattr(Child, original_attr)  # type: ignore[attr-defined]  # noqa: SLF001
    assert original.__get__(None, Child)() == "https://module.rapidkit.top"


def test_safe_override_missing_method_raises() -> None:
    class Target:
        pass

    with pytest.raises(ValueError):

        @safe_override(Target, "missing")
        def _override(_self: Any) -> str:
            return "nope"


def test_safe_override_applies_to_subclass_and_preserves_original() -> None:
    class Base:
        def compute(self) -> str:
            return "base"

    class Child(Base):
        pass

    @safe_override(Base, "compute")
    def compute(_self: Any) -> str:
        return "override"

    apply_overrides(Child)

    instance = Child()
    assert instance.compute() == "override"
    original_attr = "_original_compute"
    original_compute = getattr(Child, original_attr)  # type: ignore[attr-defined]  # noqa: SLF001
    assert original_compute(instance) == "base"

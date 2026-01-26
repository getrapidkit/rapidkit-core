import pytest

from core.services.override_contracts.decorators import (
    get_override_registry,
    override_setting,
    safe_override,
)
from core.services.override_contracts.mixins import (
    ConfigurableOverrideMixin,
    OverrideMixin,
    SettingOverrideMixin,
)


@pytest.fixture(autouse=True)
def reset_override_registry():
    registry = get_override_registry()
    registry.method_overrides.clear()
    registry.setting_overrides.clear()


def test_override_mixin_stores_original_and_calls_base():
    class Base:
        def greet(self) -> str:
            return "base"

    class Derived(OverrideMixin, Base):
        def greet(self) -> str:
            return "derived"

    instance = Derived()
    assert instance.greet() == "derived"
    assert instance.call_original("greet") == "base"
    assert hasattr(Derived, "_original_greet")


def test_override_mixin_call_original_missing():
    class Lone(OverrideMixin):
        def compute(self) -> int:
            return 1

    instance = Lone()
    with pytest.raises(AttributeError):
        instance.call_original("missing")


def test_safe_override_applies_registry_to_instances():
    class Service(OverrideMixin):
        def execute(self) -> str:
            return "service"

    @safe_override(Service)
    def execute(self):  # type: ignore[override]
        return f"override:{self.call_original('execute')}"

    instance = Service()
    assert instance.execute() == "override:service"
    assert instance.call_original("execute") == "service"


def test_setting_override_mixin_applies_direct_and_callable():
    override_threshold = 42
    original_threshold = 10

    class Settings(SettingOverrideMixin):
        mode = "default"
        threshold = original_threshold

    @override_setting("Settings.mode", setting_value="custom")
    def _mode() -> str:
        return "ignored"

    @override_setting("Settings.threshold")
    def threshold_provider() -> int:
        return override_threshold

    instance = Settings()
    assert instance.mode == "custom"
    assert instance.threshold == override_threshold
    assert instance.get_original_setting("mode") == "default"
    assert instance.get_original_setting("threshold") == original_threshold

    with pytest.raises(AttributeError):
        instance.get_original_setting("missing")


def test_configurable_override_mixin_combines_behaviour():
    class Target(ConfigurableOverrideMixin):
        setting = "original"

        def process(self) -> str:
            return "target"

    @safe_override(Target)
    def process(self):  # type: ignore[override]
        return f"override:{self.setting}"

    @override_setting("Target.setting", setting_value="updated")
    def _setting() -> str:
        return "unused"

    instance = Target()
    assert instance.setting == "updated"
    assert instance.process() == "override:updated"
    assert instance.call_original("process") == "target"
    assert instance.get_override_info()["method_overrides"][0]["method"] == "process"

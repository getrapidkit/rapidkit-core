from modules.free.business.feature_flags.overrides import FeatureFlagsOverrides


def test_feature_flags_overrides_are_configurable() -> None:
    overrides = FeatureFlagsOverrides()

    assert overrides.get_override_info() == {"method_overrides": [], "setting_overrides": []}
    assert hasattr(overrides, "call_original")

import pytest


def test_feature_flags_rejects_disabled_runtime_when_fail_closed(rendered_feature_flags) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_feature_flags["vendor"]
    runtime = vendor.FeatureFlags(vendor.FeatureFlagsConfig(enabled=False, fail_closed=True))

    with pytest.raises(vendor.FeatureFlagsError, match="disabled"):
        runtime.evaluate("flag")


def test_feature_flags_requires_non_empty_keys(rendered_feature_flags) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_feature_flags["vendor"]
    runtime = vendor.FeatureFlags()

    with pytest.raises(vendor.FeatureFlagsError, match="key"):
        runtime.upsert_flag(key=" ", default=False)

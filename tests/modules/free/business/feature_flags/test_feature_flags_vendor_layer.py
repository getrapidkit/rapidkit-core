def test_feature_flags_vendor_exports_runtime_contract(rendered_feature_flags) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_feature_flags["vendor"]

    for name in (
        "FeatureFlags",
        "FeatureFlagsConfig",
        "FeatureFlagsError",
        "FeatureFlag",
        "FlagRule",
        "FlagEvaluation",
        "FlagEvent",
        "FlagStatus",
        "EvaluationContext",
    ):
        assert hasattr(vendor, name)

    assert vendor.FlagStatus.ACTIVE.value == "active"

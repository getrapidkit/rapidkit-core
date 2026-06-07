def test_feature_flags_generated_runtime_is_usable(rendered_feature_flags) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_feature_flags["vendor"]

    runtime = vendor.FeatureFlags()
    runtime.upsert_flag(key="checkout", default=True)

    assert runtime.is_enabled("checkout")
    assert runtime.stats()["flags"] == 1

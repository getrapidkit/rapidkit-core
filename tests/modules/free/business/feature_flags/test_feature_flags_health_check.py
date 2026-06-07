def test_feature_flags_health_reports_registry_stats(rendered_feature_flags) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_feature_flags["vendor"]
    runtime = vendor.FeatureFlags()
    runtime.upsert_flag(key="alpha", default=True)

    health = runtime.health()

    assert health["module"] == "feature_flags"
    assert health["status"] == "ok"
    assert health["stats"]["flags"] == 1
    assert health["stats"]["by_status"] == {"active": 1}

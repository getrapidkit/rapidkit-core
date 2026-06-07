def test_feature_flags_percentage_rollout_is_stable(rendered_feature_flags) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_feature_flags["vendor"]
    runtime = vendor.FeatureFlags()
    context = vendor.EvaluationContext(user_id="u-1")

    runtime.upsert_flag(key="rollout", default=True, rollout_percentage=50)

    first = runtime.evaluate("rollout", context=context)
    second = runtime.evaluate("rollout", context=context)

    assert first == second

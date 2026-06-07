def test_feature_flags_evaluates_tenant_user_and_rule_overrides(rendered_feature_flags) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_feature_flags["vendor"]
    runtime = vendor.FeatureFlags()
    rule = vendor.FlagRule(
        attribute="plan",
        operator="equals",
        values=("enterprise",),
        variation=True,
    )

    runtime.upsert_flag(
        key="new-checkout",
        default=False,
        rules=(rule,),
        tenant_overrides={"tenant-a": True},
        user_overrides={"user-b": True},
    )

    assert runtime.is_enabled(
        "new-checkout",
        context=vendor.EvaluationContext(tenant_id="tenant-a"),
    )
    assert runtime.is_enabled(
        "new-checkout",
        context=vendor.EvaluationContext(user_id="user-b"),
    )
    assert runtime.is_enabled(
        "new-checkout",
        context=vendor.EvaluationContext(attributes={"plan": "enterprise"}),
    )
    assert not runtime.is_enabled(
        "new-checkout",
        context=vendor.EvaluationContext(attributes={"plan": "free"}),
    )


def test_feature_flags_missing_flag_uses_default(rendered_feature_flags) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_feature_flags["vendor"]
    runtime = vendor.FeatureFlags()

    evaluation = runtime.evaluate("missing", default="fallback")

    assert evaluation.value == "fallback"
    assert evaluation.reason == "missing"
    assert evaluation.default_used is True

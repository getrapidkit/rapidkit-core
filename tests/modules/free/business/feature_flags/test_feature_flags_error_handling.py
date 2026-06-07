import pytest


def test_feature_flags_rejects_invalid_rollout(rendered_feature_flags) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_feature_flags["vendor"]
    runtime = vendor.FeatureFlags()

    with pytest.raises(vendor.FeatureFlagsError, match="rollout"):
        runtime.upsert_flag(key="bad", default=False, rollout_percentage=101)


def test_feature_flags_rejects_unknown_rule_operator(rendered_feature_flags) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_feature_flags["vendor"]
    runtime = vendor.FeatureFlags()
    runtime.upsert_flag(
        key="bad-rule",
        default=False,
        rules=(vendor.FlagRule("plan", "contains", ("pro",), True),),
    )

    with pytest.raises(vendor.FeatureFlagsError, match="unsupported"):
        runtime.evaluate("bad-rule", context=vendor.EvaluationContext(attributes={"plan": "pro"}))

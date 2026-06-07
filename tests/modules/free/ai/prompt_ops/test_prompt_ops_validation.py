import pytest


def test_prompt_ops_validates_enterprise_policy(rendered_prompt_ops) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_prompt_ops["vendor"]

    ops = vendor.PromptOps(vendor.PromptOpsConfig(require_approval_for_publish=False))
    prompt = ops.create_prompt("welcome", "Hello")

    with pytest.raises(vendor.PromptOpsError):
        ops.record_evaluation("welcome", prompt.version, score=2, passed=False)

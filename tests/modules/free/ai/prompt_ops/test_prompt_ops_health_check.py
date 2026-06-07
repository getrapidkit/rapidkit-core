def test_prompt_ops_health_check_reports_runtime_state(rendered_prompt_ops) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_prompt_ops["vendor"]

    ops = vendor.PromptOps(vendor.PromptOpsConfig(require_approval_for_publish=False))
    prompt = ops.create_prompt("welcome", "Hello")
    ops.publish("welcome", prompt.version)

    health = ops.health_check()

    assert health["module"] == "prompt_ops"
    assert health["published"] == 1

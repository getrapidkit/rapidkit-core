def test_prompt_ops_generated_runtime_is_usable(rendered_prompt_ops) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_prompt_ops["vendor"]

    ops = vendor.PromptOps(vendor.PromptOpsConfig(require_approval_for_publish=False))
    prompt = ops.create_prompt("welcome", "Hello $name")
    ops.publish("welcome", prompt.version)

    assert ops.render("welcome", {"name": "Ada"}) == "Hello Ada"

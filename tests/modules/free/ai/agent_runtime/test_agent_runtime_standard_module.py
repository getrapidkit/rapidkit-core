def test_agent_runtime_generated_runtime_is_usable(rendered_agent_runtime) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_agent_runtime["vendor"]

    runtime = vendor.AgentRuntime()
    run = runtime.create_run("enterprise smoke")

    assert run.run_id
    assert runtime.get_run(run.run_id).objective == "enterprise smoke"

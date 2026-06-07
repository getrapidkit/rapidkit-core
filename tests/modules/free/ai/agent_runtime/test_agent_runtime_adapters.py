def test_agent_runtime_tool_adapter_contract(rendered_agent_runtime) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_agent_runtime["vendor"]

    seen = {}

    def capture(arguments, run):  # type: ignore[no-untyped-def]
        seen["tenant_id"] = run.tenant_id
        return arguments

    runtime = vendor.AgentRuntime(tools={"capture": capture})
    run = runtime.create_run("adapter", tenant_id="tenant-1")
    runtime.execute(run.run_id, [vendor.AgentToolCall("capture", {"ok": True})])

    assert seen["tenant_id"] == "tenant-1"
    assert run.steps[0].output == {"ok": True}

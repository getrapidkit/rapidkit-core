def test_agent_runtime_executes_registered_tools(rendered_agent_runtime) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_agent_runtime["vendor"]

    def echo(arguments, run):  # type: ignore[no-untyped-def]
        return {"objective": run.objective, "value": arguments["value"]}

    runtime = vendor.AgentRuntime(tools={"echo": echo})
    run = runtime.create_run("Handle support ticket", tenant_id="tenant-1")
    completed = runtime.execute(run.run_id, [vendor.AgentToolCall("echo", {"value": 42})])

    assert completed.status == vendor.AgentRunStatus.SUCCEEDED
    assert completed.steps[0].output["value"] == 42
    assert runtime.list_runs(tenant_id="tenant-1") == [completed]
    assert [event.type for event in runtime.events(completed.run_id)] == [
        "run.created",
        "run.started",
        "step.started",
        "step.succeeded",
        "run.succeeded",
    ]


def test_agent_runtime_marks_missing_tool_failed(rendered_agent_runtime) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_agent_runtime["vendor"]

    runtime = vendor.AgentRuntime()
    run = runtime.create_run("Do work")
    failed = runtime.execute(run.run_id, [vendor.AgentToolCall("missing")])

    assert failed.status == vendor.AgentRunStatus.FAILED
    assert "not registered" in failed.steps[0].error


def test_agent_runtime_reuses_run_for_idempotency_key(rendered_agent_runtime) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_agent_runtime["vendor"]
    runtime = vendor.AgentRuntime()

    created = runtime.create_run("Do work", tenant_id="tenant-1", idempotency_key="run-123")
    reused = runtime.create_run("Do work again", tenant_id="tenant-1", idempotency_key="run-123")

    assert reused.run_id == created.run_id

def test_agent_runtime_health_reports_runs_and_tools(rendered_agent_runtime) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_agent_runtime["vendor"]

    runtime = vendor.AgentRuntime(tools={"noop": lambda _args, _run: "ok"})
    runtime.create_run("Observe")

    health = runtime.health_check()

    assert health["module"] == "agent_runtime"
    assert health["status"] == "ok"
    assert health["runs"] == 1
    assert "noop" in health["tools"]

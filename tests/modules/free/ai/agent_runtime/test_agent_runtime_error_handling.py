import pytest


def test_agent_runtime_retries_and_records_tool_failure(rendered_agent_runtime) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_agent_runtime["vendor"]
    attempts = {"count": 0}

    def broken(_arguments, _run):  # type: ignore[no-untyped-def]
        attempts["count"] += 1
        raise RuntimeError("transient failure")

    runtime = vendor.AgentRuntime(
        vendor.AgentRuntimeConfig(retry_limit=2), tools={"broken": broken}
    )
    run = runtime.create_run("retry work")
    failed = runtime.execute(run.run_id, [vendor.AgentToolCall("broken")])

    assert attempts["count"] == 3
    assert failed.status == vendor.AgentRunStatus.FAILED
    assert "transient failure" in failed.steps[0].error


def test_agent_runtime_prevents_execution_after_cancel(rendered_agent_runtime) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_agent_runtime["vendor"]

    runtime = vendor.AgentRuntime()
    run = runtime.create_run("cancel me")
    runtime.cancel(run.run_id)

    with pytest.raises(vendor.AgentRuntimeError, match="cancelled"):
        runtime.execute(run.run_id, [])

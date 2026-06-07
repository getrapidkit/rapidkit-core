import pytest


def test_agent_runtime_rejects_disabled_runtime(rendered_agent_runtime) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_agent_runtime["vendor"]

    runtime = vendor.AgentRuntime(vendor.AgentRuntimeConfig(enabled=False))

    with pytest.raises(vendor.AgentRuntimeError, match="disabled"):
        runtime.create_run("Do work")


def test_agent_runtime_enforces_tool_allowlist(rendered_agent_runtime) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_agent_runtime["vendor"]

    runtime = vendor.AgentRuntime(vendor.AgentRuntimeConfig(allowed_tools=("safe",)))

    with pytest.raises(vendor.AgentRuntimeError, match="not allowed"):
        runtime.register_tool("unsafe", lambda _args, _run: "nope")

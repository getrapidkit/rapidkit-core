def test_agent_runtime_vendor_exports_contract(rendered_agent_runtime) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_agent_runtime["vendor"]

    for name in (
        "AgentRuntime",
        "AgentRuntimeConfig",
        "AgentRuntimeError",
        "AgentRun",
        "AgentRunStatus",
        "AgentToolCall",
        "AgentStep",
    ):
        assert hasattr(vendor, name)

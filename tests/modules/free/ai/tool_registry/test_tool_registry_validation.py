def test_tool_registry_validates_enterprise_policy(rendered_tool_registry) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_tool_registry["vendor"]

    registry = vendor.ToolRegistry()
    registry.register_tool(
        vendor.ToolDefinition(name="secure", description="Secure", scopes=("a",))
    )

    decision = registry.evaluate("secure", vendor.ToolInvocationPolicy())

    assert decision.allowed is False
    assert decision.reason == "missing_required_scope"

def test_tool_registry_health_check_reports_runtime_state(rendered_tool_registry) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_tool_registry["vendor"]

    registry = vendor.ToolRegistry()
    registry.register_tool(vendor.ToolDefinition(name="lookup", description="Lookup data"))

    health = registry.health_check()

    assert health["module"] == "tool_registry"
    assert health["tools"] == 1

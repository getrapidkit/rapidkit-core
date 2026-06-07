def test_tool_registry_generated_runtime_is_usable(rendered_tool_registry) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_tool_registry["vendor"]

    registry = vendor.ToolRegistry()
    tool = registry.register_tool(vendor.ToolDefinition(name="lookup", description="Lookup data"))

    assert tool.name == "lookup"
    assert registry.get_tool("lookup").description == "Lookup data"

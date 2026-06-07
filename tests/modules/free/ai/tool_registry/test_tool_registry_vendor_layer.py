def test_tool_registry_vendor_exports_contract(rendered_tool_registry) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_tool_registry["vendor"]

    for name in (
        "ToolRegistry",
        "ToolRegistryConfig",
        "ToolRegistryError",
        "ToolDefinition",
        "ToolInvocationPolicy",
        "ToolDecision",
        "ToolRisk",
    ):
        assert hasattr(vendor, name)

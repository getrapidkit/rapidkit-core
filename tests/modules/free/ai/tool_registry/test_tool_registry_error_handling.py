import pytest


def test_tool_registry_raises_clear_errors(rendered_tool_registry) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_tool_registry["vendor"]

    registry = vendor.ToolRegistry()

    with pytest.raises(vendor.ToolRegistryError):
        registry.register_tool(vendor.ToolDefinition(name="", description="bad"))
    with pytest.raises(vendor.ToolRegistryError):
        registry.get_tool("missing")

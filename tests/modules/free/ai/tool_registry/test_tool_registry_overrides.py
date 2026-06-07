from modules.free.ai.tool_registry import overrides


def test_tool_registry_overrides_module_is_importable() -> None:
    assert overrides is not None

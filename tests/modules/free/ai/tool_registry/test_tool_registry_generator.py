from importlib import import_module


def test_tool_registry_generator_entrypoint() -> None:
    """Ensure the module generator can be imported without crashing."""

    generator_module = import_module("modules.free.ai.tool_registry.generate")
    assert hasattr(generator_module, "main"), "Expected a main() entrypoint on the generator module"

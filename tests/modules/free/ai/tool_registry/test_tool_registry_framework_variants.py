from modules.free.ai.tool_registry.generate import ToolRegistryModuleGenerator


def test_tool_registry_declares_fastapi_and_nestjs_variants() -> None:
    generator = ToolRegistryModuleGenerator()
    config = generator.load_module_config()
    variants = config["generation"]["variants"]

    assert "fastapi" in variants
    assert "nestjs" in variants
    assert "fastapi.standard" in variants
    assert "nestjs.standard" in variants

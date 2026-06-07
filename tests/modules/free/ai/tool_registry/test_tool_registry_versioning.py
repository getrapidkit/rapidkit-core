from modules.free.ai.tool_registry.generate import ToolRegistryModuleGenerator


def test_tool_registry_manifest_has_stable_version() -> None:
    generator = ToolRegistryModuleGenerator()
    config = generator.load_module_config()

    assert config["version"].count(".") == 2
    assert config["status"] == "stable"

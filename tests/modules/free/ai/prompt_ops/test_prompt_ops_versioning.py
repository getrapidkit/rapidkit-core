from modules.free.ai.prompt_ops.generate import PromptOpsModuleGenerator


def test_prompt_ops_manifest_has_stable_version() -> None:
    generator = PromptOpsModuleGenerator()
    config = generator.load_module_config()

    assert config["version"].count(".") == 2
    assert config["status"] == "stable"

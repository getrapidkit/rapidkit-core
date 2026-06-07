from modules.free.ai.ai_guardrails.generate import AiGuardrailsModuleGenerator


def test_ai_guardrails_manifest_has_stable_version() -> None:
    generator = AiGuardrailsModuleGenerator()
    config = generator.load_module_config()

    assert config["version"].count(".") == 2
    assert config["status"] == "stable"

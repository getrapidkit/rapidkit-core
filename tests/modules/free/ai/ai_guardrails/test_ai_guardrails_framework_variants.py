from modules.free.ai.ai_guardrails.generate import AiGuardrailsModuleGenerator


def test_ai_guardrails_declares_fastapi_and_nestjs_variants() -> None:
    generator = AiGuardrailsModuleGenerator()
    config = generator.load_module_config()
    variants = config["generation"]["variants"]

    assert "fastapi" in variants
    assert "nestjs" in variants
    assert "fastapi.standard" in variants
    assert "nestjs.standard" in variants

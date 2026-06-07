from modules.free.ai.prompt_ops.generate import PromptOpsModuleGenerator


def test_prompt_ops_declares_fastapi_and_nestjs_variants() -> None:
    generator = PromptOpsModuleGenerator()
    config = generator.load_module_config()
    variants = config["generation"]["variants"]

    assert "fastapi" in variants
    assert "nestjs" in variants
    assert "fastapi.standard" in variants
    assert "nestjs.standard" in variants

from modules.free.business.forms_engine.generate import FormsEngineModuleGenerator


def test_forms_engine_declares_fastapi_and_nestjs_variants() -> None:
    config = FormsEngineModuleGenerator().load_module_config()
    variants = config["generation"]["variants"]

    assert "fastapi" in variants
    assert "nestjs" in variants

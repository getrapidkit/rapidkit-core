from modules.free.business.forms_engine.generate import FormsEngineModuleGenerator


def test_forms_engine_module_metadata_is_stable_enterprise_ready() -> None:
    config = FormsEngineModuleGenerator().load_module_config()

    assert config["status"] == "stable"
    assert config["testing"]["coverage_min"] >= 85
    assert config["metadata"]["enterprise_ready"] is True

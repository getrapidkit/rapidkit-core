from modules.free.business.forms_engine.generate import FormsEngineModuleGenerator


def test_forms_engine_declares_semver_version() -> None:
    config = FormsEngineModuleGenerator().load_module_config()
    parts = str(config["version"]).split(".")

    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)

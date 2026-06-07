from modules.free.business.admin_console.generate import AdminConsoleModuleGenerator


def test_admin_console_generator_version_matches_manifest() -> None:
    generator = AdminConsoleModuleGenerator()
    config = generator.load_module_config()

    assert config["version"] == "0.1.3"

from modules.free.business.org_admin_console.generate import OrgAdminConsoleModuleGenerator


def test_org_admin_console_generator_version_matches_manifest() -> None:
    generator = OrgAdminConsoleModuleGenerator()
    config = generator.load_module_config()

    assert config["version"] == "0.1.3"

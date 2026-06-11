import yaml

from modules.free.business.admin_console.generate import (
    MODULE_ROOT,
    AdminConsoleModuleGenerator,
)


def test_admin_console_generator_version_matches_manifest() -> None:
    generator = AdminConsoleModuleGenerator()
    config = generator.load_module_config()
    manifest = yaml.safe_load((MODULE_ROOT / "module.yaml").read_text(encoding="utf-8"))

    assert config["version"] == manifest["version"]

import yaml

from modules.free.business.connector_pack_library.generate import (
    MODULE_ROOT,
    ConnectorPackLibraryModuleGenerator,
)


def test_connector_pack_library_generator_version_matches_manifest() -> None:
    generator = ConnectorPackLibraryModuleGenerator()
    config = generator.load_module_config()
    manifest = yaml.safe_load((MODULE_ROOT / "module.yaml").read_text(encoding="utf-8"))

    assert config["version"] == manifest["version"]

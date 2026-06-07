from modules.free.business.connector_pack_library.generate import (
    ConnectorPackLibraryModuleGenerator,
)


def test_connector_pack_library_generator_version_matches_manifest() -> None:
    generator = ConnectorPackLibraryModuleGenerator()
    config = generator.load_module_config()

    assert config["version"] == "0.1.3"

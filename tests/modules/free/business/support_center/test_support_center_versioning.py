from modules.free.business.support_center.generate import SupportCenterModuleGenerator


def test_support_center_version_matches_manifest() -> None:
    config = SupportCenterModuleGenerator().load_module_config()

    assert config["version"] == "0.1.3"

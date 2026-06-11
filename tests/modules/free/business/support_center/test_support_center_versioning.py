import yaml

from modules.free.business.support_center.generate import (
    MODULE_ROOT,
    SupportCenterModuleGenerator,
)


def test_support_center_version_matches_manifest() -> None:
    config = SupportCenterModuleGenerator().load_module_config()
    manifest = yaml.safe_load((MODULE_ROOT / "module.yaml").read_text(encoding="utf-8"))

    assert config["version"] == manifest["version"]

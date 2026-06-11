import yaml

from modules.free.business.approval_engine.generate import (
    MODULE_ROOT,
    ApprovalEngineModuleGenerator,
)


def test_approval_engine_version_matches_manifest() -> None:
    config = ApprovalEngineModuleGenerator().load_module_config()
    manifest = yaml.safe_load((MODULE_ROOT / "module.yaml").read_text(encoding="utf-8"))

    assert config["version"] == manifest["version"]
